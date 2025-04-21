#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Point d'entrée principal de l'application AdcAutoClient.
"""

import sys
import os
import logging
from pathlib import Path

# Ajout du répertoire parent au chemin de recherche Python
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger


def main():
    """Fonction principale de démarrage de l'application."""
    # Configuration du logger
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Démarrage de l'application AdcAutoClient")

    # Création de l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("AdcAutoClient")
    app.setOrganizationName("AdcAuto")
    
    # Création et affichage de la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Exécution de la boucle d'événements Qt
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
