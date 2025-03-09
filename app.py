import streamlit as st
import cv2
import mediapipe as mp
import time
import math
import beepy

# Helper: Compute an angle between three points (in degrees).
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

# ---------------------
# Plank Exercise Logic
# ---------------------
def run_plank_exercise(target_time, plank_mode):
    st.write("Assume the plank position. The timer will run when you’re in good posture.")
    
    # Initialize stop flag if needed.
    if "stop_plank" not in st.session_state:
        st.session_state["stop_plank"] = False

    # Create a persistent stop button.
    stop_button_container = st.empty()
    if stop_button_container.button("Stop Plank", key="plank_stop", on_click=lambda: st.session_state.update({"stop_plank": True})):
        pass

    cap = cv2.VideoCapture(0)
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    frame_placeholder = st.empty()

    elapsed = 0.0
    last_time = time.time()

    while cap.isOpened() and not st.session_state["stop_plank"]:
        current_time = time.time()
        delta = current_time - last_time
        last_time = current_time

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        in_good_position = False
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape

            # Use left ear, shoulder, and hip to compute the back angle.
            left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]

            a = (left_ear.x * w, left_ear.y * h)
            b = (left_shoulder.x * w, left_shoulder.y * h)
            c = (left_hip.x * w, left_hip.y * h)
            angle = calculate_angle(a, b, c)

            cv2.putText(frame, f'Angle: {int(angle)}', (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Acceptable range for a straight back (adjust as needed)
            if 160 <= angle <= 200:
                in_good_position = True
            else:
                cv2.putText(frame, "Adjust your position!", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "No landmarks detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Update timer based on mode and posture.
        if in_good_position:
            elapsed += delta
        else:
            if plank_mode == "Hardcore":
                elapsed = 0.0
            # In Normal mode, elapsed stays the same (pausing the countdown)

        remaining = max(target_time - elapsed, 0)
        cv2.putText(frame, f"Time remaining: {int(remaining)} sec", (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        frame_placeholder.image(frame, channels="BGR")

        if remaining <= 0:
            st.success("Plank complete!")
            break

        time.sleep(0.03)

    cap.release()

# -------------------------
# Criss Cross Exercise Logic
# -------------------------
def run_criss_cross_exercise(beep_interval):
    st.write("For the Criss Cross exercise: Spread your legs and bring your hands together above your head in sync with the beeps.")
    
    if "stop_criss_cross" not in st.session_state:
        st.session_state["stop_criss_cross"] = False

    stop_button_container = st.empty()
    if stop_button_container.button("Stop Criss Cross", key="criss_cross_stop", on_click=lambda: st.session_state.update({"stop_criss_cross": True})):
        pass

    cap = cv2.VideoCapture(0)
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    frame_placeholder = st.empty()

    last_beep_time = time.time()

    while cap.isOpened() and not st.session_state["stop_criss_cross"]:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        in_correct_position = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, _ = frame.shape

            # Check hands: wrists together and above shoulders.
            left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            lw = (left_wrist.x * w, left_wrist.y * h)
            rw = (right_wrist.x * w, right_wrist.y * h)
            ls = (left_shoulder.x * w, left_shoulder.y * h)
            rs = (right_shoulder.x * w, right_shoulder.y * h)

            hand_distance = math.hypot(lw[0] - rw[0], lw[1] - rw[1])
            hands_together = (lw[1] < ls[1] and rw[1] < rs[1] and hand_distance < 100)

            # Check legs: ankles should be spread apart.
            left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
            right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
            la = (left_ankle.x * w, left_ankle.y * h)
            ra = (right_ankle.x * w, right_ankle.y * h)
            leg_distance = math.hypot(la[0] - ra[0], la[1] - ra[1])
            legs_spread = (leg_distance >= 150)

            in_correct_position = hands_together and legs_spread

            if not hands_together:
                cv2.putText(frame, "Join your hands above your head", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            if not legs_spread:
                cv2.putText(frame, "Spread your legs", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "No landmarks detected", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Play beep at regular intervals.
        if time.time() - last_beep_time >= beep_interval:
            beepy.beep(sound=1)
            last_beep_time = time.time()

        # Draw a colored border: green if correct, red if not.
        border_color = (0, 255, 0) if in_correct_position else (0, 0, 255)
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, 0), (w, h), border_color, thickness=10)

        status = "Good position" if in_correct_position else "Adjust your form!"
        cv2.putText(frame, status, (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        frame_placeholder.image(frame, channels="BGR")

        time.sleep(0.03)

    cap.release()

# --------------
# Main Streamlit App
# --------------
st.title("AI Powered Sport Coach")

exercise = st.sidebar.radio("Select Exercise", ("Plank", "Criss Cross"))

if exercise == "Plank":
    st.header("Plank Exercise")
    # User inputs for duration and mode.
    target_time = st.number_input("Exercise Duration (sec)", min_value=10, max_value=600, value=60, step=10)
    # Hover over the mode selection to see its explanation.
    plank_mode = st.radio(
        "Select Mode",
        options=["Normal", "Hardcore"],
        help=(
            "Normal Mode: If your position is bad, the timer pauses (time stops decreasing but doesn't reset). "
            "Hardcore Mode: If your position is bad, the timer resets to the beginning."
        )
    )
    if st.button("Start Plank"):
        st.session_state["stop_plank"] = False  # Reset flag before starting.
        run_plank_exercise(target_time, plank_mode)


elif exercise == "Criss Cross":
    st.header("Criss Cross Exercise")
    # Slider to choose beep interval.
    beep_interval = st.slider("Beep Interval (sec)", min_value=1, max_value=10, value=5)
    if st.button("Start Criss Cross"):
        st.session_state["stop_criss_cross"] = False  # Reset flag before starting.
        run_criss_cross_exercise(beep_interval)
