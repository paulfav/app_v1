import os
import math
import base64
import numpy as np
import cv2
import mediapipe as mp
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import socket
import traceback
import time
import eventlet

# Patch eventlet for better socket performance
eventlet.monkey_patch()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Print startup message
logger.info("="*50)
logger.info("Starting Workout Analysis Server")
logger.info("="*50)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize MediaPipe Pose
logger.info("Initializing MediaPipe Pose")
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1  # Use a more accurate model
)

# Print local IP for connection
local_ip = socket.gethostbyname(socket.gethostname())
logger.info(f"Server running on http://{local_ip}:5001")

# Helper: Get local IP address
def get_local_ip():
    try:
        # Create a socket connection to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Helper: Compute an angle between three points (in degrees)
def calculate_angle(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    norm_ba = math.hypot(*ba)
    norm_bc = math.hypot(*bc)
    if norm_ba * norm_bc == 0:
        return 0
    cosine_angle = dot / (norm_ba * norm_bc)
    cosine_angle = max(-1, min(1, cosine_angle))
    return math.degrees(math.acos(cosine_angle))

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')
    emit('server_info', {'message': 'Connected to workout analysis server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('frame')
def handle_frame(frame_data):
    logger.debug(f"Received frame from client: {request.sid}")
    start_time = time.time()
    
    # Process the frame
    result = process_frame(frame_data)
    
    # Log processing time and result summary
    processing_time = time.time() - start_time
    logger.info(f"Frame processed in {processing_time:.2f}s: angle={result.get('angle')}, posture_correct={result.get('posture_correct')}, landmarks_count={len(result.get('landmarks', []))}")
    
    # Send result back to client
    emit('pose_analysis', result)

# HTTP routes
@app.route('/')
def index():
    return "Workout Pose Analysis Server"

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.json:
        return jsonify({"error": "No image data provided"}), 400
    
    frame_data = request.json['image']
    result = process_frame(frame_data)
    return jsonify(result)

def process_frame(frame_data):
    response = {
        "posture_correct": False,
        "angle": None,
        "message": "No pose detected",
        "landmarks": []
    }
    
    try:
        logger.debug("Starting to process frame")
        
        # Decode base64 image
        try:
            img_bytes = base64.b64decode(frame_data.split(',')[1])
            img_np = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.error("Failed to decode image")
                return response
                
            logger.debug(f"Image decoded successfully. Shape: {frame.shape}")
        except Exception as e:
            logger.error(f"Error decoding image: {str(e)}")
            logger.error(traceback.format_exc())
            return response
        
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe Pose
        logger.debug("Processing image with MediaPipe")
        results = pose.process(image_rgb)
        
        if not results.pose_landmarks:
            logger.warning("No pose landmarks detected in the frame")
            return response
            
        logger.debug(f"Pose landmarks detected: {len(results.pose_landmarks.landmark)}")
        
        # Get landmarks for posture analysis
        landmarks = results.pose_landmarks.landmark
        
        # Use left ear, shoulder, and hip to compute the back angle
        left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        
        # Convert normalized coordinates to pixel coordinates
        h, w, _ = frame.shape
        a = (left_ear.x * w, left_ear.y * h)
        b = (left_shoulder.x * w, left_shoulder.y * h)
        c = (left_hip.x * w, left_hip.y * h)
        
        # Calculate angle
        angle = calculate_angle(a, b, c)
        logger.debug(f"Calculated angle: {angle}")
        
        # Check if posture is correct (angle between 160 and 200 degrees)
        posture_correct = 160 <= angle <= 200
        
        # Extract all landmarks for visualization
        landmarks_list = []
        for idx, landmark in enumerate(landmarks):
            landmarks_list.append({
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z,
                "visibility": landmark.visibility,
                "name": idx  # Add landmark index/name for debugging
            })
        
        logger.debug(f"Extracted {len(landmarks_list)} landmarks")
        
        response = {
            "posture_correct": posture_correct,
            "angle": int(angle),
            "message": "Good posture!" if posture_correct else "Adjust your position!",
            "landmarks": landmarks_list
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        logger.error(traceback.format_exc())
        return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    
    logger.info(f"Starting server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=True, use_reloader=False) 