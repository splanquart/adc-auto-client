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
| `STATUS` | `STATUS` | Affiche l'état complet du système | `{"source":"system","type":"data","command":"status","ready":1,"adc":{"level":0,"strength":0,"angles":{"angle1":90,"angle2":90}},"mpu6050":{"initialized":true,"pitch":-2.49,"roll":-49.16,"level":-2},"angles":{"angle1":90,"angle2":90}}` |
| `MPU` | `MPU` | Affiche l'état actuel du module MPU-6050 | `{"source":"system","type":"data","command":"mpu","mpu6050":{"initialized":true,"pitch":7.15,"roll":2.86,"level":7}}` |
| `MPU=init` | `MPU=init` | Initialise le module MPU-6050 | `{"source":"system","type":"data","command":"mpu","mpu6050":{"initialized":true,"action":"init"},"status":"ok"}` |
| `MPU=calibrate` | `MPU=calibrate` | Calibre le module MPU-6050 | `{"source":"system","type":"data","command":"mpu","mpu6050":{"initialized":true,"action":"calibrate"},"status":"ok"}` |
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
- L'état du premier servo (`adc`)
- L'état du module MPU-6050 (`mpu6050`)
- L'état des angles (`angles`)

#### Format de réponse STATUS

```json
{
  "source": "system",
  "type": "data",
  "command": "status",
  "ready": 1,
  "adc": {
    "level": 0,
    "strength": 0,
    "angles": {
      "angle1": 90,
      "angle2": 90
    }
  },
  "mpu6050": {
    "initialized": true,
    "pitch": -2.49,
    "roll": -49.16,
    "level": -2
  },
  "angles": {
    "angle1": 90,
    "angle2": 90
  }
}
```

- **ready** : Indique si le système est prêt
- **adc** : État du premier servo
- **mpu6050** : État du module MPU-6050
- **angles** : État des angles

### MPU

Les commandes `MPU` permettent d'interagir avec le capteur MPU-6050 (accéléromètre et gyroscope).

- **MPU** : Affiche l'état actuel du module MPU-6050, y compris les angles d'inclinaison (pitch, roll) et le niveau calculé
- **MPU=init** : Initialise le module MPU-6050
- **MPU=calibrate** : Calibre le module MPU-6050 pour corriger les offsets

#### Format de réponse MPU

```json
{
  "source": "system",
  "type": "data",
  "command": "mpu",
  "mpu6050": {
    "initialized": true,
    "pitch": 7.15,
    "roll": 2.86,
    "level": 7
  }
}
```

- **initialized** : Indique si le module est initialisé
- **pitch** : Angle d'inclinaison avant/arrière en degrés
- **roll** : Angle d'inclinaison gauche/droite en degrés
- **level** : Niveau calculé (arrondi à l'entier le plus proche) utilisé pour l'ADC

## Intégration dans l'application

L'application AdcAutoClient intègre toutes ces commandes via une interface graphique permettant de :

- Contrôler manuellement le niveau et la force
- Visualiser l'état des servos avec des indicateurs graphiques
- Afficher un indicateur d'horizon artificiel pour le niveau
- Initialiser et calibrer le capteur MPU-6050
- Utiliser les données du MPU pour mettre à jour automatiquement le niveau
