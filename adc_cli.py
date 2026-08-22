#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adc_cli.py — Client série minimal pour le firmware ADC-Auto (ESP32-C3).

Périmètre volontairement réduit : connexion série + LEVEL + STRENGTH + RESET + STATUS.
Le MPU-6050 et le serveur Alpaca ne sont pas traités ici (phases suivantes).

Usage :
    python3 adc_cli.py status                 # état complet
    python3 adc_cli.py level 30               # régler level (angle, -45..45)
    python3 adc_cli.py strength 75            # régler strength (force, 0..100)
    python3 adc_cli.py reset                  # retour à level=0, strength=0
    python3 adc_cli.py sweep                  # rampe de validation matérielle
    python3 adc_cli.py                        # mode interactif (REPL)
    python3 adc_cli.py --port /dev/ttyACM0 --baud 115200 status

Comportement :
    - ignore les lignes texte brut du firmware (messages de boot, help...)
    - affiche les logs JSON (type:"log") en gris
    - traite les réponses data/error
"""

import argparse
import json
import sys
import time

import serial
import serial.tools.list_ports

BAUD_DEFAULT = 115200          # vitesse du firmware (Serial.begin(115200))
TIMEOUT = 1.0                  # timeout de lecture pySerial
RESPONSE_TIMEOUT = 4.0         # attente max d'une réponse après une commande

# Ordre d'affichage des infos du modèle ADC
ADC_FIELDS = ("level", "strength")
ANGLE_FIELDS = ("angle1", "angle2")


def find_serial_port():
    """Retourne le port série USB le plus probable (1er candidat), ou None."""
    keywords = ("usb", "uart", "cp210", "ch340", "serial", "jtag", "acm")
    candidates = []
    for p in serial.tools.list_ports.comports():
        desc = (p.description or "").lower()
        dev = p.device.lower()
        if any(k in desc for k in keywords) or any(k in dev for k in keywords):
            candidates.append(p)
    if not candidates:
        # Fallback : tous les ports (Linux /dev/ttyS* exclus)
        candidates = [p for p in serial.tools.list_ports.comports()
                      if "ttyS" not in p.device]
    return candidates[0] if candidates else None


def display_adc(data):
    """Affiche l'état ADC contenu dans une réponse JSON."""
    adc = data.get("adc", {})
    if not adc:
        return
    parts = [f"{k}={adc.get(k, '?')}" for k in ADC_FIELDS]
    angles = adc.get("angles", {})
    if angles:
        parts.append("angles=" + ",".join(f"{k}:{angles.get(k, '?')}" for k in ANGLE_FIELDS))
    print("  ADC  : " + " | ".join(parts))


def handle_response(data, verbose=False):
    """Affiche une réponse JSON data/error. Retourne l'objet ou None."""
    if data is None:
        return None
    dtype = data.get("type")
    command = data.get("command", "?")
    if dtype == "error":
        print(f"  [ERREUR {data.get('code', '?')}] {data.get('reason', '?')} "
              f"(commande: {command})")
        return None
    if dtype != "data":
        return None
    if command == "status":
        print(f"  ready: {data.get('ready')}")
        display_adc(data)
        mpu = data.get("mpu6050")
        if mpu:
            print(f"  MPU  : initialized={mpu.get('initialized')} "
                  f"pitch={mpu.get('pitch')} roll={mpu.get('roll')} "
                  f"level={mpu.get('level')}")
        if "angles" in data:
            a = data["angles"]
            print(f"  Servos: angle1={a.get('angle1')} angle2={a.get('angle2')}")
    elif command == "level":
        print(f"  level -> {data.get('level')}")
        display_adc(data)
    elif command == "strength":
        print(f"  strength -> {data.get('strength')}")
        display_adc(data)
    elif command == "reset":
        print(f"  reset -> {data.get('status')}")
        display_adc(data)
    else:
        print(f"  [{command}] {json.dumps(data, ensure_ascii=False)}")
    return data


class AdcClient:
    """Connexion série au firmware ADC-Auto."""

    def __init__(self, port, baud=BAUD_DEFAULT, timeout=TIMEOUT):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.ser.reset_input_buffer()
        print(f"Connecté à {port} ({baud} bauds)")

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def _read_response(self, timeout=RESPONSE_TIMEOUT):
        """Lit les lignes jusqu'à une réponse JSON data/error.

        Les lignes texte brut et les logs JSON sont affichés mais ignorés.
        Retourne l'objet réponse, ou None si timeout.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.ser.readline()
            if not line:
                continue
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            if not text.startswith("{"):
                print(f"  [brut] {text}")
                continue
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                print(f"  [non-JSON] {text[:80]}")
                continue
            if data.get("type") == "log":
                print(f"  [log:{data.get('level')}] {data.get('message', '')}")
                continue
            return data
        print("  [timeout: pas de réponse]")
        return None

    def send(self, command, timeout=RESPONSE_TIMEOUT):
        """Envoie une commande et retourne la réponse JSON (ou None)."""
        self.ser.write((command + "\n").encode("utf-8"))
        return self._read_response(timeout)

    def send_raw(self, command, duration=1.5):
        """Envoie une commande sans réponse JSON (ex: HELP) et draine les
        lignes texte brut pendant `duration` secondes."""
        self.ser.write((command + "\n").encode("utf-8"))
        deadline = time.time() + duration
        while time.time() < deadline:
            line = self.ser.readline()
            if not line:
                continue
            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if data.get("type") == "log":
                        print(f"  [log:{data.get('level')}] {data.get('message', '')}")
                        continue
                    handle_response(data)
                    continue
                except json.JSONDecodeError:
                    pass
            print(f"  [brut] {text}")

    # ── Commandes applicatives ──────────────────────────────────────────
    def status(self):
        return self.send("STATUS")

    def set_level(self, value):
        return self.send(f"LEVEL={int(value)}")

    def set_strength(self, value):
        return self.send(f"STRENGTH={int(value)}")

    def reset(self):
        return self.send("RESET")


def cmd_status(client):
    handle_response(client.status())


def cmd_set(client, name, value, lo, hi):
    try:
        v = int(value)
    except ValueError:
        print(f"Valeur invalide: {value!r} (entier attendu)")
        return 2
    if not (lo <= v <= hi):
        print(f"Hors plage: {v} (attendu {lo}..{hi})")
        return 2
    if name == "level":
        handle_response(client.set_level(v))
    else:
        handle_response(client.set_strength(v))
    return 0


def cmd_reset(client):
    handle_response(client.reset())


def cmd_sweep(client):
    """Rampe de validation : level -45→45 par 15, puis strength 0→100 par 25."""
    print("=== SWEEP level (-45 → 45, pas 15) ===")
    for v in range(-45, 46, 15):
        print(f"-- LEVEL={v}")
        handle_response(client.set_level(v))
        time.sleep(0.5)
    print("=== SWEEP strength (0 → 100, pas 25) ===")
    for v in range(0, 101, 25):
        print(f"-- STRENGTH={v}")
        handle_response(client.set_strength(v))
        time.sleep(0.5)
    print("=== RESET ===")
    handle_response(client.reset())
    print("=== STATUS final ===")
    handle_response(client.status())


def cmd_repl(client):
    """Mode interactif : tape une commande brute, affiche la réponse."""
    print("Mode interactif (Ctrl-D ou 'quit' pour quitter).")
    print("Exemples: LEVEL=30, STRENGTH=75, STATUS, RESET, HELP")
    while True:
        try:
            line = input("adc> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("quit", "exit", "q"):
            break
        if line.upper() in ("HELP", "H"):
            client.send_raw("HELP")
            continue
        handle_response(client.send(line.upper()))


def main():
    parser = argparse.ArgumentParser(description="Client série ADC-Auto")
    parser.add_argument("--port", help="Port série (auto-détection sinon)")
    parser.add_argument("--baud", type=int, default=BAUD_DEFAULT, help=f"Baudrate (défaut {BAUD_DEFAULT})")
    parser.add_argument("command", nargs="?", help="status | level N | strength N | reset | sweep")
    parser.add_argument("value", nargs="?", help="valeur pour level/strength")
    args = parser.parse_args()

    port = args.port
    if not port:
        found = find_serial_port()
        if not found:
            print("Aucun port série USB trouvé. Utilisez --port pour le forcer.")
            return 2
        port = found.device
        print(f"Port auto-détecté: {port} ({found.description})")

    client = AdcClient(port, args.baud)
    try:
        if not args.command:
            cmd_repl(client)
            return 0
        cmd = args.command.lower()
        if cmd == "status":
            cmd_status(client)
        elif cmd in ("level", "strength"):
            if args.value is None:
                print(f"Usage: adc_cli.py {cmd} <valeur>")
                return 2
            lo, hi = (-45, 45) if cmd == "level" else (0, 100)
            return cmd_set(client, cmd, args.value, lo, hi)
        elif cmd == "reset":
            cmd_reset(client)
        elif cmd == "sweep":
            cmd_sweep(client)
        else:
            print(f"Commande inconnue: {cmd}")
            parser.print_help()
            return 2
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
