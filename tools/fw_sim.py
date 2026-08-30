#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test du client contre le firmware adc-auto commit 9f9b496 (MPU amélioré).

Vérifie la compatibilité du client adc_cli.py avec les réponses du firmware :
- STATUS (ready, adc, angles, mpu6050 optionnel)
- LEVEL/STRENGTH lecture + écriture
- MPU, MPU=raw (logs), MPU=init/calibrate/update
- custom_levels dans la réponse MPU
"""
import json
import os
import pty
import sys
import time
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

def main():
    master_fd, slave_fd = pty.openpty()
    tty.setraw(slave_fd)
    port = os.ttyname(slave_fd)
    print(f"SLAVE_PORT={port}")
    state = {"level": 0, "strength": 0, "mpu_init": False, "pitch": 7.15, "roll": 2.86}

    def send(line):
        os.write(master_fd, (line + "\n").encode())

    time.sleep(0.2)
    send("=== ADC Control System ===")
    send("=== System Ready! ===")

    def mpu_json(custom=False):
        d = {"source": "system", "type": "data", "command": "mpu",
             "mpu6050": {"initialized": state["mpu_init"]}}
        if state["mpu_init"]:
            d["mpu6050"].update({
                "pitch": state["pitch"], "roll": state["roll"], "level": 7})
            if custom:
                d["mpu6050"].update({
                    "custom_levels": {"x_only": 10.5, "y_only": 2.3, "z_only": 0.0,
                                      "xy": 11.0, "xz": 10.5, "yz": 2.3},
                    "action": "custom_levels"})
        return d

    def handle(cmd):
        if cmd.startswith("LEVEL="):
            v = int(cmd.split("=")[1])
            if -45 <= v <= 45:
                state["level"] = v
                d = {"source": "system", "type": "data", "command": "level",
                     "level": v,
                     "adc": {"level": v, "strength": state["strength"],
                             "angles": dict(zip(("angle1", "angle2"),
                                                servo_angles(v, state["strength"])))}}
                send(json.dumps(d))
        elif cmd == "LEVEL":
            d = {"source": "system", "type": "data", "command": "level",
                 "level": state["level"],
                 "adc": {"level": state["level"], "strength": state["strength"],
                         "angles": dict(zip(("angle1", "angle2"),
                                            servo_angles(state["level"], state["strength"])))}}
            send(json.dumps(d))
        elif cmd.startswith("STRENGTH="):
            v = int(cmd.split("=")[1])
            if 0 <= v <= 100:
                state["strength"] = v
                d = {"source": "system", "type": "data", "command": "strength",
                     "strength": v,
                     "adc": {"level": state["level"], "strength": v,
                             "angles": dict(zip(("angle1", "angle2"),
                                                servo_angles(state["level"], v)))}}
                send(json.dumps(d))
        elif cmd == "STRENGTH":
            d = {"source": "system", "type": "data", "command": "strength",
                 "strength": state["strength"],
                 "adc": {"level": state["level"], "strength": state["strength"],
                         "angles": dict(zip(("angle1", "angle2"),
                                            servo_angles(state["level"], state["strength"])))}}
            send(json.dumps(d))
        elif cmd == "STATUS":
            a1, a2 = servo_angles(state["level"], state["strength"])
            d = {"source": "system", "type": "data", "command": "status",
                 "ready": True,
                 "adc": {"level": state["level"], "strength": state["strength"],
                         "angles": {"angle1": a1, "angle2": a2}},
                 "angles": {"angle1": a1, "angle2": a2}}
            if state["mpu_init"]:
                d["mpu6050"] = {"initialized": True, "pitch": state["pitch"],
                                "roll": state["roll"], "level": 7}
            send(json.dumps(d))
        elif cmd == "MPU":
            send(json.dumps(mpu_json()))
        elif cmd == "MPU=INIT":
            state["mpu_init"] = True
            send(json.dumps({"source": "system", "type": "log", "level": "info",
                             "message": "MPU-6050 initialized successfully"}))
            d = mpu_json()
            d["mpu6050"]["action"] = "initialize"
            d["status"] = "ok"
            send(json.dumps(d))
        elif cmd == "MPU=CUSTOM":
            if state["mpu_init"]:
                d = mpu_json(custom=True)
                send(json.dumps(d))
        elif cmd == "MPU=RAW":
            if state["mpu_init"]:
                send(json.dumps({"source": "system", "type": "log", "level": "info",
                                 "message": "MPU-6050 Raw Data:\nAccel X: 100 (0.08 g)\nPitch: 7.15°"}))
                d = mpu_json()
                d["mpu6050"]["action"] = "print_raw_data"
                send(json.dumps(d))
        elif cmd == "MPU=UPDATE":
            if state["mpu_init"]:
                state["level"] = 7  # le firmware met à jour le niveau ADC
                d = mpu_json()
                d["mpu6050"]["action"] = "update"
                d["status"] = "ok"
                send(json.dumps(d))
        elif cmd == "RESET":
            state["level"] = 0
            state["strength"] = 0
            a1, a2 = servo_angles(0, 0)
            send(json.dumps({"source": "system", "type": "data", "command": "reset",
                             "status": "ok",
                             "adc": {"level": 0, "strength": 0,
                                     "angles": {"angle1": a1, "angle2": a2}},
                             "angles": {"angle1": a1, "angle2": a2}}))
        else:
            send(json.dumps({"source": "system", "type": "error", "code": "GENERIC_ERROR",
                             "command": cmd, "reason": "Commande inconnue"}))

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
                handle(line.decode().strip().upper())

    threading.Thread(target=reader, daemon=True).start()
    time.sleep(600)

if __name__ == "__main__":
    main()
