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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

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

# Process frame and analyze pose
def process_frame(frame_data):
    try:
        # Decode base64 image
        img_bytes = base64.b64decode(frame_data.split(',')[1])
        img_np = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        
        # Convert to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image with MediaPipe Pose
        results = pose.process(image_rgb)
        
        # Initialize response
        response = {
            "posture_correct": False,
            "angle": None,
            "message": "No pose detected"
        }
        
        if results.pose_landmarks:
            h, w, _ = frame.shape
            
            # Get landmarks for posture analysis
            landmarks = results.pose_landmarks.landmark
            
            # Use left ear, shoulder, and hip to compute the back angle
            left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            
            # Convert normalized coordinates to pixel coordinates
            a = (left_ear.x * w, left_ear.y * h)
            b = (left_shoulder.x * w, left_shoulder.y * h)
            c = (left_hip.x * w, left_hip.y * h)
            
            # Calculate angle
            angle = calculate_angle(a, b, c)
            
            # Check if posture is correct (angle between 160 and 200 degrees)
            posture_correct = 160 <= angle <= 200
            
            response = {
                "posture_correct": posture_correct,
                "angle": int(angle),
                "message": "Good posture!" if posture_correct else "Adjust your position!"
            }
            
        return response
        
    except Exception as e:
        logger.error(f"Error processing frame: {str(e)}")
        return {"error": str(e)}

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('frame')
def handle_frame(frame_data):
    result = process_frame(frame_data)
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    local_ip = get_local_ip()
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Server accessible at: http://{local_ip}:{port}")
    logger.info(f"Use this URL in your mobile app: http://{local_ip}:{port}")
    
    socketio.run(app, host=host, port=port, debug=True) 