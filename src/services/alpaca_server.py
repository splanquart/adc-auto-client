#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Service de serveur ASCOM Alpaca pour AdcAutoClient.
"""

import logging
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Callable
import socket
import urllib.parse


class AlpacaRequestHandler(BaseHTTPRequestHandler):
    """Gestionnaire de requêtes HTTP pour le serveur ASCOM Alpaca."""
    
    # Référence au service parent
    server_service = None
    
    def log_message(self, format, *args):
        """Redirige les logs vers le logger de l'application."""
        logging.getLogger("AlpacaServer").debug(format % args)
    
    def do_GET(self):
        """Gère les requêtes GET."""
        try:
            # Analyser l'URL
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            query = urllib.parse.parse_qs(parsed_url.query)
            
            # Convertir les paramètres de requête en dictionnaire
            params = {k: v[0] for k, v in query.items()}
            
            # Traiter la requête
            response = self.server_service.handle_request("GET", path, params)
            
            # Envoyer la réponse
            self.send_response(response.get("status", 200))
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response.get("data", {})).encode("utf-8"))
        
        except Exception as e:
            logging.getLogger("AlpacaServer").error(f"Erreur lors du traitement de la requête GET: {str(e)}")
            self.send_error(500, f"Erreur interne: {str(e)}")
    
    def do_PUT(self):
        """Gère les requêtes PUT."""
        try:
            # Analyser l'URL
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            
            # Lire le corps de la requête
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            
            # Convertir le corps JSON en dictionnaire
            params = json.loads(body) if body else {}
            
            # Traiter la requête
            response = self.server_service.handle_request("PUT", path, params)
            
            # Envoyer la réponse
            self.send_response(response.get("status", 200))
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response.get("data", {})).encode("utf-8"))
        
        except Exception as e:
            logging.getLogger("AlpacaServer").error(f"Erreur lors du traitement de la requête PUT: {str(e)}")
            self.send_error(500, f"Erreur interne: {str(e)}")


class AlpacaServerService:
    """
    Service de serveur ASCOM Alpaca pour la communication avec les systèmes d'astronomie.
    """
    
    def __init__(self, host="0.0.0.0", port=11111):
        """
        Initialise le service de serveur ASCOM Alpaca.
        
        Args:
            host (str): Adresse d'hôte du serveur. Par défaut "0.0.0.0" (toutes les interfaces).
            port (int): Port d'écoute du serveur. Par défaut 11111.
        """
        self.logger = logging.getLogger("AlpacaServer")
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.device_handlers = {}
        
        # Configuration d'Alpaca
        self.server_name = "AdcAutoClient"
        self.manufacturer = "AdcAuto"
        self.version = "1.0"
        
        # Configurer le gestionnaire de requêtes
        AlpacaRequestHandler.server_service = self
        
        self.logger.info(f"Service de serveur ASCOM Alpaca initialisé ({host}:{port})")
    
    def start(self) -> bool:
        """
        Démarre le serveur ASCOM Alpaca.
        
        Returns:
            bool: True si le serveur a démarré, False sinon
        """
        if self.is_running:
            self.logger.warning("Le serveur est déjà en cours d'exécution")
            return False
        
        try:
            self.server = HTTPServer((self.host, self.port), AlpacaRequestHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.is_running = True
            self.logger.info(f"Serveur ASCOM Alpaca démarré sur {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du démarrage du serveur: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Arrête le serveur ASCOM Alpaca.
        
        Returns:
            bool: True si le serveur a été arrêté, False sinon
        """
        if not self.is_running:
            self.logger.warning("Le serveur n'est pas en cours d'exécution")
            return False
        
        try:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join(timeout=1.0)
            self.is_running = False
            self.server = None
            self.server_thread = None
            self.logger.info("Serveur ASCOM Alpaca arrêté")
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt du serveur: {str(e)}")
            return False
    
    def register_device_handler(self, device_type: str, device_number: int, 
                               handler: Callable[[str, str, Dict[str, Any]], Dict[str, Any]]) -> None:
        """
        Enregistre un gestionnaire pour un type de périphérique ASCOM.
        
        Args:
            device_type (str): Type de périphérique ASCOM (ex: "focuser", "rotator")
            device_number (int): Numéro du périphérique
            handler (Callable): Fonction de traitement des requêtes pour ce périphérique
        """
        key = f"{device_type}/{device_number}"
        self.device_handlers[key] = handler
        self.logger.info(f"Gestionnaire enregistré pour le périphérique {key}")
    
    def unregister_device_handler(self, device_type: str, device_number: int) -> None:
        """
        Supprime un gestionnaire de périphérique.
        
        Args:
            device_type (str): Type de périphérique ASCOM
            device_number (int): Numéro du périphérique
        """
        key = f"{device_type}/{device_number}"
        if key in self.device_handlers:
            del self.device_handlers[key]
            self.logger.info(f"Gestionnaire supprimé pour le périphérique {key}")
    
    def handle_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite une requête HTTP pour le serveur ASCOM Alpaca.
        
        Args:
            method (str): Méthode HTTP (GET, PUT)
            path (str): Chemin de la requête
            params (Dict[str, Any]): Paramètres de la requête
            
        Returns:
            Dict[str, Any]: Réponse à envoyer au client
        """
        self.logger.debug(f"Requête reçue: {method} {path} {params}")
        
        # Gestion des endpoints de base d'Alpaca
        if path == "/api/v1/management/apiversions":
            return {
                "status": 200,
                "data": {
                    "Value": [1],
                    "ClientTransactionID": params.get("ClientTransactionID", 0),
                    "ServerTransactionID": 1
                }
            }
        
        elif path == "/api/v1/management/v1/description":
            return {
                "status": 200,
                "data": {
                    "Value": {
                        "ServerName": self.server_name,
                        "Manufacturer": self.manufacturer,
                        "ManufacturerVersion": self.version,
                        "Location": f"{socket.gethostname()}:{self.port}"
                    },
                    "ClientTransactionID": params.get("ClientTransactionID", 0),
                    "ServerTransactionID": 1
                }
            }
        
        elif path == "/api/v1/management/v1/configureddevices":
            # Liste des périphériques configurés
            devices = []
            for key in self.device_handlers:
                device_type, device_number = key.split("/")
                devices.append({
                    "DeviceName": f"{device_type}{device_number}",
                    "DeviceType": device_type,
                    "DeviceNumber": int(device_number),
                    "UniqueID": f"{device_type}{device_number}"
                })
            
            return {
                "status": 200,
                "data": {
                    "Value": devices,
                    "ClientTransactionID": params.get("ClientTransactionID", 0),
                    "ServerTransactionID": 1
                }
            }
        
        # Traitement des requêtes pour les périphériques
        # Format du chemin: /api/v1/{device_type}/{device_number}/{method}
        parts = path.strip("/").split("/")
        if len(parts) >= 5 and parts[0] == "api" and parts[1] == "v1":
            device_type = parts[2]
            try:
                device_number = int(parts[3])
                device_method = parts[4]
                
                # Recherche du gestionnaire pour ce périphérique
                key = f"{device_type}/{device_number}"
                if key in self.device_handlers:
                    # Appel du gestionnaire avec la méthode et les paramètres
                    handler = self.device_handlers[key]
                    return handler(method, device_method, params)
                else:
                    self.logger.warning(f"Aucun gestionnaire pour le périphérique {key}")
                    return {
                        "status": 404,
                        "data": {
                            "ErrorMessage": f"Périphérique non trouvé: {device_type}/{device_number}",
                            "ErrorNumber": 1,
                            "ClientTransactionID": params.get("ClientTransactionID", 0),
                            "ServerTransactionID": 1
                        }
                    }
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de la requête: {str(e)}")
                return {
                    "status": 500,
                    "data": {
                        "ErrorMessage": f"Erreur interne: {str(e)}",
                        "ErrorNumber": 2,
                        "ClientTransactionID": params.get("ClientTransactionID", 0),
                        "ServerTransactionID": 1
                    }
                }
        
        # Endpoint non reconnu
        return {
            "status": 404,
            "data": {
                "ErrorMessage": f"Endpoint non reconnu: {path}",
                "ErrorNumber": 3,
                "ClientTransactionID": params.get("ClientTransactionID", 0),
                "ServerTransactionID": 1
            }
        }
