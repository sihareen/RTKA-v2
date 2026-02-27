#!/usr/bin/env python3
"""
Bab 18.1: Hand Tracking & Gesture Recognition dengan MediaPipe
===============================================================
Deteksi tangan dan gesture recognition menggunakan MediaPipe
Dapat mendeteksi hingga 21 landmark pada tangan

Hardware:
- Raspberry Pi 4/5 (4GB+ RAM)
- Pi Camera v2/v3 atau USB Webcam

Install:
  pip3 install opencv-python mediapipe numpy

MediaPipe menyediakan pre-trained model untuk hand tracking
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
from datetime import datetime

print("="*70)
print("Hand Tracking & Gesture Recognition - MediaPipe")
print("="*70)

# ============================================================================
# MEDIAPIPE SETUP
# ============================================================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# ============================================================================
# HAND TRACKER CLASS
# ============================================================================

class HandTracker:
    """MediaPipe hand tracking and gesture recognition"""
    
    def __init__(self, max_num_hands=2, min_detection_confidence=0.7, 
                 min_tracking_confidence=0.5):
        """Initialize hand tracker"""
        
        print("\n🔧 Initializing MediaPipe Hand Tracker...")
        
        self.hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        print(f"   • Max hands: {max_num_hands}")
        print(f"   • Detection confidence: {min_detection_confidence}")
        print(f"   • Tracking confidence: {min_tracking_confidence}")
        print("✅ Hand tracker ready")
        
        # Landmark names
        self.landmark_names = [
            'WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP',
            'INDEX_FINGER_MCP', 'INDEX_FINGER_PIP', 'INDEX_FINGER_DIP', 'INDEX_FINGER_TIP',
            'MIDDLE_FINGER_MCP', 'MIDDLE_FINGER_PIP', 'MIDDLE_FINGER_DIP', 'MIDDLE_FINGER_TIP',
            'RING_FINGER_MCP', 'RING_FINGER_PIP', 'RING_FINGER_DIP', 'RING_FINGER_TIP',
            'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP'
        ]
    
    def process(self, frame):
        """Process frame and detect hands"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        hands_data = []
        
        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Get handedness (Left/Right)
                handedness = results.multi_handedness[hand_idx].classification[0].label
                
                # Extract landmarks
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append({
                        'x': lm.x,
                        'y': lm.y,
                        'z': lm.z
                    })
                
                hands_data.append({
                    'handedness': handedness,
                    'landmarks': landmarks,
                    'raw_landmarks': hand_landmarks
                })
        
        return hands_data
    
    def draw_landmarks(self, frame, hands_data):
        """Draw hand landmarks on frame"""
        output = frame.copy()
        
        for hand in hands_data:
            mp_drawing.draw_landmarks(
                output,
                hand['raw_landmarks'],
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # Draw handedness label
            wrist = hand['landmarks'][0]
            h, w = frame.shape[:2]
            x, y = int(wrist['x'] * w), int(wrist['y'] * h)
            
            label = hand['handedness']
            cv2.putText(output, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return output
    
    def close(self):
        """Release resources"""
        self.hands.close()

# ============================================================================
# GESTURE RECOGNITION
# ============================================================================

class GestureRecognizer:
    """Recognize hand gestures from landmarks"""
    
    def __init__(self):
        print("\n🔧 Initializing Gesture Recognizer...")
        print("✅ Recognizer ready")
    
    def get_finger_state(self, landmarks):
        """Get state of each finger (extended or not)"""
        # Finger tip and pip indices
        fingers = {
            'thumb': (4, 3),      # Thumb tip, thumb IP
            'index': (8, 6),      # Index tip, index PIP
            'middle': (12, 10),   # Middle tip, middle PIP
            'ring': (16, 14),     # Ring tip, ring PIP
            'pinky': (20, 18)     # Pinky tip, pinky PIP
        }
        
        finger_states = {}
        
        for name, (tip_idx, pip_idx) in fingers.items():
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            
            # For thumb, check x-coordinate (different orientation)
            if name == 'thumb':
                # Thumb is extended if tip is farther from wrist than pip
                wrist = landmarks[0]
                dist_tip = abs(tip['x'] - wrist['x'])
                dist_pip = abs(pip['x'] - wrist['x'])
                finger_states[name] = dist_tip > dist_pip
            else:
                # Other fingers: extended if tip y < pip y (tip is higher)
                finger_states[name] = tip['y'] < pip['y']
        
        return finger_states
    
    def count_extended_fingers(self, finger_states):
        """Count how many fingers are extended"""
        return sum(1 for extended in finger_states.values() if extended)
    
    def recognize_gesture(self, landmarks):
        """Recognize gesture from hand landmarks"""
        finger_states = self.get_finger_state(landmarks)
        extended_count = self.count_extended_fingers(finger_states)
        
        # Gesture patterns
        thumb = finger_states['thumb']
        index = finger_states['index']
        middle = finger_states['middle']
        ring = finger_states['ring']
        pinky = finger_states['pinky']
        
        # Number gestures (0-5)
        if extended_count == 0:
            return "FIST", "✊"
        
        elif extended_count == 1:
            if thumb:
                return "THUMBS_UP", "👍"
            elif index:
                return "POINTING", "☝️"
            elif pinky:
                return "PINKY", "🤙"
        
        elif extended_count == 2:
            if index and middle and not thumb:
                return "PEACE / VICTORY", "✌️"
            elif thumb and index and not middle:
                return "GUN", "🔫"
            elif thumb and pinky:
                return "CALL_ME", "🤙"
        
        elif extended_count == 3:
            if thumb and index and middle:
                return "THREE", "3️⃣"
        
        elif extended_count == 4:
            if not thumb:
                return "FOUR", "4️⃣"
        
        elif extended_count == 5:
            return "OPEN_PALM / FIVE", "✋"
        
        return f"UNKNOWN ({extended_count} fingers)", "❓"
    
    def get_pinch_state(self, landmarks):
        """Check if thumb and index are pinching"""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Calculate distance
        distance = math.sqrt(
            (thumb_tip['x'] - index_tip['x'])**2 +
            (thumb_tip['y'] - index_tip['y'])**2
        )
        
        # Pinching if distance is small
        is_pinching = distance < 0.05
        
        return is_pinching, distance

# ============================================================================
# DEMOS
# ============================================================================

def demo_hand_tracking(camera, tracker):
    """Basic hand tracking demo"""
    print("\n👋 Hand Tracking Demo")
    print("   Press 'q' to quit")
    
    fps_start = time.time()
    fps_counter = 0
    fps = 0
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Detect hands
        hands_data = tracker.process(frame)
        
        # Draw landmarks
        output = tracker.draw_landmarks(frame, hands_data)
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 30:
            fps = fps_counter / (time.time() - fps_start)
            fps_start = time.time()
            fps_counter = 0
        
        # Info overlay
        cv2.putText(output, f"FPS: {fps:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(output, f"Hands: {len(hands_data)}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Hand Tracking (Press Q)', output)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

def demo_gesture_recognition(camera, tracker, recognizer):
    """Gesture recognition demo"""
    print("\n🤟 Gesture Recognition Demo")
    print("   Try: Fist, Thumbs Up, Peace, Open Palm, etc.")
    print("   Press 'q' to quit")
    
    fps_start = time.time()
    fps_counter = 0
    fps = 0
    
    gesture_history = []
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Detect hands
        hands_data = tracker.process(frame)
        
        # Draw landmarks
        output = tracker.draw_landmarks(frame, hands_data)
        
        # Recognize gestures
        gestures = []
        for hand in hands_data:
            gesture_name, gesture_emoji = recognizer.recognize_gesture(hand['landmarks'])
            gestures.append({
                'hand': hand['handedness'],
                'gesture': gesture_name,
                'emoji': gesture_emoji
            })
            gesture_history.append(gesture_name)
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 30:
            fps = fps_counter / (time.time() - fps_start)
            fps_start = time.time()
            fps_counter = 0
        
        # Display info
        y_offset = 30
        cv2.putText(output, f"FPS: {fps:.1f}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        y_offset += 40
        for gesture_info in gestures:
            text = f"{gesture_info['hand']}: {gesture_info['gesture']} {gesture_info['emoji']}"
            cv2.putText(output, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            y_offset += 35
        
        cv2.imshow('Gesture Recognition (Press Q)', output)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    
    # Statistics
    if gesture_history:
        print("\n📊 Gesture Statistics:")
        from collections import Counter
        counts = Counter(gesture_history)
        for gesture, count in counts.most_common(5):
            print(f"   {gesture}: {count} times")

def demo_pinch_control(camera, tracker, recognizer):
    """Pinch gesture control demo"""
    print("\n🤏 Pinch Control Demo")
    print("   Pinch thumb and index finger together")
    print("   Press 'q' to quit")
    
    pinch_active = False
    pinch_start_pos = None
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        h, w = frame.shape[:2]
        
        # Detect hands
        hands_data = tracker.process(frame)
        
        output = frame.copy()
        
        for hand in hands_data:
            # Draw landmarks
            mp_drawing.draw_landmarks(
                output, hand['raw_landmarks'], mp_hands.HAND_CONNECTIONS
            )
            
            # Check pinch
            is_pinching, distance = recognizer.get_pinch_state(hand['landmarks'])
            
            # Get index finger tip position
            index_tip = hand['landmarks'][8]
            x, y = int(index_tip['x'] * w), int(index_tip['y'] * h)
            
            if is_pinching:
                cv2.circle(output, (x, y), 20, (0, 0, 255), -1)
                cv2.putText(output, "PINCHING!", (x + 30, y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                if not pinch_active:
                    pinch_start_pos = (x, y)
                    pinch_active = True
                
                # Draw line from start to current
                if pinch_start_pos:
                    cv2.line(output, pinch_start_pos, (x, y), (255, 0, 0), 3)
            else:
                cv2.circle(output, (x, y), 10, (0, 255, 0), 2)
                pinch_active = False
                pinch_start_pos = None
            
            # Show distance
            cv2.putText(output, f"Distance: {distance:.3f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow('Pinch Control (Press Q)', output)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 Hand Tracking & Gesture Recognition")
    print("   Using MediaPipe Hands solution")
    
    camera = None
    tracker = None
    recognizer = None
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Initialize Hand Tracker")
        print("  2. Initialize Gesture Recognizer")
        print("  3. Open Camera")
        print("  4. Demo: Hand Tracking")
        print("  5. Demo: Gesture Recognition")
        print("  6. Demo: Pinch Control")
        print("  7. Show Landmark Map")
        print("  8. Release Resources")
        print("  9. Exit")
        print("="*70)
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            max_hands = input("Max hands to detect (1-2) [2]: ").strip()
            max_hands = int(max_hands) if max_hands.isdigit() else 2
            
            tracker = HandTracker(max_num_hands=max_hands)
        
        elif choice == "2":
            recognizer = GestureRecognizer()
        
        elif choice == "3":
            cam_id = input("Camera ID [0]: ").strip()
            cam_id = int(cam_id) if cam_id.isdigit() else 0
            
            camera = cv2.VideoCapture(cam_id)
            if camera.isOpened():
                print(f"✅ Camera {cam_id} opened")
            else:
                print("❌ Cannot open camera")
                camera = None
        
        elif choice == "4":
            if not tracker or not camera:
                print("❌ Initialize tracker and camera first!")
                continue
            demo_hand_tracking(camera, tracker)
        
        elif choice == "5":
            if not tracker or not camera or not recognizer:
                print("❌ Initialize all components first!")
                continue
            demo_gesture_recognition(camera, tracker, recognizer)
        
        elif choice == "6":
            if not tracker or not camera or not recognizer:
                print("❌ Initialize all components first!")
                continue
            demo_pinch_control(camera, tracker, recognizer)
        
        elif choice == "7":
            if tracker:
                print("\n🗺️  Hand Landmark Map (21 points):")
                for i, name in enumerate(tracker.landmark_names):
                    print(f"   {i:2d}. {name}")
        
        elif choice == "8":
            if camera:
                camera.release()
                camera = None
            if tracker:
                tracker.close()
                tracker = None
            recognizer = None
            print("📷 Resources released")
        
        elif choice == "9":
            if camera:
                camera.release()
            if tracker:
                tracker.close()
            break
    
    print("\n✅ Program finished!")
    print("\n🎓 What you learned:")
    print("  • MediaPipe hand tracking")
    print("  • 21-point hand landmarks")
    print("  • Gesture recognition algorithms")
    print("  • Finger state detection")
    print("  • Pinch gesture detection")
    print("\n📖 Next: Bab 18.2 - Robot Control with Gestures")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated")
        cv2.destroyAllWindows()
