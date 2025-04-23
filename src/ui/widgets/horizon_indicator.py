#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Widget d'indicateur d'horizon artificiel pour l'affichage du niveau (level).
"""

import math
import logging
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath
)
from PyQt6.QtCore import Qt, QRectF, QPointF


class HorizonIndicator(QWidget):
    """
    Widget qui affiche graphiquement l'inclinaison sous forme d'horizon artificiel,
    similaire à ceux utilisés dans les cockpits d'avion.
    """
    
    def __init__(self, title="Horizon", parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.title = title
        self.angle = 0  # Angle en degrés (-90 à +90)
        self.min_angle = -90
        self.max_angle = 90
        self.current_range = (-45, 45)  # Plage actuelle du firmware
        self.setMinimumSize(200, 200)
        self.logger.debug("Indicateur d'horizon '%s' créé", self.title)
    
    def set_angle(self, angle):
        """
        Définit l'angle de l'indicateur et déclenche un rafraîchissement.
        
        Args:
            angle (float): Angle en degrés (-90 à +90)
        """
        # Limiter l'angle à la plage valide
        self.angle = max(self.min_angle, min(self.max_angle, angle))
        self.update()
        self.logger.debug("Angle de l'indicateur d'horizon '%s' mis à jour: %s", self.title, angle)
    
    def set_range(self, min_angle, max_angle):
        """
        Définit la plage d'angles supportée par le firmware.
        
        Args:
            min_angle (float): Angle minimum en degrés
            max_angle (float): Angle maximum en degrés
        """
        self.current_range = (min_angle, max_angle)
        self.update()
        self.logger.debug("Plage de l'indicateur d'horizon mise à jour: %s à %s", min_angle, max_angle)
    
    def paintEvent(self, _event):
        """
        Dessine l'indicateur d'horizon artificiel.
        
        Args:
            _event: Événement de peinture Qt (non utilisé)
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calcul des dimensions
        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        center_x = width / 2
        center_y = height / 2
        
        # Dessiner le titre
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(0, 0, width, 30, Qt.AlignmentFlag.AlignCenter, self.title)
        
        # Dessiner le cercle extérieur (cadre)
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        outer_rect = QRectF(center_x - size/2, center_y - size/2 + 10, size, size)
        painter.drawEllipse(outer_rect)
        
        # Sauvegarder l'état du peintre pour le clipping
        painter.save()
        
        # Définir la zone de clipping au cercle
        path = QPainterPath()
        path.addEllipse(outer_rect)
        painter.setClipPath(path)
        
        # Calculer la position de l'horizon basée sur l'angle
        horizon_y = center_y + 10 - (size / 2) * math.sin(math.radians(self.angle))
        
        # Dessiner le ciel (bleu)
        sky_gradient = QLinearGradient(0, center_y - size/2, 0, horizon_y)
        sky_gradient.setColorAt(0, QColor(135, 206, 250))  # Bleu ciel clair en haut
        sky_gradient.setColorAt(1, QColor(65, 105, 225))   # Bleu plus foncé près de l'horizon
        
        # Dessiner la terre (marron)
        ground_gradient = QLinearGradient(0, horizon_y, 0, center_y + size/2 + 10)
        ground_gradient.setColorAt(0, QColor(139, 69, 19))   # Marron foncé près de l'horizon
        ground_gradient.setColorAt(1, QColor(160, 82, 45))   # Marron plus clair en bas
        
        # Rotation pour l'inclinaison de l'horizon
        painter.translate(center_x, center_y + 10)
        painter.rotate(-self.angle)
        painter.translate(-center_x, -(center_y + 10))
        
        # Dessiner le rectangle du ciel
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sky_gradient))
        sky_rect = QRectF(center_x - size, center_y - size, size * 2, size)
        painter.drawRect(sky_rect)
        
        # Dessiner le rectangle de la terre
        painter.setBrush(QBrush(ground_gradient))
        ground_rect = QRectF(center_x - size, center_y, size * 2, size)
        painter.drawRect(ground_rect)
        
        # Dessiner la ligne d'horizon
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawLine(int(center_x - size), int(center_y),
                        int(center_x + size), int(center_y))
        
        # Restaurer l'état du peintre
        painter.restore()
        
        # Dessiner les graduations
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        
        # Dessiner les graduations principales tous les 10 degrés
        for i in range(-90, 91, 10):
            # Ne dessiner que si dans la plage visible
            if i < self.min_angle or i > self.max_angle:
                continue
                
            # Position verticale basée sur l'angle
            y_pos = center_y + 10 - (i / 90.0) * (size / 2)
            
            # Longueur de la graduation (plus longue pour les multiples de 30)
            line_length = 15 if i % 30 == 0 else 10
            
            # Dessiner la graduation à gauche
            painter.drawLine(int(center_x - size/2 + 5), int(y_pos),
                            int(center_x - size/2 + 5 + line_length), int(y_pos))
            
            # Dessiner la graduation à droite
            painter.drawLine(int(center_x + size/2 - 5), int(y_pos),
                            int(center_x + size/2 - 5 - line_length), int(y_pos))
            
            # Ajouter des étiquettes pour les angles principaux (multiples de 30)
            if i % 30 == 0:
                painter.setFont(QFont("Arial", 8))
                # Étiquette à gauche
                painter.drawText(int(center_x - size/2 + 5 + line_length + 2), int(y_pos + 4), f"{i}°")
                # Étiquette à droite
                painter.drawText(int(center_x + size/2 - 5 - line_length - 20), int(y_pos + 4), f"{i}°")
        
        # Dessiner l'indicateur de plage actuelle du firmware
        min_y = center_y + 10 - (self.current_range[0] / 90.0) * (size / 2)
        max_y = center_y + 10 - (self.current_range[1] / 90.0) * (size / 2)
        
        painter.setPen(QPen(QColor(255, 165, 0), 2))  # Orange
        painter.drawLine(int(center_x - size/2 - 5), int(min_y), int(center_x - size/2), int(min_y))
        painter.drawLine(int(center_x - size/2 - 5), int(max_y), int(center_x - size/2), int(max_y))
        painter.drawLine(int(center_x - size/2 - 5), int(min_y), int(center_x - size/2 - 5), int(max_y))
        
        # Dessiner l'avion (symbole fixe au centre)
        painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        # Ailes
        painter.drawLine(int(center_x - 20), int(center_y + 10),
                        int(center_x + 20), int(center_y + 10))
        # Fuselage
        painter.drawLine(int(center_x), int(center_y + 5),
                        int(center_x), int(center_y + 15))
        
        # Afficher la valeur de l'angle
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, height - 30, width, 30, Qt.AlignmentFlag.AlignCenter, f"{self.angle:.1f}°")
