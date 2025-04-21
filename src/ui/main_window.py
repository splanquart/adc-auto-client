#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application AdcAutoClient.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSlider, QGroupBox, QPushButton, QStatusBar,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont

from src.ui.widgets.servo_indicator import ServoIndicator
from src.services.serial_service import SerialService


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.serial_service = SerialService()
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur."""
        # Configuration de la fenêtre
        self.setWindowTitle("AdcAutoClient")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Groupe pour les contrôles
        controls_group = QGroupBox("Contrôles")
        controls_layout = QHBoxLayout()
        
        # Layout pour les sliders
        sliders_layout = QVBoxLayout()
        
        # Slider pour le level
        level_layout = QVBoxLayout()
        level_label = QLabel("Level")
        level_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.level_slider = QSlider(Qt.Orientation.Horizontal)
        self.level_slider.setMinimum(-45)
        self.level_slider.setMaximum(45)
        self.level_slider.setValue(0)
        self.level_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.level_slider.setTickInterval(15)
        self.level_value_label = QLabel("0°")
        self.level_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_slider)
        level_layout.addWidget(self.level_value_label)
        
        # Slider pour le strength
        strength_layout = QVBoxLayout()
        strength_label = QLabel("Strength")
        strength_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.strength_slider = QSlider(Qt.Orientation.Horizontal)
        self.strength_slider.setMinimum(0)
        self.strength_slider.setMaximum(100)
        self.strength_slider.setValue(50)
        self.strength_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.strength_slider.setTickInterval(10)
        self.strength_value_label = QLabel("50")
        self.strength_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        strength_layout.addWidget(strength_label)
        strength_layout.addWidget(self.strength_slider)
        strength_layout.addWidget(self.strength_value_label)
        
        # Ajout des layouts de sliders au layout principal des sliders
        sliders_layout.addLayout(level_layout)
        sliders_layout.addLayout(strength_layout)
        
        # Ajout du layout des sliders au layout des contrôles
        controls_layout.addLayout(sliders_layout)
        
        # Groupe pour les indicateurs de servo
        indicators_group = QGroupBox("État des Servos")
        indicators_layout = QHBoxLayout()
        
        # Indicateurs de servo
        self.servo1_indicator = ServoIndicator("Servo 1")
        self.servo2_indicator = ServoIndicator("Servo 2")
        
        indicators_layout.addWidget(self.servo1_indicator)
        indicators_layout.addWidget(self.servo2_indicator)
        indicators_group.setLayout(indicators_layout)
        
        # Configuration des contrôles
        controls_group.setLayout(controls_layout)
        
        # Ajout des groupes au layout principal
        main_layout.addWidget(controls_group)
        main_layout.addWidget(indicators_group)
        
        # Boutons de contrôle
        buttons_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Connecter")
        self.start_server_button = QPushButton("Démarrer Serveur ASCOM")
        
        buttons_layout.addWidget(self.connect_button)
        buttons_layout.addWidget(self.start_server_button)
        
        main_layout.addLayout(buttons_layout)
        
        # Zone de commande personnalisée
        command_layout = QHBoxLayout()
        command_label = QLabel("Commande:")
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Entrez une commande...")
        self.send_command_button = QPushButton("Envoyer")
        self.send_command_button.setEnabled(False)  # Désactivé jusqu'à la connexion
        
        command_layout.addWidget(command_label)
        command_layout.addWidget(self.command_input)
        command_layout.addWidget(self.send_command_button)
        
        main_layout.addLayout(command_layout)
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
        
        # Connexions des signaux
        self.level_slider.valueChanged.connect(self.on_level_changed)
        self.strength_slider.valueChanged.connect(self.on_strength_changed)
        self.connect_button.clicked.connect(self.on_connect_clicked)
        self.start_server_button.clicked.connect(self.on_start_server_clicked)
        self.send_command_button.clicked.connect(self.on_send_command_clicked)
        
        self.logger.info("Interface utilisateur initialisée")
    
    @pyqtSlot(int)
    def on_level_changed(self, value):
        """Gère le changement de valeur du slider de level."""
        self.level_value_label.setText(f"{value}°")
        
        # Conversion de la valeur -45..45 en angle pour l'indicateur (0-360)
        indicator_angle = (value + 45) * 4  # Convertit -45..45 en 0-360 degrés
        self.servo1_indicator.set_angle(indicator_angle)
        self.logger.debug(f"Level changé: {value}°")
        
        # Envoi de la commande au microcontrôleur si connecté
        if self.serial_service.is_connected:
            command = f"LEVEL={value}"
            self.logger.debug(f"Envoi de la commande: {command}")
            self.serial_service.send_command(command)
    
    @pyqtSlot(int)
    def on_strength_changed(self, value):
        """Gère le changement de valeur du slider de strength."""
        self.strength_value_label.setText(str(value))
        self.servo2_indicator.set_angle(value * 3.6)  # Convertit 0-100 en 0-360 degrés
        self.logger.debug(f"Strength changé: {value}")
        
        # Envoi de la commande au microcontrôleur si connecté
        if self.serial_service.is_connected:
            command = f"STRENGTH={value}"
            self.logger.debug(f"Envoi de la commande: {command}")
            self.serial_service.send_command(command)
    
    @pyqtSlot()
    def on_connect_clicked(self):
        """Gère le clic sur le bouton de connexion."""
        # Si déjà connecté, déconnecter
        if self.serial_service.is_connected:
            self.logger.info("Déconnexion du périphérique")
            if self.serial_service.disconnect():
                self.status_bar.showMessage("Déconnecté")
                self.connect_button.setText("Connecter")
                self.send_command_button.setEnabled(False)
            else:
                self.status_bar.showMessage("Échec de la déconnexion")
            return
            
        # Connexion au périphérique série sur /dev/cu.usbmodem1101
        port = "/dev/cu.usbmodem1101"
        self.status_bar.showMessage(f"Connexion en cours sur {port}...")
        self.logger.info(f"Tentative de connexion sur {port}")
        
        try:
            if self.serial_service.connect(port):
                self.status_bar.showMessage(f"Connecté à {port}")
                self.connect_button.setText("Déconnecter")
                self.send_command_button.setEnabled(True)
                
                # Envoi de la commande STATUS
                self.logger.info("Envoi de la commande STATUS")
                self.serial_service.send_command("STATUS")
                
                # Lecture de la réponse
                response = self.serial_service.read_line()
                if response:
                    self.logger.info(f"Réponse à STATUS: {response}")
                    self.status_bar.showMessage(f"Connecté à {port} - Status: {response}")
                else:
                    self.logger.warning("Pas de réponse à la commande STATUS")
            else:
                self.status_bar.showMessage(f"Échec de la connexion à {port}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion: {str(e)}")
            QMessageBox.critical(self, "Erreur de connexion", 
                                f"Impossible de se connecter à {port}:\n{str(e)}")
            self.status_bar.showMessage(f"Erreur de connexion: {str(e)}")
    
    @pyqtSlot()
    def on_start_server_clicked(self):
        """Gère le clic sur le bouton de démarrage du serveur ASCOM."""
        # À implémenter: démarrage du serveur ASCOM Alpaca
        self.status_bar.showMessage("Démarrage du serveur ASCOM...")
        self.logger.info("Démarrage du serveur ASCOM")

    @pyqtSlot()
    def on_send_command_clicked(self):
        """Envoie une commande personnalisée au périphérique."""
        if not self.serial_service.is_connected:
            self.status_bar.showMessage("Pas de connexion active")
            return
            
        command = self.command_input.text().strip()
        if not command:
            return
            
        self.logger.info(f"Envoi de la commande: {command}")
        
        if self.serial_service.send_command(command):
            # Lecture de la réponse
            response = self.serial_service.read_line()
            if response:
                self.logger.info(f"Réponse: {response}")
                self.status_bar.showMessage(f"Réponse: {response}")
            else:
                self.logger.warning(f"Pas de réponse à la commande: {command}")
                self.status_bar.showMessage(f"Commande envoyée, pas de réponse")
        else:
            self.status_bar.showMessage(f"Échec de l'envoi de la commande")
            
        # Effacer le champ de saisie
        self.command_input.clear()
