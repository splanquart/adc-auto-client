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
class MpuState:
    """État du capteur MPU-6050."""
    initialized: bool = False
    calibrated: bool = False
    pitch: float = 0.0
    roll: float = 0.0
    level: int = 0


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
        self.mpu = MpuState()
    
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
            self.logger.info(f"Mise à jour du modèle avec la commande: {command}")
            if command == "status":
                self._update_from_status(data)
            elif command == "level":
                self._update_from_level(data)
            elif command == "strength":
                self._update_from_strength(data)
            elif command == "reset":
                self._update_from_reset(data)
            elif command == "mpu":
                self._update_from_mpu(data)
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
                
                # Mettre à jour les angles des servos à partir des angles de l'ADC
                self.servo1.current_angle = self.adc.angles["angle1"]
                self.servo1.target_angle = self.adc.angles["angle1"]
                self.servo2.current_angle = self.adc.angles["angle2"]
                self.servo2.target_angle = self.adc.angles["angle2"]
        # Mise à jour des angles des servos si disponibles
        if "angles" in data:
            angles_data = data["angles"]
            self.adc.angles = {
                "angle1": float(angles_data.get("angle1", 45)),
                "angle2": float(angles_data.get("angle2", 135))
            }
            
            # Mettre à jour les angles des servos à partir des angles de l'ADC
            self.servo1.current_angle = self.adc.angles["angle1"]
            self.servo1.target_angle = self.adc.angles["angle1"]
            self.servo2.current_angle = self.adc.angles["angle2"]
            self.servo2.target_angle = self.adc.angles["angle2"]
        
        # Mise à jour des données MPU (nouveau format)
        if "mpu6050" in data:
            mpu_data = data["mpu6050"]
            self.mpu.initialized = bool(mpu_data.get("initialized", False))
            
            if "pitch" in mpu_data:
                self.mpu.pitch = float(mpu_data.get("pitch", 0.0))
            if "roll" in mpu_data:
                self.mpu.roll = float(mpu_data.get("roll", 0.0))
            if "level" in mpu_data:
                self.mpu.level = int(mpu_data.get("level", 0))

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
        
        # Mise à jour directe des angles si disponibles sinon on se content de adc.angles
        if "angles" in data:
            angles_data = data["angles"]
            if not self.adc.angles:
                self.adc.angles = {}
            self.adc.angles.update({
                "angle1": float(angles_data.get("angle1", 45)),
                "angle2": float(angles_data.get("angle2", 135))
            })
            
    def _update_from_mpu(self, data: Dict[str, Any]) -> None:
        """Met à jour le modèle à partir d'une réponse à la commande MPU."""
        # Vérifier si les données MPU sont présentes
        if "mpu6050" not in data:
            self.logger.warning("Données MPU-6050 manquantes dans la réponse")
            self.logger.info("Réponse: %s", data)
            return
            
        mpu_data = data["mpu6050"]
        
        # Mise à jour de l'état du MPU
        self.mpu.initialized = bool(mpu_data.get("initialized", False))
        
        # Si une action spécifique a été effectuée
        action = mpu_data.get("action", "")
        if action == "calibrate":
            self.mpu.calibrated = True
            self.logger.info("MPU-6050 calibré avec succès")
        elif action == "init":
            self.logger.info("MPU-6050 initialisé avec succès")
        
        # Mise à jour des valeurs d'angle si disponibles
        if "pitch" in mpu_data:
            self.mpu.pitch = float(mpu_data.get("pitch", 0.0))
        if "roll" in mpu_data:
            self.mpu.roll = float(mpu_data.get("roll", 0.0))
        if "level" in mpu_data:
            self.mpu.level = int(mpu_data.get("level", 0))
