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

## Outil CLI de test (`adc_cli.py`)

Client série minimal pour valider la connexion, le niveau et la force sans l'interface graphique.
Dépendance : `pyserial` uniquement (déjà dans `requirements.txt`).

```bash
python3 adc_cli.py status              # état complet (ready, level, strength, angles)
python3 adc_cli.py level 30            # régler le niveau (-45..45)
python3 adc_cli.py strength 75         # régler la force (0..100)
python3 adc_cli.py reset               # retour à level=0, strength=0
python3 adc_cli.py sweep               # rampe de validation matérielle
python3 adc_cli.py                     # mode interactif (REPL)
python3 adc_cli.py --port /dev/ttyACM0 status   # forcer le port
```

- Le port série est auto-détecté (USB série).
- **Baudrate : 115200** (vitesse du firmware, `Serial.begin(115200)`).
- Les messages texte brut du firmware (boot, HELP) et les logs JSON sont ignorés
  ou affichés, seules les réponses `data`/`error` sont traitées.

## Simulateur de firmware (`tools/fw_sim.py`)

Émule les réponses série du microcontrôleur (pty) pour développer/tester le client
**sans le C3**. Standard library uniquement, aucune dépendance.

```bash
python3 tools/fw_sim.py          # crée un pseudo-port /dev/pts/N (affiché en sortie)
python3 adc_cli.py --port /dev/pts/N sweep
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
