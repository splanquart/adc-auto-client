#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modèle pour les servos dans AdcAutoClient.
"""

import logging
from typing import Optional, Callable


class Servo:
    """
    Modèle représentant un servo avec ses propriétés et comportements.
    """
    
    def __init__(self, name: str, servo_id: int = 1):
        """
        Initialise un nouveau servo.
        
        Args:
            name (str): Nom du servo
            servo_id (int, optional): Identifiant du servo. Par défaut 1.
        """
        self.logger = logging.getLogger(__name__)
        self.name = name
        self.servo_id = servo_id
        self.position = 0.0  # Position actuelle (0-100)
        self.target_position = 0.0  # Position cible (0-100)
        self.is_moving = False
        self.callbacks = []
        self.logger.debug(f"Servo '{name}' (ID: {servo_id}) créé")
    
    def set_position(self, position: float) -> None:
        """
        Définit la position actuelle du servo.
        
        Args:
            position (float): Position (0-100)
        """
        # Limiter la position à la plage 0-100
        position = max(0.0, min(100.0, position))
        
        # Mettre à jour la position
        old_position = self.position
        self.position = position
        
        # Notifier les observateurs si la position a changé
        if old_position != self.position:
            self.logger.debug(f"Position du servo '{self.name}' mise à jour: {self.position}")
            self._notify_observers()
    
    def move_to(self, target_position: float) -> None:
        """
        Définit la position cible du servo.
        
        Args:
            target_position (float): Position cible (0-100)
        """
        # Limiter la position cible à la plage 0-100
        target_position = max(0.0, min(100.0, target_position))
        
        # Mettre à jour la position cible
        self.target_position = target_position
        self.is_moving = True
        
        self.logger.debug(f"Servo '{self.name}' en mouvement vers la position {target_position}")
        
        # Dans une application réelle, cette méthode enverrait une commande au servo
        # via le service de communication série
        
        # Pour l'instant, nous simulons le mouvement en mettant directement à jour la position
        self.set_position(target_position)
        self.is_moving = False
    
    def stop(self) -> None:
        """
        Arrête le mouvement du servo.
        """
        if self.is_moving:
            self.is_moving = False
            self.target_position = self.position
            self.logger.debug(f"Servo '{self.name}' arrêté à la position {self.position}")
    
    def register_observer(self, callback: Callable[[float], None]) -> None:
        """
        Enregistre une fonction de rappel pour les changements de position.
        
        Args:
            callback (Callable[[float], None]): Fonction à appeler avec la nouvelle position
        """
        self.callbacks.append(callback)
        self.logger.debug(f"Observateur enregistré pour le servo '{self.name}'")
    
    def unregister_observer(self, callback: Callable[[float], None]) -> None:
        """
        Supprime une fonction de rappel.
        
        Args:
            callback (Callable[[float], None]): Fonction à supprimer
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            self.logger.debug(f"Observateur supprimé pour le servo '{self.name}'")
    
    def _notify_observers(self) -> None:
        """
        Notifie tous les observateurs du changement de position.
        """
        for callback in self.callbacks:
            try:
                callback(self.position)
            except Exception as e:
                self.logger.error(f"Erreur dans un observateur du servo '{self.name}': {str(e)}")
    
    def to_dict(self) -> dict:
        """
        Convertit le servo en dictionnaire pour la sérialisation.
        
        Returns:
            dict: Représentation du servo sous forme de dictionnaire
        """
        return {
            "name": self.name,
            "servo_id": self.servo_id,
            "position": self.position,
            "target_position": self.target_position,
            "is_moving": self.is_moving
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Servo':
        """
        Crée un servo à partir d'un dictionnaire.
        
        Args:
            data (dict): Dictionnaire contenant les données du servo
            
        Returns:
            Servo: Instance de servo créée
        """
        servo = cls(data["name"], data["servo_id"])
        servo.position = data["position"]
        servo.target_position = data["target_position"]
        servo.is_moving = data["is_moving"]
        return servo
