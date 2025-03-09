#!/bin/bash

# Afficher un message d'aide
echo "=== Workout App - Démarrage ==="
echo "Ce script va démarrer le serveur Flask et l'application React Native."
echo ""

# Vérifier si le serveur Flask est déjà en cours d'exécution
if lsof -i :5001 > /dev/null 2>&1; then
    echo "Le port 5001 est déjà utilisé. Le serveur Flask est peut-être déjà en cours d'exécution."
    echo "Vérifiez avec la commande: lsof -i :5001"
else
    echo "Démarrage du serveur Flask..."
    
    # Démarrer le serveur Flask en arrière-plan en utilisant l'environnement Conda complet
    (cd server && eval "$(conda shell.bash hook)" && conda activate workout-env && python app.py) &
    
    # Attendre que le serveur démarre
    sleep 3
    echo "Serveur Flask démarré sur http://$(hostname -I | awk '{print $1}'):5001"
    echo ""
fi

# Démarrer l'application React Native
echo "Démarrage de l'application React Native..."
echo "Scannez le QR code avec l'application Expo Go sur votre téléphone."
echo ""

# Démarrer l'application React Native
npx expo start 