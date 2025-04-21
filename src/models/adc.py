#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle pour représenter l'état de l'ADC (Automatic Declination Compensator).
"""

import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ServoState:
    """État d'un servo-moteur."""
    attached: bool = False
    pin: int = 0
    current_angle: float = 0
    target_angle: float = 0
    intermediate_angle: Optional[float] = None
    initializing: bool = False


@dataclass
class AdcState:
    """État complet de l'ADC."""
    level: int = 0
    strength: int = 50
    angles: Dict[str, float] = None
    
    def __post_init__(self):
        if self.angles is None:
            self.angles = {"angle1": 45, "angle2": 135}


class AdcModel:
    """
    Modèle représentant l'état complet de l'ADC et de ses servos.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ready: bool = False
        self.servo1 = ServoState()
        self.servo2 = ServoState()
        self.adc = AdcState()
    
    def update_from_json(self, json_data: str) -> bool:
        """
        Met à jour le modèle à partir d'une réponse JSON du périphérique.
        
        Args:
            json_data (str): Données JSON à analyser
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            data = json.loads(json_data)
            
            # Vérifier si c'est une réponse valide
            if "source" not in data or data["source"] != "system":
                return False
                
            # Mise à jour selon le type de commande
            command = data.get("command", "")
            
            if command == "status":
                self._update_from_status(data)
            elif command == "level":
                self._update_from_level(data)
            elif command == "strength":
                self._update_from_strength(data)
            elif command == "reset":
                self._update_from_reset(data)
            else:
                self.logger.warning("Commande inconnue dans la réponse JSON: %s", command)
                return False
                
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error("Erreur lors de l'analyse JSON: %s", str(e))
            return False
        except KeyError as e:
            self.logger.error("Clé manquante dans les données JSON: %s", str(e))
            return False
        except ValueError as e:
            self.logger.error("Erreur de valeur dans les données JSON: %s", str(e))
            return False
        except Exception as e:
            self.logger.error("Erreur inattendue lors de la mise à jour du modèle: %s", str(e))
            return False
    
    def _update_from_status(self, data: Dict[str, Any]) -> None:
        """Met à jour le modèle à partir d'une réponse à la commande STATUS."""
        self.ready = bool(data.get("ready", 0))
        
        # Mise à jour du servo 1
        if "servo1" in data:
            servo1_data = data["servo1"]
            self.servo1.attached = bool(servo1_data.get("attached", False))
            self.servo1.pin = int(servo1_data.get("pin", 0))
            self.servo1.current_angle = float(servo1_data.get("current_angle", 0))
            self.servo1.target_angle = float(servo1_data.get("target_angle", 0))
            if "intermediate_angle" in servo1_data:
                self.servo1.intermediate_angle = float(servo1_data["intermediate_angle"])
            self.servo1.initializing = bool(servo1_data.get("initializing", False))
        
        # Mise à jour du servo 2
        if "servo2" in data:
            servo2_data = data["servo2"]
            self.servo2.attached = bool(servo2_data.get("attached", False))
            self.servo2.pin = int(servo2_data.get("pin", 0))
            self.servo2.current_angle = float(servo2_data.get("current_angle", 0))
            self.servo2.target_angle = float(servo2_data.get("target_angle", 0))
            if "intermediate_angle" in servo2_data:
                self.servo2.intermediate_angle = float(servo2_data["intermediate_angle"])
            self.servo2.initializing = bool(servo2_data.get("initializing", False))
    
    def _update_from_level(self, data: Dict[str, Any]) -> None:
        """Met à jour le modèle à partir d'une réponse à la commande LEVEL."""
        if "level" in data:
            self.adc.level = int(data["level"])
        
        if "adc" in data:
            adc_data = data["adc"]
            self.adc.level = int(adc_data.get("level", self.adc.level))
            self.adc.strength = int(adc_data.get("strength", self.adc.strength))
            
            if "angles" in adc_data:
                angles_data = adc_data["angles"]
                self.adc.angles = {
                    "angle1": float(angles_data.get("angle1", 45)),
                    "angle2": float(angles_data.get("angle2", 135))
                }
    
    def _update_from_strength(self, data: Dict[str, Any]) -> None:
        """Met à jour le modèle à partir d'une réponse à la commande STRENGTH."""
        if "strength" in data:
            self.adc.strength = int(data["strength"])
        
        if "adc" in data:
            adc_data = data["adc"]
            self.adc.level = int(adc_data.get("level", self.adc.level))
            self.adc.strength = int(adc_data.get("strength", self.adc.strength))
            
            if "angles" in adc_data:
                angles_data = adc_data["angles"]
                self.adc.angles = {
                    "angle1": float(angles_data.get("angle1", 45)),
                    "angle2": float(angles_data.get("angle2", 135))
                }
    
    def _update_from_reset(self, data: Dict[str, Any]) -> None:
        """Met à jour le modèle à partir d'une réponse à la commande RESET."""
        # Vérifier le statut de la réinitialisation
        status = data.get("status", "")
        if status != "ok":
            self.logger.warning("Réinitialisation échouée avec statut: %s", status)
            return
            
        # Mise à jour des données ADC
        if "adc" in data:
            adc_data = data["adc"]
            self.adc.level = int(adc_data.get("level", 0))
            self.adc.strength = int(adc_data.get("strength", 50))
            
            if "angles" in adc_data:
                angles_data = adc_data["angles"]
                self.adc.angles = {
                    "angle1": float(angles_data.get("angle1", 45)),
                    "angle2": float(angles_data.get("angle2", 135))
                }
        
        # Mise à jour directe des angles si disponibles
        if "angles" in data:
            angles_data = data["angles"]
            if not self.adc.angles:
                self.adc.angles = {}
            self.adc.angles.update({
                "angle1": float(angles_data.get("angle1", 45)),
                "angle2": float(angles_data.get("angle2", 135))
            })
