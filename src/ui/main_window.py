#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application AdcAutoClient.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSlider, QGroupBox, QPushButton, QStatusBar,
    QLineEdit, QMessageBox, QSplitter, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from src.ui.widgets.servo_indicator import ServoIndicator
from src.ui.widgets.horizon_indicator import HorizonIndicator
from src.services.serial_service import SerialService
from src.models.adc import AdcModel
from src.services.device_scanner import scan_adc_devices, load_last_port, save_last_port


class PortScannerThread(QThread):
    """Scanne les ports série à la recherche du device ADC-Auto (hors UI thread)."""

    scan_finished = pyqtSignal(list)

    def run(self):
        try:
            devices = scan_adc_devices()
        except Exception as e:
            logging.getLogger(__name__).error("Erreur pendant le scan des ports: %s", e)
            devices = []
        self.scan_finished.emit(devices)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.serial_service = SerialService()
        self.adc_model = AdcModel()
        self.devices = []               # devices ADC-Auto détectés par le scan
        self.scan_thread = None         # thread de scan en cours
        self.init_ui()
        
        # Timer pour mettre à jour régulièrement l'état du système
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_data)
        self.status_timer.setInterval(2500)  # Mise à jour toutes les 2.5 secondes

        # Scan automatique des ports au démarrage
        QTimer.singleShot(200, self.start_port_scan)
        
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
        
        # Groupe pour l'indicateur d'horizon
        horizon_group = QGroupBox("Indicateur d'Horizon")
        horizon_layout = QVBoxLayout()
        
        # Indicateur d'horizon
        self.horizon_indicator = HorizonIndicator("Niveau")
        self.horizon_indicator.set_range(-45, 45)  # Plage actuelle du firmware
        
        # Boutons pour le MPU
        mpu_buttons_layout = QHBoxLayout()
        self.init_mpu_button = QPushButton("Initialiser MPU")
        self.calibrate_mpu_button = QPushButton("Calibrer MPU")
        self.mpu_status_label = QLabel("MPU: Non initialisé")
        
        # Connexion des signaux des boutons MPU
        self.init_mpu_button.clicked.connect(self.on_init_mpu_clicked)
        self.calibrate_mpu_button.clicked.connect(self.on_calibrate_mpu_clicked)
        
        # Désactiver le bouton de calibration jusqu'à l'initialisation
        self.calibrate_mpu_button.setEnabled(False)
        
        # Ajout des boutons au layout
        mpu_buttons_layout.addWidget(self.init_mpu_button)
        mpu_buttons_layout.addWidget(self.calibrate_mpu_button)
        mpu_buttons_layout.addWidget(self.mpu_status_label)
        
        # Ajout de l'indicateur et des boutons au layout d'horizon
        horizon_layout.addWidget(self.horizon_indicator)
        horizon_layout.addLayout(mpu_buttons_layout)
        horizon_group.setLayout(horizon_layout)
        
        # Configuration des contrôles
        controls_group.setLayout(controls_layout)

        # Ajout des groupes au layout principal
        main_layout.addWidget(controls_group)
        main_layout.addWidget(indicators_group)
        main_layout.addWidget(horizon_group)
        
        # Zone connexion : sélecteur de port (scan auto) + actualiser + connecter
        connection_layout = QHBoxLayout()
        connection_label = QLabel("Port ADC:")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(240)
        self.refresh_ports_button = QPushButton("Actualiser")
        self.connect_button = QPushButton("Connecter")
        connection_layout.addWidget(connection_label)
        connection_layout.addWidget(self.port_combo, 1)
        connection_layout.addWidget(self.refresh_ports_button)
        connection_layout.addWidget(self.connect_button)
        main_layout.addLayout(connection_layout)

        # Boutons de contrôle
        buttons_layout = QHBoxLayout()

        self.reset_button = QPushButton("Réinitialiser")
        self.reset_button.setEnabled(False)  # Désactivé jusqu'à la connexion
        self.start_server_button = QPushButton("Démarrer Serveur ASCOM")

        buttons_layout.addWidget(self.reset_button)
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
        self.refresh_ports_button.clicked.connect(self.start_port_scan)
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.start_server_button.clicked.connect(self.on_start_server_clicked)
        self.send_command_button.clicked.connect(self.on_send_command_clicked)
        
        self.logger.info("Interface utilisateur initialisée")
    
    def update_ui_from_model(self):
        """Met à jour l'interface utilisateur à partir du modèle ADC."""
        # Mise à jour des indicateurs de servo
        self.servo1_indicator.set_angle(self.adc_model.adc.angles["angle1"])
        self.servo2_indicator.set_angle(self.adc_model.adc.angles["angle2"])
        
        # Mise à jour des sliders
        self.level_slider.setValue(self.adc_model.adc.level)
        self.level_value_label.setText(f"{self.adc_model.adc.level}°")
        
        self.strength_slider.setValue(self.adc_model.adc.strength)
        self.strength_value_label.setText(f"{self.adc_model.adc.strength}")
        
        # Mise à jour de l'état du MPU
        if self.adc_model.mpu.initialized:
            self.init_mpu_button.setEnabled(False)
            self.calibrate_mpu_button.setEnabled(True)
            
            # Afficher les valeurs de pitch, roll et level
            mpu_status = f"MPU: Initialisé | Pitch: {self.adc_model.mpu.pitch:.1f}° | Roll: {self.adc_model.mpu.roll:.1f}° | Level: {self.adc_model.mpu.level}°"
            self.mpu_status_label.setText(mpu_status)
            
            # Mise à jour de l'indicateur d'horizon avec les données du MPU
            self.horizon_indicator.set_angle(self.adc_model.mpu.level)
            
            # Démarrer le timer MPU s'il n'est pas déjà actif
            if not self.status_timer.isActive() and hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected:
                self.status_timer.start()
        else:
            self.init_mpu_button.setEnabled(hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected)
            self.calibrate_mpu_button.setEnabled(False)
            self.mpu_status_label.setText("MPU: Non initialisé")
            
        # Mise à jour des boutons
        self.reset_button.setEnabled(hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected)
        
        # Mise à jour de la barre de statut
        if hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected:
            # Utiliser le port du serial_service s'il existe
            port_info = "périphérique"
            if hasattr(self.serial_service, 'serial_port') and self.serial_service.serial_port:
                if hasattr(self.serial_service.serial_port, 'port'):
                    port_info = self.serial_service.serial_port.port
            self.statusBar().showMessage(f"Connecté à {port_info}")
        else:
            self.statusBar().showMessage("Non connecté")

    def process_response(self, response):
        """Traite une réponse du périphérique."""
        try:
            if not response:
                return
                
            # Mettre à jour le modèle avec la réponse
            if self.adc_model.update_from_json(response):
                # Mettre à jour l'interface utilisateur
                self.logger.info("Mise à jour de l'interface utilisateur")
                self.update_ui_from_model()
                
                # Afficher la réponse dans la barre de statut
                self.status_bar.showMessage(f"Réponse: {response}")
                self.logger.info("Modèle mis à jour avec succès")
            else:
                self.logger.warning(f"Impossible de mettre à jour le modèle avec la réponse: {response}")
        except ValueError as e:
            self.logger.error(f"Erreur de valeur lors du traitement de la réponse: {e}")
        except KeyError as e:
            self.logger.error(f"Clé manquante lors du traitement de la réponse: {e}")
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors du traitement de la réponse: {e}")
    
    @pyqtSlot(int)
    def on_level_changed(self, value):
        """Gère le changement de valeur du slider de level."""
        self.level_value_label.setText(f"{value}°")
        
        # Envoi de la commande au microcontrôleur si connecté
        if hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected:
            command = f"LEVEL={value}"
            self.logger.debug(f"Envoi de la commande: {command}")
            self.serial_service.send_command(command)
            
            # Lecture et traitement de la réponse
            response = self.serial_service.read_line()
            if response:
                self.logger.info(f"Réponse à LEVEL={value}: {response}")
                self.process_response(response)
    
    @pyqtSlot(int)
    def on_strength_changed(self, value):
        """Gère le changement de valeur du slider de strength."""
        self.strength_value_label.setText(f"{value}")
        
        # Envoi de la commande au microcontrôleur si connecté
        if hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected:
            command = f"STRENGTH={value}"
            self.logger.debug(f"Envoi de la commande: {command}")
            self.serial_service.send_command(command)
            
            # Lecture et traitement de la réponse
            response = self.serial_service.read_line()
            if response:
                self.logger.info(f"Réponse à STRENGTH={value}: {response}")
                self.process_response(response)
    
    @pyqtSlot()
    def start_port_scan(self):
        """Lance le scan des ports série en arrière-plan (hors UI thread)."""
        if self.serial_service.is_connected:
            self.status_bar.showMessage("Déconnectez-vous avant de rescaner les ports.")
            return
        if self.scan_thread and self.scan_thread.isRunning():
            return
        self.status_bar.showMessage("Scan des ports série...")
        self.refresh_ports_button.setEnabled(False)
        self.scan_thread = PortScannerThread(self)
        self.scan_thread.scan_finished.connect(self.on_scan_finished)
        self.scan_thread.start()

    @pyqtSlot(list)
    def on_scan_finished(self, devices):
        """Met à jour le sélecteur de port avec les devices trouvés."""
        self.devices = devices
        self.refresh_ports_button.setEnabled(True)
        self.port_combo.clear()
        if devices:
            last = load_last_port()
            preferred_idx = 0
            for i, d in enumerate(devices):
                self.port_combo.addItem(f"{d['name']} — {d['port']}", d["port"])
                if d["port"] == last:
                    preferred_idx = i
            self.port_combo.setCurrentIndex(preferred_idx)
            self.status_bar.showMessage(
                f"{len(devices)} device(s) ADC détecté(s) — sélectionnez puis Connecter")
        else:
            self.port_combo.addItem("Aucun ADC détecté — Actualiser", None)
            self.status_bar.showMessage("Aucun ADC détecté. Vérifiez le câble USB.")

    @pyqtSlot()
    def on_connect_clicked(self):
        """Gère le clic sur le bouton de connexion."""
        # Si déjà connecté, déconnecter
        if hasattr(self.serial_service, 'is_connected') and self.serial_service.is_connected:
            self.logger.info("Déconnexion du périphérique")
            if self.serial_service.disconnect():
                self.status_bar.showMessage("Déconnecté")
                self.connect_button.setText("Connecter")
                self.send_command_button.setEnabled(False)
                self.reset_button.setEnabled(False)
                self.init_mpu_button.setEnabled(False)
                self.calibrate_mpu_button.setEnabled(False)
                self.refresh_ports_button.setEnabled(True)
                self.port_combo.setEnabled(True)
                
                # Arrêter le timer MPU
                if self.status_timer.isActive():
                    self.status_timer.stop()
            else:
                self.status_bar.showMessage("Échec de la déconnexion")
            return
            
        # Connexion au périphérique sélectionné dans le menu déroulant
        port = self.port_combo.currentData()
        if not port:
            self.status_bar.showMessage("Aucun port sélectionné — cliquez sur Actualiser.")
            return
        self.status_bar.showMessage(f"Connexion en cours sur {port}...")
        self.logger.info(f"Tentative de connexion sur {port}")
        
        try:
            if self.serial_service.connect(port):
                self.status_bar.showMessage(f"Connecté à {port}")
                self.connect_button.setText("Déconnecter")
                self.send_command_button.setEnabled(True)
                self.reset_button.setEnabled(True)
                self.init_mpu_button.setEnabled(True)
                self.refresh_ports_button.setEnabled(False)
                self.port_combo.setEnabled(False)
                save_last_port(port)
                
                # Envoyer la commande STATUS pour initialiser l'état
                self.logger.info("Envoi de la commande STATUS")
                self.serial_service.send_command("STATUS")
                response = self.serial_service.read_line()
                if response:
                    self.logger.info(f"Réponse à STATUS: {response}")
                    self.process_response(response)
                    
                # Envoyer la commande LEVEL pour obtenir le niveau actuel
                self.logger.info("Envoi de la commande LEVEL")
                self.serial_service.send_command("LEVEL")
                response = self.serial_service.read_line()
                if response:
                    self.logger.info(f"Réponse à LEVEL: {response}")
                    self.process_response(response)
                    
                # Envoyer la commande STRENGTH pour obtenir la force actuelle
                self.logger.info("Envoi de la commande STRENGTH")
                self.serial_service.send_command("STRENGTH")
                response = self.serial_service.read_line()
                if response:
                    self.logger.info(f"Réponse à STRENGTH: {response}")
                    self.process_response(response)
                    
                # Vérifier l'état du système
                self.update_status_data()
            else:
                self.status_bar.showMessage(f"Échec de la connexion à {port}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion: {str(e)}")
            self.status_bar.showMessage(f"Erreur: {str(e)}")

    @pyqtSlot()
    def on_start_server_clicked(self):
        """Gère le clic sur le bouton de démarrage du serveur ASCOM."""
        self.logger.info("Démarrage du serveur ASCOM")
        self.status_bar.showMessage("Serveur ASCOM démarré")
    
    @pyqtSlot()
    def on_send_command_clicked(self):
        """Envoie une commande personnalisée au périphérique."""
        if not hasattr(self.serial_service, 'is_connected') or not self.serial_service.is_connected:
            self.status_bar.showMessage("Pas de connexion active")
            return
            
        # Récupérer la commande depuis le champ de texte
        command = self.command_input.text().strip()
        if not command:
            self.status_bar.showMessage("Commande vide")
            return
            
        self.logger.info(f"Envoi de la commande: {command}")
        
        if self.serial_service.send_command(command):
            # Lecture de la réponse
            response = self.serial_service.read_line()
            if response:
                self.logger.info(f"Réponse: {response}")
                self.status_bar.showMessage(f"Réponse reçue")
                self.process_response(response)
            else:
                self.logger.warning(f"Pas de réponse à la commande: {command}")
                self.status_bar.showMessage(f"Commande envoyée, pas de réponse")
        else:
            self.status_bar.showMessage(f"Échec de l'envoi de la commande")
        
        # Effacer le champ de saisie
        self.command_input.clear()

    @pyqtSlot()
    def on_reset_clicked(self):
        """Gère le clic sur le bouton de réinitialisation."""
        if not hasattr(self.serial_service, 'is_connected') or not self.serial_service.is_connected:
            self.status_bar.showMessage("Pas de connexion active")
            return
            
        self.logger.info("Envoi de la commande RESET")
        
        if self.serial_service.send_command("RESET"):
            # Lecture de la réponse
            response = self.serial_service.read_line()
            if response:
                self.logger.info("Réponse à RESET: %s", response)
                self.status_bar.showMessage("Réinitialisation effectuée")
                self.process_response(response)
            else:
                self.logger.warning("Pas de réponse à la commande RESET")
                self.status_bar.showMessage("Commande RESET envoyée, pas de réponse")
        else:
            self.status_bar.showMessage("Échec de l'envoi de la commande RESET")

    @pyqtSlot()
    def on_init_mpu_clicked(self):
        """Gère le clic sur le bouton d'initialisation du MPU."""
        if not hasattr(self.serial_service, 'is_connected') or not self.serial_service.is_connected:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord connecter le périphérique.")
            return
            
        self.logger.info("Envoi de la commande: MPU=init")
        self.serial_service.send_command("MPU=init")
        
        # Lecture et traitement de la réponse
        response = self.serial_service.read_line()
        if response:
            self.logger.info(f"Réponse: {response}")
            self.process_response(response)
            
            # Mettre à jour l'état du MPU
            self.update_status_data()
    
    @pyqtSlot()
    def on_calibrate_mpu_clicked(self):
        """Gère le clic sur le bouton de calibration du MPU."""
        if not hasattr(self.serial_service, 'is_connected') or not self.serial_service.is_connected:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord connecter le périphérique.")
            return
            
        if not self.adc_model.mpu.initialized:
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord initialiser le MPU.")
            return
            
        self.logger.info("Envoi de la commande: MPU=calibrate")
        self.serial_service.send_command("MPU=calibrate")
        
        # Lecture et traitement de la réponse
        response = self.serial_service.read_line()
        if response:
            self.logger.info(f"Réponse: {response}")
            self.process_response(response)
            
            # Mettre à jour l'état du MPU
            self.update_status_data()
    
    @pyqtSlot()
    def update_status_data(self):
        """Met à jour les données d'état du système (MPU et servos)."""
        if not hasattr(self.serial_service, 'is_connected') or not self.serial_service.is_connected:
            return
            
        self.logger.debug("Mise à jour des données d'état")
        self.serial_service.send_command("STATUS")
        
        # Lecture et traitement de la réponse
        response = self.serial_service.read_line()
        if response:
            self.logger.debug(f"Réponse STATUS: {response}")
            self.process_response(response)
