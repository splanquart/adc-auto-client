# Guide d'utilisation d'AdcAutoClient

Ce document explique comment configurer l'environnement de développement, exécuter l'application et créer des exécutables pour différentes plateformes.

## Configuration de l'environnement de développement

### Prérequis

- Python 3.12 ou supérieur
- Poetry (gestionnaire de dépendances)

### Installation de Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### Configuration de Poetry pour le projet

Pour que Poetry crée l'environnement virtuel dans le répertoire du projet (sous `.venv`) :

```bash
# Dans le répertoire du projet
poetry config virtualenvs.in-project true
```

### Installation des dépendances

```bash
# Dans le répertoire du projet
poetry install
```

## Développement

### Activer l'environnement virtuel

```bash
# Méthode 1 : Utiliser Poetry
poetry shell

# Méthode 2 : Activer directement l'environnement
source .venv/bin/activate  # Sur macOS/Linux
# ou
# .venv\Scripts\activate  # Sur Windows
```

### Exécuter l'application

```bash
# Méthode 1 : Utiliser le script défini dans pyproject.toml
poetry run adcautoclient

# Méthode 2 : Exécuter directement le script Python
poetry run python src/main.py
```

### Ajouter des dépendances

```bash
# Ajouter une dépendance d'exécution
poetry add nom-package

# Ajouter une dépendance de développement
poetry add --group dev nom-package
```

### Exécuter les tests

```bash
poetry run pytest
```

### Formater le code

```bash
# Formater avec Black
poetry run black src tests

# Trier les imports avec isort
poetry run isort src tests

# Vérifier avec flake8
poetry run flake8 src tests
```

## Création d'exécutables

### Installation de PyInstaller

```bash
poetry add --group dev pyinstaller
```

### Création d'un exécutable pour Windows (.exe)

```bash
# Sur Windows
poetry run pyinstaller --name AdcAutoClient --windowed --icon=resources/icon.ico src/main.py
```

L'exécutable sera créé dans le dossier `dist/AdcAutoClient/`.

### Création d'une application pour macOS (.app)

```bash
# Sur macOS
poetry run pyinstaller --name AdcAutoClient --windowed --icon=resources/icon.icns src/main.py
```

L'application sera créée dans le dossier `dist/AdcAutoClient.app/`.

Pour créer un fichier DMG distribuable :

```bash
# Installer create-dmg
brew install create-dmg

# Créer le DMG
create-dmg \
  --volname "AdcAutoClient" \
  --volicon "resources/icon.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "AdcAutoClient.app" 175 120 \
  --hide-extension "AdcAutoClient.app" \
  --app-drop-link 425 120 \
  "AdcAutoClient.dmg" \
  "dist/AdcAutoClient.app"
```

### Création d'un exécutable pour Linux

```bash
# Sur Linux
poetry run pyinstaller --name AdcAutoClient --windowed src/main.py
```

Pour créer un AppImage (compatible avec la plupart des distributions Linux) :

```bash
# Installer appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Créer la structure AppDir
mkdir -p AppDir/usr/bin
cp -r dist/AdcAutoClient/* AppDir/usr/bin/

# Créer le fichier .desktop
cat > AppDir/adcautoclient.desktop << EOF
[Desktop Entry]
Name=AdcAutoClient
Exec=AdcAutoClient
Icon=adcautoclient
Type=Application
Categories=Utility;
EOF

# Copier l'icône
cp resources/icon.png AppDir/adcautoclient.png

# Créer l'AppImage
./appimagetool-x86_64.AppImage AppDir AdcAutoClient-x86_64.AppImage
```

### Création d'un package pour Raspberry Pi

Pour Raspberry Pi, vous pouvez utiliser PyInstaller comme pour Linux, ou créer un package Debian :

```bash
# Installer les outils de packaging Debian
sudo apt-get install python3-stdeb dh-python

# Créer le package Debian
poetry build
python3 -m stdeb --command-packages=stdeb.command bdist_deb
```

Le package Debian sera créé dans le dossier `deb_dist/`.

## Conseils pour le déploiement multi-plateforme

1. **Chemins de fichiers** : Utilisez `pathlib.Path` pour gérer les chemins de fichiers de manière compatible avec toutes les plateformes.

2. **Ressources** : Utilisez des chemins relatifs pour accéder aux ressources, ou utilisez `pkg_resources` pour les ressources empaquetées.

3. **Interfaces utilisateur** : PyQt6 s'adapte automatiquement au style de la plateforme, mais vous pouvez personnaliser l'apparence si nécessaire.

4. **Permissions** : Tenez compte des différences de permissions entre les plateformes, notamment pour l'accès aux ports série.

5. **Tests** : Testez votre application sur toutes les plateformes cibles avant la distribution finale.

## Résolution des problèmes courants

### Problèmes de ports série sur macOS

Sur macOS, les ports série peuvent nécessiter des permissions spéciales. Assurez-vous que votre application a accès aux ports série en vérifiant les préférences de sécurité et de confidentialité.

### Problèmes de dépendances avec PyInstaller

Si PyInstaller ne parvient pas à trouver certaines dépendances, vous pouvez les spécifier explicitement :

```bash
poetry run pyinstaller --name AdcAutoClient --windowed --hidden-import=pkg_name src/main.py
```

### Problèmes d'icônes sur Windows

Sur Windows, assurez-vous que votre icône est au format .ico et qu'elle est correctement référencée dans le script PyInstaller.
