import cv2
import mediapipe as mp

# Initialize MediaPipe Pose.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to RGB.
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        h, w, _ = frame.shape

        # Define the landmark indices to display.
        indices = [
            mp_pose.PoseLandmark.LEFT_SHOULDER.value,
            mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
            mp_pose.PoseLandmark.LEFT_HIP.value,
            mp_pose.PoseLandmark.RIGHT_HIP.value,
            mp_pose.PoseLandmark.LEFT_EAR.value,
            mp_pose.PoseLandmark.RIGHT_EAR.value,
            mp_pose.PoseLandmark.LEFT_KNEE.value,
            mp_pose.PoseLandmark.RIGHT_KNEE.value,
            mp_pose.PoseLandmark.LEFT_WRIST.value,
            mp_pose.PoseLandmark.RIGHT_WRIST.value,
            mp_pose.PoseLandmark.LEFT_ELBOW.value,
            mp_pose.PoseLandmark.RIGHT_ELBOW.value,
            mp_pose.PoseLandmark.LEFT_ANKLE.value,
            mp_pose.PoseLandmark.RIGHT_ANKLE.value
        ]

        # Draw a circle for each selected landmark.
        for idx in indices:
            landmark = landmarks[idx]
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), radius=5, color=(0, 255, 0), thickness=-1)

        # Define pairs for drawing lines.
        pairs = [
            # Left arm: wrist -> elbow -> shoulder
            (mp_pose.PoseLandmark.LEFT_WRIST.value, mp_pose.PoseLandmark.LEFT_ELBOW.value),
            (mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_SHOULDER.value),
            
            # Right arm: wrist -> elbow -> shoulder
            (mp_pose.PoseLandmark.RIGHT_WRIST.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value),
            (mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value),
            
            # Left body: ear -> shoulder -> hip -> knee -> ankle
            (mp_pose.PoseLandmark.LEFT_EAR.value, mp_pose.PoseLandmark.LEFT_SHOULDER.value),
            (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_HIP.value),
            (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value),
            (mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value),
            
            # Right body: ear -> shoulder -> hip -> knee -> ankle
            (mp_pose.PoseLandmark.RIGHT_EAR.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value),
            (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_HIP.value),
            (mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value),
            (mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value)
        ]
        
        # Draw lines connecting the selected landmark pairs.
        for start_idx, end_idx in pairs:
            start_landmark = landmarks[start_idx]
            end_landmark = landmarks[end_idx]
            x1, y1 = int(start_landmark.x * w), int(start_landmark.y * h)
            x2, y2 = int(end_landmark.x * w), int(end_landmark.y * h)
            cv2.line(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)
    
    cv2.imshow("Pose Estimation", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
