#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Service de communication série pour AdcAutoClient.
"""

import logging
import time
import threading
from typing import Optional, Callable, List, Dict
import serial
import serial.tools.list_ports


class SerialService:
    """
    Service de gestion de la communication série avec les périphériques.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.serial_port: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_listening = False
        self.listener_thread: Optional[threading.Thread] = None
        self.callbacks: List[Callable[[str], None]] = []
    
    def get_available_ports(self) -> List[Dict[str, str]]:
        """
        Récupère la liste des ports série disponibles.
        
        Returns:
            List[Dict[str, str]]: Liste des ports série disponibles avec leurs informations
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unknown'
            })
        self.logger.info(f"Ports série disponibles: {len(ports)}")
        return ports
    
    def connect(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> bool:
        """
        Établit une connexion avec un port série.
        
        Args:
            port (str): Nom du port série
            baudrate (int, optional): Vitesse de communication. Par défaut 9600.
            timeout (float, optional): Délai d'attente en secondes. Par défaut 1.0.
            
        Returns:
            bool: True si la connexion est établie, False sinon
        """
        if self.is_connected:
            self.logger.warning("Déjà connecté à un port série")
            return False
        
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
            self.is_connected = True
            self.logger.info(f"Connecté au port série {port} à {baudrate} bauds")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Erreur de connexion au port série {port}: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Ferme la connexion série.
        
        Returns:
            bool: True si la déconnexion est réussie, False sinon
        """
        if not self.is_connected:
            self.logger.warning("Pas de connexion série active")
            return False
        
        try:
            self.stop_listening()
            self.serial_port.close()
            self.is_connected = False
            self.serial_port = None
            self.logger.info("Déconnecté du port série")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la déconnexion: {str(e)}")
            return False
    
    def send_command(self, command: str) -> bool:
        """
        Envoie une commande au périphérique série.
        
        Args:
            command (str): Commande à envoyer
            
        Returns:
            bool: True si la commande a été envoyée, False sinon
        """
        if not self.is_connected or not self.serial_port:
            self.logger.error("Impossible d'envoyer la commande: pas de connexion série")
            return False
        
        try:
            # Ajouter un retour à la ligne si nécessaire
            if not command.endswith('\n'):
                command += '\n'
            
            self.serial_port.write(command.encode('utf-8'))
            self.logger.debug(f"Commande envoyée: {command.strip()}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de la commande: {str(e)}")
            return False
    
    def read_line(self) -> Optional[str]:
        """
        Lit une ligne depuis le port série.
        
        Returns:
            Optional[str]: Ligne lue ou None en cas d'erreur
        """
        if not self.is_connected or not self.serial_port:
            self.logger.error("Impossible de lire: pas de connexion série")
            return None
        
        try:
            line = self.serial_port.readline().decode('utf-8').strip()
            if line:
                self.logger.debug(f"Ligne reçue: {line}")
            return line
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture: {str(e)}")
            return None
    
    def start_listening(self) -> bool:
        """
        Démarre l'écoute en continu du port série dans un thread séparé.
        
        Returns:
            bool: True si l'écoute a démarré, False sinon
        """
        if not self.is_connected or not self.serial_port:
            self.logger.error("Impossible de démarrer l'écoute: pas de connexion série")
            return False
        
        if self.is_listening:
            self.logger.warning("L'écoute est déjà active")
            return False
        
        self.is_listening = True
        self.listener_thread = threading.Thread(target=self._listener_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        self.logger.info("Écoute du port série démarrée")
        return True
    
    def stop_listening(self) -> bool:
        """
        Arrête l'écoute du port série.
        
        Returns:
            bool: True si l'écoute a été arrêtée, False sinon
        """
        if not self.is_listening:
            self.logger.warning("L'écoute n'est pas active")
            return False
        
        self.is_listening = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
            self.listener_thread = None
        
        self.logger.info("Écoute du port série arrêtée")
        return True
    
    def register_callback(self, callback: Callable[[str], None]) -> None:
        """
        Enregistre une fonction de rappel pour les données reçues.
        
        Args:
            callback (Callable[[str], None]): Fonction à appeler avec les données reçues
        """
        self.callbacks.append(callback)
        self.logger.debug(f"Callback enregistré, total: {len(self.callbacks)}")
    
    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """
        Supprime une fonction de rappel.
        
        Args:
            callback (Callable[[str], None]): Fonction à supprimer
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            self.logger.debug(f"Callback supprimé, total: {len(self.callbacks)}")
    
    def _listener_loop(self) -> None:
        """
        Boucle d'écoute du port série, exécutée dans un thread séparé.
        """
        self.logger.debug("Thread d'écoute démarré")
        
        while self.is_listening and self.is_connected and self.serial_port:
            try:
                line = self.read_line()
                if line:
                    # Appel des callbacks enregistrés
                    for callback in self.callbacks:
                        try:
                            callback(line)
                        except Exception as e:
                            self.logger.error(f"Erreur dans un callback: {str(e)}")
                else:
                    # Petite pause pour éviter de surcharger le CPU
                    time.sleep(0.01)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'écoute: {str(e)}")
                time.sleep(0.1)
        
        self.logger.debug("Thread d'écoute terminé")
