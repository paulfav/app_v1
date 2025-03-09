#!/bin/bash

# Initialiser Conda pour ce script
eval "$(conda shell.bash hook)"

# Déterminer le chemin de l'environnement Conda
if conda env list | grep -q workout-env; then
    echo "Environnement Conda 'workout-env' trouvé."
else
    echo "Environnement Conda 'workout-env' non trouvé. Création de l'environnement..."
    conda create -n workout-env python=3.10 -y
    
    echo "Installation des dépendances..."
    conda activate workout-env
    pip install -r requirements.txt
    echo "Installation terminée."
fi

# Activer l'environnement Conda
conda activate workout-env

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