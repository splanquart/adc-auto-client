#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Détection automatique du device ADC-Auto sur les ports série.

Principe : on interroge chaque port série avec le handshake du firmware
(commande STATUS) et on garde ceux qui répondent en JSON avec
`source == "system"` et `type == "data"`. Les autres devices (monture,
focuser, caméra...) ne parlent pas ce protocole et sont donc écartés
automatiquement, même branchés en même temps.

Le scan est parallèle (ThreadPoolExecutor) : ~2-4 s pour 8 ports.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)

# Vitesse du firmware ADC-Auto (Serial.begin(115200))
BAUDRATE = 115200
# Commande de handshake : STATUS répond toujours (même servos pas prêts)
HANDSHAKE_COMMAND = b"STATUS\n"
# Temps max de lecture après l'envoi du handshake sur un port
SCAN_TIMEOUT = 1.5
# Pause après ouverture du port (stabilisation)
OPEN_STABILIZE = 0.15

# Fichier de config (dernier port utilisé)
CONFIG_DIR = Path.home() / "AdcAutoClient"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _candidate_ports():
    """Retourne les ports série candidats (exclut les UART internes ttyS*)."""
    out = []
    for p in serial.tools.list_ports.comports():
        if p.device.lower().startswith("/dev/ttyS"):
            continue
        out.append(p)
    return out


def _probe_port(port):
    """Interroge un port série.

    Args:
        port: objet ListPortInfo de pyserial

    Returns:
        dict {"port", "description", "name"} si c'est un ADC-Auto, sinon None.
    """
    try:
        ser = serial.Serial(port.device, BAUDRATE, timeout=0.3)
    except Exception:
        return None
    try:
        # Ne pas toucher DTR/RTS : sur certains adaptateurs (CP2102, CH340),
        # les faire basculer déclenche un reset du microcontrôleur.
        try:
            ser.dtr = False
            ser.rts = False
        except Exception:
            pass
        ser.reset_input_buffer()
        time.sleep(OPEN_STABILIZE)
        ser.write(HANDSHAKE_COMMAND)
        deadline = time.time() + SCAN_TIMEOUT
        while time.time() < deadline:
            line = ser.readline()
            if not line:
                continue
            text = line.decode("utf-8", errors="replace").strip()
            if not text.startswith("{"):
                continue  # texte brut du firmware (boot, help...)
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                continue
            if data.get("source") == "system" and data.get("type") == "data":
                return {
                    "port": port.device,
                    "description": port.description or port.device,
                    "name": "ADC-Auto",
                }
    finally:
        try:
            ser.close()
        except Exception:
            pass
    return None


def scan_adc_devices(timeout=SCAN_TIMEOUT, parallel=True):
    """Scanne les ports série et retourne les devices ADC-Auto trouvés.

    Returns:
        Liste de dicts {"port", "description", "name"}.
    """
    ports = _candidate_ports()
    if not ports:
        logger.info("Aucun port série candidat")
        return []
    results = []
    if parallel and len(ports) > 1:
        with ThreadPoolExecutor(max_workers=min(6, len(ports))) as ex:
            futs = {ex.submit(_probe_port, p): p for p in ports}
            for fut in as_completed(futs):
                try:
                    r = fut.result()
                except Exception:
                    r = None
                if r:
                    results.append(r)
    else:
        for p in ports:
            r = _probe_port(p)
            if r:
                results.append(r)
    logger.info("Devices ADC-Auto trouvés: %s", results)
    return results


# ── Persistance du dernier port ──────────────────────────────────────────

def load_last_port():
    """Retourne le dernier port ADC utilisé (ou None)."""
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f).get("last_port")
    except Exception:
        return None


def save_last_port(port):
    """Mémorise le port ADC utilisé pour les prochains lancements."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {}
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
        except Exception:
            pass
        data["last_port"] = port
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Impossible de sauvegarder le port: %s", e)
