# Documentation des commandes du microcontrôleur

Ce document décrit les commandes disponibles pour communiquer avec le microcontrôleur via l'interface série.

## Commandes disponibles

| Commande | Format | Description | Exemple de réponse |
|----------|--------|-------------|-------------------|
| `LEVEL` | `LEVEL` | Affiche le niveau actuel | `{"source":"system","type":"data","command":"level","level":0,"adc":{"level":0,"strength":50,"angles":{"angle1":45,"angle2":135}}}` |
| `LEVEL=n` | `LEVEL=-45..45` | Définit le niveau entre -45° et +45° | `{"source":"system","type":"data","command":"level","level":-30,"adc":{"level":-30,"strength":50,"angles":{"angle1":30,"angle2":120}}}` |
| `STRENGTH` | `STRENGTH` | Affiche la force actuelle | `{"source":"system","type":"data","command":"strength","strength":50,"adc":{"level":0,"strength":50,"angles":{"angle1":45,"angle2":135}}}` |
| `STRENGTH=n` | `STRENGTH=0..100` | Définit la force entre 0 et 100% | `{"source":"system","type":"data","command":"strength","strength":75,"adc":{"level":0,"strength":75,"angles":{"angle1":33,"angle2":147}}}` |
| `RESET` | `RESET` | Réinitialise la position | `{"source":"system","type":"data","command":"reset","status":"ok","adc":{"level":0,"strength":50,"angles":{"angle1":45,"angle2":135}},"angles":{"angle1":45,"angle2":135}}` |
| `STATUS` | `STATUS` | Affiche l'état complet du système | `{"source":"system","type":"data","command":"status","ready":true,"servo1":{...},"servo2":{...},"adcManager":{...}}` |
| `DEBUG` | `DEBUG` | Affiche l'état du debug | `{"source":"system","type":"data","command":"debug","debug":{"adc":false,"servo1":false,"servo2":false}}` |
| `DEBUG=on/off` | `DEBUG=on` | Active/désactive le debug global | - |
| `DEBUG.ADC=on/off` | `DEBUG.ADC=on` | Active/désactive le debug de l'ADC | - |
| `DEBUG.SERVO1=on/off` | `DEBUG.SERVO1=on` | Active/désactive le debug du servo 1 | - |
| `DEBUG.SERVO2=on/off` | `DEBUG.SERVO2=on` | Active/désactive le debug du servo 2 | - |
| `LOG_LEVEL` | `LOG_LEVEL` | Affiche le niveau de log actuel | `{"source":"system","type":"data","command":"log_level","log_level":"info"}` |
| `LOG_LEVEL=level` | `LOG_LEVEL=verbose` | Définit le niveau de log (verbose, debug, info, warning, error, off) | - |
| `TEST` | `TEST` | Lance la séquence de test | - |
| `HELP` | `HELP` | Affiche l'aide | - |

## Détails des commandes principales

### LEVEL

La commande `LEVEL` permet de contrôler l'angle du premier servo.

- **Plage de valeurs** : -45° à +45°
- **Format de commande** : `LEVEL=n` où n est un entier entre -45 et 45
- **Exemple** : `LEVEL=30` pour définir le niveau à 30 degrés

### STRENGTH

La commande `STRENGTH` permet de contrôler la force appliquée par le second servo.

- **Plage de valeurs** : 0 à 100%
- **Format de commande** : `STRENGTH=n` où n est un entier entre 0 et 100
- **Exemple** : `STRENGTH=75` pour définir la force à 75%

### STATUS

La commande `STATUS` renvoie l'état complet du système sous forme d'un objet JSON contenant :

- L'état de préparation du système (`ready`)
- L'état du premier servo (`servo1`)
- L'état du second servo (`servo2`)
- L'état du gestionnaire ADC (`adcManager`)

### RESET

La commande `RESET` réinitialise la position des servos à leurs valeurs par défaut.

## Intégration dans l'application

Dans l'application AdcAutoClient, les commandes sont envoyées au microcontrôleur via le port série. L'interface utilisateur permet de :

1. Contrôler le niveau (-45° à +45°) via le slider "Level"
2. Contrôler la force (0 à 100%) via le slider "Strength"
3. Envoyer des commandes personnalisées via le champ de commande

Les réponses du microcontrôleur sont affichées dans la barre de statut et enregistrées dans les logs de l'application.
