#!/usr/bin/env python3
"""
Bab 18: Test Hand Tracking - Basic
===================================
Program sederhana untuk test MediaPipe hand tracking

Install:
  pip3 install mediapipe opencv-python
"""

import cv2
import mediapipe as mp

print("="*50)
print("Test Hand Tracking - Basic")
print("="*50)

try:
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5
    )
    print("✅ MediaPipe Hands initialized")
except Exception as e:
    print(f"❌ MediaPipe error: {e}")
    print("   Install: pip3 install mediapipe")
    exit(1)

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("❌ Cannot open camera")
    exit(1)

print("✅ Camera opened")
print("\nTracking hands... (Press 'q' to quit)\n")

hand_detected_count = 0

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            hand_detected_count += 1
            
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
            
            cv2.putText(frame, f"Hands: {len(results.multi_hand_landmarks)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No hands detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow('Hand Tracking Test (Press Q)', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"\n✅ Test selesai!")
    print(f"   Frames with hand: {hand_detected_count}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

finally:
    hands.close()
    camera.release()
    cv2.destroyAllWindows()

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test hand tracking menggunakan MediaPipe Hands, library dari Google
untuk real-time hand detection dan landmark tracking.

MediaPipe:
MediaPipe adalah framework dari Google untuk building multimodal ML pipelines. Provides
pre-built solutions untuk:
- Hands (hand tracking)
- Pose (body pose estimation)
- Face Mesh (face landmarks)
- Face Detection
- Holistic (hands + pose + face)
- Selfie Segmentation

MediaPipe Hands:
Detect dan track 21 hand landmarks (key points) untuk each hand dalam real-time.

21 Hand Landmarks:
0: WRIST
1-4: THUMB (CMC, MCP, IP, TIP)
5-8: INDEX_FINGER (MCP, PIP, DIP, TIP)
9-12: MIDDLE_FINGER (MCP, PIP, DIP, TIP)
13-16: RING_FINGER (MCP, PIP, DIP, TIP)
17-20: PINKY (MCP, PIP, DIP, TIP)

Dimana MCP=Metacarpophalangeal, PIP=Proximal Interphalangeal, DIP=Distal Interphalangeal,
IP=Interphalangeal, CMC=Carpometacarpal

Cara Kerja MediaPipe Hands:
1. Palm Detection:
   - Detect palm region menggunakan custom SSD model
   - Return bounding box untuk palm

2. Hand Landmark Model:
   - Crop hand region dari palm detection
   - Predict 21 3D landmarks (x, y, z coordinates)
   - x, y normalized ke [0, 1] relative to image
   - z is depth relative to wrist landmark

3. Hand Tracking:
   - Once detected, use previous frame landmarks untuk predict current frame region
   - More efficient daripada run palm detection setiap frame
   - Re-run palm detection jika tracking lost

Cara Kerja Program:
1. Initialize MediaPipe Hands:
   - static_image_mode=False: video mode (use tracking)
   - max_num_hands=2: detect maksimal 2 hands
   - min_detection_confidence=0.5: threshold untuk palm detection
   - Optional parameters:
     * min_tracking_confidence: threshold untuk tracking (default 0.5)
     * model_complexity: 0 atau 1 (1=more accurate, slower)

2. Process Frame:
   - Convert BGR (OpenCV) ke RGB (MediaPipe expects RGB)
   - hands.process() return results dengan landmarks

3. Results Object:
   - multi_hand_landmarks: list of detected hands
   - multi_handedness: list of handedness (Left/Right)
   - Each hand_landmarks contains 21 landmarks
   - Each landmark has x, y, z coordinates

4. Drawing Landmarks:
   - mp_drawing.draw_landmarks() draw 21 points dan connections
   - HAND_CONNECTIONS: pre-defined connections antara landmarks (garis)
   - Default: green dots untuk landmarks, white lines untuk connections

5. Customization:
   - Bisa customize colors, thickness, circle radius
   - Access individual landmarks: landmark.x, landmark.y, landmark.z
   - Convert normalized coordinates ke pixel: x_pixel = landmark.x * image_width

Gesture Recognition:
Dengan 21 landmarks, bisa recognize gestures seperti:
- Peace sign: index dan middle extended, others folded
- Thumbs up: thumb extended, others folded
- OK sign: thumb dan index form circle
- Fist: all fingers folded
- Open palm: all fingers extended
- Counting: 1, 2, 3, 4, 5 fingers

Implementation Methods:
1. Heuristic Rules:
   - Check jika finger tip above/below PIP joint (extended/folded)
   - Calculate angles antara joints
   - Distance antara fingertips

2. Machine Learning:
   - Extract features dari landmarks (angles, distances)
   - Train classifier (SVM, Random Forest, Neural Network)
   - More robust untuk complex gestures

Applications:
- Touchless interfaces (control without touching screen)
- Sign language recognition
- Virtual reality hand tracking
- Robot control via gestures
- Gaming (hand gestures sebagai controller)
- Medical applications (rehabilitation tracking)
- Augmented reality (virtual object manipulation)

Performance:
- MediaPipe very efficient (optimized dengan TensorFlow Lite)
- Raspberry Pi 4: ~10-20 FPS (depends on resolution)
- Reduce resolution untuk higher FPS
- Use model_complexity=0 untuk faster inference

Landmark Accuracy:
- x, y: sangat accurate (sub-pixel precision)
- z: less accurate (relative depth, bukan absolute distance)
- Occlusions: landmarks di-infer bahkan jika partially hidden

Limitations:
1. Lighting: needs good lighting (struggles di low light)
2. Background: busy backgrounds bisa cause false detections
3. Distance: works best 0.5-2 meters dari camera
4. Orientation: best dengan palm facing camera
5. Speed: very fast movements bisa lose tracking

Tips untuk Better Performance:
- Good lighting (natural atau bright artificial)
- Plain background
- Camera resolution 640x480 atau 320x240 untuk balance speed/accuracy
- Keep hands in frame dan clear visibility
- Avoid motion blur (use good quality camera)
"""
