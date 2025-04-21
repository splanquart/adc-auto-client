# AdcAutoClient

Une application cliente pour le contrôle de servos avec interface graphique PyQt6 et communication série.

## Fonctionnalités

- Interface utilisateur avec sliders pour le level et strength
- Affichage graphique de l'état des servos
- Serveur ASCOM Alpaca pour la communication avec les systèmes d'astronomie

## Prérequis

- Python 3.12 ou supérieur
- PyQt6
- PySerial

## Installation

1. Cloner le dépôt

```bash
git clone <url-du-repo>
cd AdcAutoClient
```

2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
source venv/bin/activate  # Sur Unix/MacOS
# ou
venv\Scripts\activate  # Sur Windows
```

3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python src/main.py
```

## Structure du projet

```
AdcAutoClient/
├── docs/               # Documentation
├── resources/          # Ressources (images, etc.)
├── src/                # Code source
│   ├── core/           # Logique métier
│   ├── models/         # Modèles de données
│   ├── services/       # Services (communication série, ASCOM Alpaca)
│   ├── ui/             # Interface utilisateur
│   └── utils/          # Utilitaires
├── tests/              # Tests unitaires
├── README.md           # Documentation principale
└── requirements.txt    # Dépendances
```

## Développement

Ce projet est conçu pour fonctionner sur plusieurs plateformes :

- macOS (développement)
- Windows (déploiement principal)
- Linux
- Raspberry Pi

## Licence

[Insérer la licence ici]
