#!/usr/bin/env python3
"""Simulateur du firmware ADC-Auto : émule les réponses série exactes du C3.

Créé un pty (pseudo-terminal) et y répond aux commandes comme le firmware :
    LEVEL=n / STRENGTH=n / STATUS / RESET + messages de boot texte brut
    + logs JSON occasionnels.
"""
import os
import pty
import time
import json
import threading
import select
import termios
import tty

def servo_angles(level, strength):
    base = 90 + level
    spread = int(strength / 100 * 150)
    a1 = max(0, min(180, base - spread // 2))
    a2 = max(0, min(180, base + spread // 2))
    return a1, a2

def adc_json(level, strength):
    a1, a2 = servo_angles(level, strength)
    return {
        "source": "system", "type": "data", "command": "level",
        "level": level,
        "adc": {"level": level, "strength": strength,
                "angles": {"angle1": a1, "angle2": a2}},
    }

def main():
    master_fd, slave_fd = pty.openpty()
    # Mode raw : pas d'écho ni de canonique (comme un vrai port USB série)
    tty.setraw(slave_fd)
    print(f"SLAVE_PORT={os.ttyname(slave_fd)}")
    state = {"level": 0, "strength": 0}

    def send(line):
        os.write(master_fd, (line + "\n").encode())

    # Boot messages texte brut (comme le vrai firmware)
    time.sleep(0.2)
    send("=== ADC Control System ===")
    send("Starting initialization sequence...")
    send("System is still initializing...")
    time.sleep(0.3)
    send("=== System Ready! ===")
    send("You can now send commands.")

    def reader():
        buf = b""
        while True:
            r, _, _ = select.select([master_fd], [], [], 0.05)
            if not r:
                continue
            try:
                chunk = os.read(master_fd, 256)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode().strip().upper()
                handle(cmd)

    def handle(cmd):
        if cmd.startswith("LEVEL="):
            v = int(cmd.split("=")[1])
            if -45 <= v <= 45:
                state["level"] = v
            else:
                send(json.dumps({"source": "system", "type": "error",
                                 "code": "INVALID_LEVEL", "command": cmd,
                                 "reason": "Valeur de niveau invalide (-45 à 45)",
                                 "help": "Tapez HELP"}))
                return
            d = adc_json(state["level"], state["strength"])
            send(json.dumps(d))
        elif cmd.startswith("STRENGTH="):
            v = int(cmd.split("=")[1])
            if 0 <= v <= 100:
                state["strength"] = v
            else:
                send(json.dumps({"source": "system", "type": "error",
                                 "code": "INVALID_STRENGTH", "command": cmd,
                                 "reason": "Valeur de force invalide (0 à 100)",
                                 "help": "Tapez HELP"}))
                return
            d = adc_json(state["level"], state["strength"])
            d["command"] = "strength"
            d["strength"] = v
            send(json.dumps(d))
        elif cmd == "STATUS":
            a1, a2 = servo_angles(state["level"], state["strength"])
            send(json.dumps({
                "source": "system", "type": "data", "command": "status",
                "ready": True,
                "adc": {"level": state["level"], "strength": state["strength"],
                        "angles": {"angle1": a1, "angle2": a2}},
                "angles": {"angle1": a1, "angle2": a2},
            }))
        elif cmd == "RESET":
            state["level"] = 0
            state["strength"] = 0
            a1, a2 = servo_angles(0, 0)
            send(json.dumps({
                "source": "system", "type": "data", "command": "reset",
                "status": "ok",
                "adc": {"level": 0, "strength": 0,
                        "angles": {"angle1": a1, "angle2": a2}},
                "angles": {"angle1": a1, "angle2": a2},
            }))
        elif cmd == "LOG_LEVEL=DEBUG":
            send(json.dumps({"source": "system", "type": "log",
                             "level": "debug", "message": "debug mode on"}))
        elif cmd in ("HELP", "H"):
            send("=== ADC Control Commands ===")
            send("  LEVEL=VALUE : Set level (-45 to 45)")
        else:
            send(json.dumps({"source": "system", "type": "error",
                             "code": "GENERIC_ERROR", "command": cmd,
                             "reason": "Commande inconnue", "help": "Tapez HELP"}))

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        time.sleep(600)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
