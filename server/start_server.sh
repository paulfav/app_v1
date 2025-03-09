#!/bin/bash

# Déterminer le chemin de l'environnement Conda
if [ -f ~/miniforge3/bin/activate ]; then
    CONDA_PATH=~/miniforge3/bin/activate
elif [ -f ~/miniconda3/bin/activate ]; then
    CONDA_PATH=~/miniconda3/bin/activate
elif [ -f ~/anaconda3/bin/activate ]; then
    CONDA_PATH=~/anaconda3/bin/activate
else
    echo "Conda non trouvé. Veuillez installer Conda ou modifier ce script."
    exit 1
fi

# Activer l'environnement Conda
source $CONDA_PATH workout-env

# Obtenir l'adresse IP locale
IP_ADDRESS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
if [ -z "$IP_ADDRESS" ]; then
    IP_ADDRESS="127.0.0.1"
fi

# Définir le port
PORT=5001

echo "Démarrage du serveur sur $IP_ADDRESS:$PORT"
echo "Utilisez cette adresse dans votre application mobile: http://$IP_ADDRESS:$PORT"

# Définir la variable d'environnement pour l'adresse IP et le port
export FLASK_RUN_HOST=$IP_ADDRESS
export PORT=$PORT

# Démarrer le serveur Flask
python app.py 