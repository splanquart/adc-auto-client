#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Widget d'indicateur graphique pour l'état des servos.
"""

import math
import logging
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt6.QtCore import Qt, QRectF


class ServoIndicator(QWidget):
    """
    Widget qui affiche graphiquement l'état d'un servo sous forme de roue.
    """
    
    def __init__(self, title="Servo", parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.title = title
        self.angle = 0  # Angle en degrés (0-360)
        self.setMinimumSize(200, 200)
        self.logger.debug(f"Indicateur de servo '{title}' créé")
    
    def set_angle(self, angle):
        """
        Définit l'angle de l'indicateur et déclenche un rafraîchissement.
        
        Args:
            angle (float): Angle en degrés (0-360)
        """
        self.angle = angle
        self.update()
        self.logger.debug(f"Angle de l'indicateur '{self.title}' mis à jour: {angle}")
    
    def paintEvent(self, event):
        """
        Dessine l'indicateur de servo.
        
        Args:
            event: Événement de peinture Qt
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
        
        # Dessiner le cercle extérieur
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        outer_rect = QRectF(center_x - size/2, center_y - size/2 + 10, size, size)
        painter.drawEllipse(outer_rect)
        
        # Dessiner les graduations
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        for i in range(0, 360, 30):
            angle_rad = math.radians(i)
            start_x = center_x + (size/2 - 10) * math.cos(angle_rad)
            start_y = center_y + (size/2 - 10) * math.sin(angle_rad) + 10
            end_x = center_x + (size/2) * math.cos(angle_rad)
            end_y = center_y + (size/2) * math.sin(angle_rad) + 10
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))
            
            # Ajouter des étiquettes pour les angles principaux
            if i % 90 == 0:
                text_x = center_x + (size/2 + 15) * math.cos(angle_rad) - 10
                text_y = center_y + (size/2 + 15) * math.sin(angle_rad) + 15
                # Corriger l'affichage des angles pour correspondre à la réalité physique
                displayed_angle = (i + 90) % 360
                painter.drawText(int(text_x), int(text_y), f"{displayed_angle}°")
        
        # Dessiner l'indicateur (aiguille)
        painter.setPen(QPen(Qt.GlobalColor.red, 3))
        angle_rad = math.radians(self.angle - 90)  # -90 pour que 0 soit en haut
        end_x = center_x + (size/2 - 20) * math.cos(angle_rad)
        end_y = center_y + (size/2 - 20) * math.sin(angle_rad) + 10
        painter.drawLine(int(center_x), int(center_y + 10), int(end_x), int(end_y))
        
        # Dessiner le point central
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        painter.drawEllipse(int(center_x - 5), int(center_y + 5), 10, 10)
        
        # Afficher la valeur de l'angle
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, height - 30, width, 30, Qt.AlignmentFlag.AlignCenter, f"{self.angle:.1f}°")
