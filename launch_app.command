#!/bin/bash

# Chemin vers le répertoire du projet
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_DIR"

# Vérifier si Poetry est installé
if ! command -v poetry &> /dev/null; then
    echo "Poetry n'est pas installé. Installation..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Lancer l'application
echo "Lancement d'AdcAutoClient..."
poetry run adcautoclient
