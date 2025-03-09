# Workout App - Timer with Camera

Une application simple pour chronométrer vos séances d'entraînement avec un compte à rebours, une caméra frontale et un bouton d'arrêt.

## Fonctionnalités

- Compte à rebours de 5 secondes avant le début de la séance
- Caméra frontale activée pendant la séance
- Minuteur pour suivre la durée de votre exercice
- Bouton d'arrêt pour terminer manuellement la séance

## Prérequis

- Node.js et npm
- Expo CLI
- Un smartphone avec l'application Expo Go installée

## Installation

### 1. Cloner le dépôt

```bash
git clone <url-du-repo>
cd Workout
```

### 2. Installer les dépendances

```bash
npm install
```

## Utilisation

Démarrer l'application Expo :

```bash
npx expo start
```

Scannez le QR code avec l'application Expo Go sur votre téléphone.

## Utilisation de l'application

1. Accordez les permissions d'accès à la caméra lorsque demandé
2. Appuyez sur le bouton "Start" pour commencer
3. Un compte à rebours de 5 secondes s'affichera
4. Après le compte à rebours, la caméra s'activera et la séance d'entraînement commence
5. L'application affichera un message indiquant que la séance est active
6. Vous pouvez arrêter la séance à tout moment en appuyant sur le bouton "Stop"
7. La séance se termine automatiquement après 10 secondes

## Personnalisation

Pour modifier la durée de la séance, modifiez la valeur dans le fichier `app/index.js` :

```javascript
// Changer 10000 (10 secondes) par la durée souhaitée en millisecondes
sessionTimer = setTimeout(() => {
  setSessionActive(false);
  setFeedback('Session ended.');
}, 10000);
```
