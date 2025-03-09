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
mp_drawing = mp.solutions.drawing_utils  # For debugging visualization

# Create pose instance with more permissive settings
pose = mp_pose.Pose(
    static_image_mode=False,  # Set to False for video processing
    model_complexity=1,       # Use a more accurate model (0, 1, or 2)
    smooth_landmarks=True,    # Enable landmark smoothing
    enable_segmentation=False,
    min_detection_confidence=0.3,  # Lower threshold to detect more poses
    min_tracking_confidence=0.3    # Lower threshold for tracking
)

# Test MediaPipe with a simple image to verify it works
def test_mediapipe():
    try:
        # Create a simple test image (just a black image with a white rectangle)
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(test_img, (100, 100), (300, 400), (255, 255, 255), -1)
        
        # Process with MediaPipe
        results = pose.process(test_img)
        
        if results.pose_landmarks:
            logger.info("MediaPipe test successful: landmarks detected in test image")
        else:
            logger.warning("MediaPipe test: No landmarks detected in test image")
            
    except Exception as e:
        logger.error(f"MediaPipe test failed: {str(e)}")
        logger.error(traceback.format_exc())

# Run the test
test_mediapipe()

# Helper: Get local IP address without using DNS resolution
def get_local_ip():
    try:
        # Create a socket connection to an external server
        # This doesn't actually establish a connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except Exception:
        logger.error("Failed to get local IP address")
        return '127.0.0.1'

# Get and log the local IP
local_ip = get_local_ip()
logger.info(f"Server running on http://{local_ip}:5001")

# Helper: Calculate angle between three points
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
    logger.debug(f"Frame data length: {len(frame_data)}")
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
        
        # Check if frame_data is valid
        if not frame_data or not isinstance(frame_data, str) or not frame_data.startswith('data:image'):
            logger.error(f"Invalid frame data format: {type(frame_data)}")
            return response
            
        # Decode base64 image
        try:
            logger.debug("Decoding base64 image")
            img_bytes = base64.b64decode(frame_data.split(',')[1])
            img_np = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.error("Failed to decode image")
                return response
                
            logger.debug(f"Image decoded successfully. Shape: {frame.shape}")
            
            # Save the original frame for debugging
            debug_dir = "debug_frames"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = int(time.time() * 1000)
            cv2.imwrite(f"{debug_dir}/original_{timestamp}.jpg", frame)
            logger.debug(f"Saved original frame to {debug_dir}/original_{timestamp}.jpg")
            
        except Exception as e:
            logger.error(f"Error decoding image: {str(e)}")
            logger.error(traceback.format_exc())
            return response
        
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe Pose
        logger.debug("Processing image with MediaPipe")
        results = pose.process(image_rgb)
        
        # Save the processed frame with landmarks for debugging
        debug_frame = frame.copy()
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                debug_frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )
            cv2.imwrite(f"{debug_dir}/landmarks_{timestamp}.jpg", debug_frame)
            logger.debug(f"Saved frame with landmarks to {debug_dir}/landmarks_{timestamp}.jpg")
        else:
            cv2.imwrite(f"{debug_dir}/no_landmarks_{timestamp}.jpg", debug_frame)
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
    
    # Get the local IP address for client connections
    local_ip = get_local_ip()
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Server accessible at: http://{local_ip}:{port}")
    logger.info(f"Use this URL in your mobile app: http://{local_ip}:{port}")
    
    # Run the server
    try:
        socketio.run(app, host=host, port=port, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        logger.error(traceback.format_exc()) 