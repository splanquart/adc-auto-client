#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de configuration du système de journalisation.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime


def setup_logger():
    """Configure le système de journalisation pour l'application."""
    # Création du répertoire de logs s'il n'existe pas
    log_dir = Path.home() / "AdcAutoClient" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Format du nom de fichier de log avec date
    log_filename = f"adcautoclient_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = log_dir / log_filename
    
    # Configuration du format des messages de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configuration du logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Handler pour le fichier
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    return logger
