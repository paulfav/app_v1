import React, { useState, useEffect, useRef } from 'react';
import { View, Text, Pressable, StyleSheet, Button, Dimensions } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as SocketIO from 'socket.io-client';
import * as ScreenOrientation from 'expo-screen-orientation';

// Configuration du serveur
const SERVER_URL = 'http://192.168.1.160:5001';
const FALLBACK_URL = 'http://127.0.0.1:5001'; // Fallback to localhost if main server is unreachable
console.log(`Primary server URL: ${SERVER_URL}`);
console.log(`Fallback server URL: ${FALLBACK_URL}`);

export default function HomeScreen() {
  // State variables
  const [countdown, setCountdown] = useState(null); // countdown timer state
  const [sessionActive, setSessionActive] = useState(false); // session status
  const [feedback, setFeedback] = useState(''); // feedback text
  const [sessionTime, setSessionTime] = useState(30); // session time in seconds
  const [angle, setAngle] = useState(null); // posture angle
  const [isGoodPosture, setIsGoodPosture] = useState(false); // posture status
  const [landmarks, setLandmarks] = useState(null); // pose landmarks
  const [screenDimensions, setScreenDimensions] = useState(Dimensions.get('window')); // screen dimensions
  
  // Camera permissions
  const [permission, requestPermission] = useCameraPermissions();
  
  // Refs
  const cameraRef = useRef(null);
  const socketRef = useRef(null);
  const frameIntervalRef = useRef(null);

  // Handle screen dimensions changes
  useEffect(() => {
    const subscription = Dimensions.addEventListener('change', ({ window }) => {
      setScreenDimensions(window);
    });
    return () => subscription?.remove();
  }, []);

  // Start the countdown when the Start button is pressed
  const startCountdown = () => {
    setCountdown(5); // a 5-second countdown before the session starts
  };

  // Stop the session when the Stop button is pressed
  const stopSession = async () => {
    setSessionActive(false);
    setFeedback('Session stopped manually.');
    setSessionTime(30); // Reset session time
    setLandmarks(null); // Clear landmarks
    
    // Reset screen orientation to portrait
    await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP);
    
    // Disconnect socket
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    // Clear frame interval
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  };

  // Handle countdown logic
  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown(prev => {
          if (prev === 1) {
            clearInterval(timer);
            startSession(); // Start the session once countdown reaches 0
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [countdown]);

  // Start the session and connect to the server
  const startSession = async () => {
    setSessionActive(true);
    setFeedback('Connecting to server...');
    
    // Lock screen orientation to landscape
    await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.LANDSCAPE_RIGHT);
    
    // Connect to the server with detailed logging
    console.log(`Initializing socket connection to ${SERVER_URL}`);
    
    // Add socket options for better debugging
    const socketOptions = {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 20000,
      forceNew: true
    };
    
    // Try to connect to the primary server
    socketRef.current = SocketIO.io(SERVER_URL, socketOptions);
    
    // Set a timeout to try the fallback URL if primary connection fails
    const connectionTimeout = setTimeout(() => {
      if (!socketRef.current.connected) {
        console.log(`Connection to ${SERVER_URL} failed. Trying fallback URL: ${FALLBACK_URL}`);
        setFeedback('Primary server unreachable, trying fallback...');
        
        // Disconnect from the primary server
        socketRef.current.disconnect();
        
        // Connect to the fallback server
        socketRef.current = SocketIO.io(FALLBACK_URL, socketOptions);
        
        // Set up event handlers for the fallback connection
        setupSocketEventHandlers();
      }
    }, 5000); // Wait 5 seconds before trying fallback
    
    // Set up socket event handlers
    setupSocketEventHandlers();
    
    // Function to set up event handlers
    function setupSocketEventHandlers() {
      socketRef.current.on('connect', () => {
        // Clear the connection timeout if it's still active
        clearTimeout(connectionTimeout);
        
        console.log('Socket connected successfully!');
        setFeedback('Connected! Starting workout analysis...');
        
        // Start sending frames
        startSendingFrames();
      });
      
      socketRef.current.on('disconnect', (reason) => {
        console.log(`Socket disconnected. Reason: ${reason}`);
        setFeedback(`Disconnected from server: ${reason}`);
      });
      
      socketRef.current.on('connect_error', (error) => {
        console.error('Connection error:', error.message);
        setFeedback(`Error connecting to server: ${error.message}`);
      });
      
      socketRef.current.on('error', (error) => {
        console.error('Socket error:', error);
        setFeedback(`Socket error: ${error}`);
      });
      
      socketRef.current.on('reconnect_attempt', (attemptNumber) => {
        console.log(`Attempting to reconnect: attempt ${attemptNumber}`);
        setFeedback(`Reconnecting... (attempt ${attemptNumber})`);
      });
      
      socketRef.current.on('pose_analysis', (data) => {
        console.log('Received pose analysis data:', JSON.stringify(data));
        setAngle(data.angle);
        setIsGoodPosture(data.posture_correct);
        setFeedback(data.message);
        
        // Store landmarks if available
        if (data.landmarks && data.landmarks.length > 0) {
          console.log(`Received ${data.landmarks.length} landmarks from server`);
          console.log(`First landmark: x=${data.landmarks[0].x}, y=${data.landmarks[0].y}, visibility=${data.landmarks[0].visibility}`);
          setLandmarks(data.landmarks);
        } else {
          console.log("No landmarks received from server or empty landmarks array");
          // Clear landmarks to ensure UI updates
          setLandmarks([]);
        }
      });
    }
  };
  
  // Start sending camera frames to the server
  const startSendingFrames = async () => {
    if (!cameraRef.current) return;
    
    // Start session timer (30 seconds)
    const sessionTimer = setInterval(() => {
      setSessionTime(prevTime => {
        if (prevTime <= 1) {
          clearInterval(sessionTimer);
          stopSession();
          setFeedback('Session completed successfully!');
          return 30; // Reset to 30 seconds
        }
        return prevTime - 1;
      });
    }, 1000);
    
    // Send frames every 200ms (5 frames per second)
    frameIntervalRef.current = setInterval(async () => {
      if (cameraRef.current && sessionActive && socketRef.current && socketRef.current.connected) {
        try {
          console.log("Taking picture from camera...");
          const photo = await cameraRef.current.takePictureAsync({
            quality: 0.5,
            base64: true,
            exif: false,
          });
          
          console.log(`Picture taken, base64 length: ${photo.base64.length}`);
          
          // Send the frame to the server
          console.log("Sending frame to server...");
          socketRef.current.emit('frame', `data:image/jpg;base64,${photo.base64}`);
          console.log("Frame sent to server");
        } catch (error) {
          console.error('Error taking picture:', error);
        }
      } else {
        console.log(`Cannot take picture: camera=${!!cameraRef.current}, sessionActive=${sessionActive}, socket=${!!socketRef.current}, connected=${socketRef.current?.connected}`);
      }
    }, 200);
  };

  // Render landmarks on camera view
  const renderLandmarks = () => {
    if (!landmarks || landmarks.length === 0) {
      console.log("No landmarks to render");
      return null;
    }
    
    console.log(`Rendering ${landmarks.length} landmarks`);
    
    // Get the dimensions of the camera container for proper scaling
    const containerWidth = screenDimensions.width * 0.9; // 90% of screen width
    const containerHeight = screenDimensions.height * 0.7; // 70% of screen height
    
    console.log(`Container dimensions: ${containerWidth}x${containerHeight}`);
    
    // Create an array to hold all landmark components
    const landmarkComponents = [];
    
    // Process each landmark
    for (let i = 0; i < landmarks.length; i++) {
      const point = landmarks[i];
      
      // Skip points with low visibility
      if (point.visibility < 0.5) {
        console.log(`Skipping landmark ${i} due to low visibility: ${point.visibility}`);
        continue;
      }
      
      // Scale normalized coordinates to container size
      const x = point.x * containerWidth;
      const y = point.y * containerHeight;
      
      console.log(`Rendering landmark ${i} at position (${x}, ${y})`);
      
      // Add landmark component to array
      landmarkComponents.push(
        <View
          key={i}
          style={{
            position: 'absolute',
            left: x,
            top: y,
            width: 12,
            height: 12,
            borderRadius: 6,
            backgroundColor: isGoodPosture ? '#4CAF50' : '#F44336',
            borderWidth: 2,
            borderColor: '#FFFFFF',
            zIndex: 1000,
          }}
        />
      );
    }
    
    // Return all landmark components
    return landmarkComponents;
  };

  // Render based on camera permission
  if (!permission) {
    return <View style={styles.container}><Text>Requesting camera permission...</Text></View>;
  }
  
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.message}>We need your permission to show the camera</Text>
        <Button onPress={requestPermission} title="Grant Permission" />
      </View>
    );
  }

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

      {/* Show camera and feedback if the session is active */}
      {sessionActive && (
        <View style={styles.sessionContainer}>
          <View style={styles.cameraContainer}>
            <CameraView
              ref={cameraRef}
              style={styles.camera}
              facing="front"
              enableTorch={false}
              active={sessionActive}
              onCameraReady={() => console.log("Camera is ready")}
              onMountError={(error) => console.error("Camera mount error:", error)}
            />
            
            {/* Landmarks overlay - positioned absolutely over the camera */}
            <View style={styles.landmarksContainer}>
              {renderLandmarks()}
            </View>
            
            {/* Timer overlay */}
            <View style={styles.timerOverlay}>
              <Text style={styles.timerText}>{sessionTime}s</Text>
            </View>
            
            {/* Angle indicator */}
            <View style={[
              styles.angleIndicator,
              isGoodPosture ? styles.goodPosture : styles.badPosture
            ]}>
              <Text style={styles.angleText}>{angle || '--'}°</Text>
            </View>
          </View>
          
          <Text style={styles.feedbackText}>{feedback}</Text>
          
          {/* Progress bar */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBackground}>
              <View 
                style={[
                  styles.progressFill, 
                  { width: `${(sessionTime / 30) * 100}%` },
                  isGoodPosture ? styles.goodPostureFill : styles.badPostureFill
                ]} 
              />
            </View>
          </View>
          
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
    backgroundColor: '#f5f5f5',
  },
  sessionContainer: {
    flex: 1,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 20,
  },
  cameraContainer: {
    width: '90%',
    height: '70%',
    borderRadius: 20,
    overflow: 'hidden',
    marginBottom: 10,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  landmarkPoint: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: 'white',
    backgroundColor: 'red',
    zIndex: 1000,
  },
  timerOverlay: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 30,
    zIndex: 10,
  },
  timerText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  angleIndicator: {
    position: 'absolute',
    top: 20,
    left: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  goodPosture: {
    backgroundColor: 'rgba(76, 175, 80, 0.8)', // Green with opacity
  },
  badPosture: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)', // Red with opacity
  },
  angleText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  progressContainer: {
    width: '90%',
    marginBottom: 10,
  },
  progressBackground: {
    height: 10,
    backgroundColor: '#e0e0e0',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 5,
  },
  goodPostureFill: {
    backgroundColor: '#4CAF50', // Green
  },
  badPostureFill: {
    backgroundColor: '#F44336', // Red
  },
  button: {
    backgroundColor: '#2196F3',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 5,
    marginVertical: 10,
  },
  stopButton: {
    backgroundColor: '#F44336',
    marginTop: 10,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  countdownText: {
    fontSize: 80,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  feedbackText: {
    fontSize: 24,
    marginTop: 10,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  message: {
    textAlign: 'center',
    paddingBottom: 10,
    fontSize: 18,
  },
  landmarksContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 10,
  },
}); 