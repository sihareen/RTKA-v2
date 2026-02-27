#!/usr/bin/env python3
"""
Bab 16: Test Face Detection - Basic
====================================
Program sederhana untuk test face detection dengan Haar Cascade

Install:
  pip3 install opencv-python
"""

import cv2

print("="*50)
print("Test Face Detection - Basic")
print("="*50)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

if face_cascade.empty():
    print("❌ Failed to load Haar Cascade")
    exit(1)

print("✅ Haar Cascade loaded")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("❌ Cannot open camera")
    exit(1)

print("✅ Camera opened")
print("\nDetecting faces... (Press 'q' to quit)\n")

face_count = 0

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        if len(faces) > 0:
            face_count += 1
        
        cv2.putText(frame, f"Faces: {len(faces)}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Face Detection Test (Press Q)', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"\n✅ Test selesai!")
    print(f"   Frames with face detected: {face_count}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

finally:
    camera.release()
    cv2.destroyAllWindows()

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test face detection menggunakan Haar Cascade classifier dari OpenCV.
Ini adalah metode klasik machine learning untuk object detection.

Haar Cascade Algorithm:
Haar Cascade adalah machine learning based approach yang dikembangkan oleh Paul Viola
dan Michael Jones pada tahun 2001. Algorithm menggunakan cascade of classifiers trained
on positive (faces) dan negative (non-faces) images.

Cara Kerja Haar Cascade:
1. Haar Features:
   - Rectangle features yang detect edges, lines, dan patterns
   - Contoh: edge features (vertical, horizontal, diagonal)
   - Hitung difference antara sum pixel values di adjacent rectangles

2. Integral Image:
   - Pre-processing untuk fast feature calculation
   - Allows constant time computation untuk any rectangle

3. AdaBoost Training:
   - Select best features dari thousands of possible features
   - Weak classifiers digabung jadi strong classifier

4. Cascade of Classifiers:
   - Multi-stage classifier (cascade)
   - Early stages reject obvious non-faces quickly
   - Later stages do more detailed checking
   - Result: fast detection karena majority windows rejected early

Cara Kerja Program:
1. Load Pre-trained Model:
   - haarcascade_frontalface_default.xml dari OpenCV data
   - Model sudah trained on thousands of face samples
   - OpenCV provides various cascade files (face, eyes, smile, body, etc)

2. Camera Setup:
   - Open camera dengan cv2.VideoCapture(0)
   - Check jika camera berhasil dibuka

3. Main Detection Loop:
   - Capture frame dari camera
   - Convert ke grayscale (Haar Cascade works on grayscale)
   - detectMultiScale() untuk detect faces
   - Draw rectangle dan label pada detected faces
   - Display count dan visualization

4. detectMultiScale Parameters:
   - image: input grayscale image
   - scaleFactor=1.1: image pyramid scale (detect faces di berbagai sizes)
   - minNeighbors=5: minimum neighbors untuk retain detection (filter false positives)
   - minSize=(50,50): minimum face size dalam pixels (ignore faces terlalu kecil)

   Returns: list of rectangles (x, y, width, height) untuk each detected face

5. Visualization:
   - Green rectangle around each face
   - Label "Face" di atas rectangle
   - Counter showing jumlah faces di current frame

Color Spaces:
- BGR: OpenCV default (Blue, Green, Red)
- Grayscale: single channel, values 0-255
- cv2.cvtColor() convert antar color spaces
- Haar Cascade requires grayscale karena hanya analyze intensity patterns

Performance:
- Haar Cascade sangat fast (~30 FPS di Raspberry Pi)
- Trade-off: speed vs accuracy
- Modern alternatives: DNN face detectors (slower tapi lebih accurate)

Limitations:
1. Hanya detect frontal faces (tidak detect profile/side view)
2. Sensitive to lighting conditions
3. Can have false positives (detect non-faces as faces)
4. Not good dengan occlusions (glasses, mask, hair covering face)
5. Fixed features (tidak adaptive seperti deep learning)

Improvements:
- Combine dengan eye detection untuk validate faces
- Use face recognition untuk identify specific persons
- Add tracking untuk smooth detection across frames
- Try different cascade files (side face, profile, etc)

Other Cascade Classifiers Available:
- haarcascade_eye.xml: eye detection
- haarcascade_smile.xml: smile detection
- haarcascade_frontalface_alt.xml: alternative face detector
- haarcascade_fullbody.xml: full body detection
- haarcascade_upperbody.xml: upper body detection

Modern Alternatives (more accurate but slower):
- DNN face detector (cv2.dnn)
- MTCNN (Multi-task Cascaded CNN)
- RetinaFace
- MediaPipe Face Detection

Applications:
- Face recognition systems
- Security cameras
- Attendance systems
- Human-robot interaction
- Photo organization
- Snapchat-like filters
"""
