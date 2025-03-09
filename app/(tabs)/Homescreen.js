import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';

export default function HomeScreen() {
  // State variables
  const [countdown, setCountdown] = useState(null); // countdown timer state
  const [sessionActive, setSessionActive] = useState(false); // session status
  const [feedback, setFeedback] = useState(''); // feedback text

  // Start the countdown when the Start button is pressed
  const startCountdown = () => {
    setCountdown(5); // a 5-second countdown before the session starts
  };

  // Stop the session when the Stop button is pressed
  const stopSession = () => {
    setSessionActive(false);
    setFeedback('Session stopped manually.');
  };

  // Handle countdown logic
  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown(prev => {
          if (prev === 1) {
            clearInterval(timer);
            setSessionActive(true); // Activate the session once countdown reaches 0
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [countdown]);

  // Manage session: Provide real-time feedback and end the session after a set time
  useEffect(() => {
    let sessionTimer;
    if (sessionActive) {
      // Example: update feedback in real-time
      setFeedback('Session is active! Enjoy your workout...');
      // End session after 10 seconds (this duration can be adjusted)
      sessionTimer = setTimeout(() => {
        setSessionActive(false);
        setFeedback('Session ended.');
      }, 10000);
    }
    return () => clearTimeout(sessionTimer);
  }, [sessionActive]);

  return (
    <View style={styles.container}>
      {/* Show the Start button when no countdown is active and session is not active */}
      {!countdown && !sessionActive && (
        <Pressable style={styles.button} onPress={startCountdown}>
          <Text style={styles.buttonText}>Start</Text>
        </Pressable>
      )}

      {/* Show countdown if it's running */}
      {countdown > 0 && (
        <Text style={styles.countdownText}>{countdown}</Text>
      )}

      {/* Show real-time feedback if the session is active */}
      {sessionActive && (
        <View style={styles.sessionContainer}>
          <Text style={styles.feedbackText}>{feedback}</Text>
          
          {/* Stop button */}
          <Pressable style={[styles.button, styles.stopButton]} onPress={stopSession}>
            <Text style={styles.buttonText}>Stop</Text>
          </Pressable>
        </View>
      )}

      {/* Optionally, display final feedback after session ends */}
      {!sessionActive && countdown === 0 && feedback && (
        <Text style={styles.feedbackText}>{feedback}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sessionContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  button: {
    backgroundColor: '#2196F3',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 5,
  },
  stopButton: {
    backgroundColor: '#F44336',
    marginTop: 20,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
  },
  countdownText: {
    fontSize: 48,
    marginBottom: 20,
  },
  feedbackText: {
    fontSize: 24,
    marginTop: 20,
  },
});