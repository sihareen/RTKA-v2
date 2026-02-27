#!/usr/bin/env python3
"""
Bab 16.1: Face Detection dengan OpenCV - Haar Cascade & DNN
============================================================
Deteksi wajah real-time menggunakan dua metode:
1. Haar Cascade (klasik, cepat)
2. DNN - Deep Neural Network (modern, akurat)

Hardware:
- Raspberry Pi Camera / USB Webcam

Install:
  pip3 install opencv-python opencv-contrib-python numpy

Models akan di-download otomatis dari OpenCV repository
"""

import cv2
import numpy as np
import time
import os
import urllib.request
from datetime import datetime

print("="*70)
print("Face Detection - Haar Cascade & DNN Methods")
print("="*70)

# ============================================================================
# MODEL SETUP & DOWNLOAD
# ============================================================================

# Haar Cascade model paths
HAAR_FACE_PATH = "haarcascade_frontalface_default.xml"
HAAR_EYE_PATH = "haarcascade_eye.xml"

# DNN model paths
DNN_PROTO_PATH = "deploy.prototxt"
DNN_MODEL_PATH = "res10_300x300_ssd_iter_140000.caffemodel"

# Model URLs
HAAR_FACE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
HAAR_EYE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_eye.xml"
DNN_PROTO_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
DNN_MODEL_URL = "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"

def download_file(url, filepath):
    """Download file if not exists"""
    if os.path.exists(filepath):
        return True
    
    print(f"📥 Downloading: {os.path.basename(filepath)}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"✅ Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def setup_models():
    """Download all required models"""
    print("\n🔧 Setting up face detection models...")
    
    models = [
        (HAAR_FACE_URL, HAAR_FACE_PATH),
        (HAAR_EYE_URL, HAAR_EYE_PATH),
        (DNN_PROTO_URL, DNN_PROTO_PATH),
        (DNN_MODEL_URL, DNN_MODEL_PATH)
    ]
    
    for url, path in models:
        if not download_file(url, path):
            return False
    
    print("✅ All models ready!")
    return True

# ============================================================================
# FACE DETECTION CLASSES
# ============================================================================

class HaarCascadeFaceDetector:
    """Face detection using Haar Cascade (OpenCV classic method)"""
    
    def __init__(self):
        print("\n🔧 Initializing Haar Cascade detector...")
        
        self.face_cascade = cv2.CascadeClassifier(HAAR_FACE_PATH)
        self.eye_cascade = cv2.CascadeClassifier(HAAR_EYE_PATH)
        
        if self.face_cascade.empty() or self.eye_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade models")
        
        print("✅ Haar Cascade detector ready")
        print("   • Fast performance (50+ FPS)")
        print("   • Good for frontal faces")
        print("   • May have false positives")
    
    def detect(self, frame, detect_eyes=True):
        """Detect faces (and optionally eyes) in frame"""
        # Convert to grayscale (Haar works on grayscale)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        results = []
        
        for (x, y, w, h) in faces:
            face_data = {
                'bbox': (x, y, w, h),
                'confidence': 1.0,  # Haar doesn't provide confidence
                'eyes': []
            }
            
            if detect_eyes:
                # Region of interest for eyes (upper half of face)
                roi_gray = gray[y:y+h//2, x:x+w]
                
                eyes = self.eye_cascade.detectMultiScale(
                    roi_gray,
                    scaleFactor=1.1,
                    minNeighbors=3,
                    minSize=(15, 15)
                )
                
                # Adjust eye coordinates to frame coordinates
                for (ex, ey, ew, eh) in eyes:
                    face_data['eyes'].append((x + ex, y + ey, ew, eh))
            
            results.append(face_data)
        
        return results

class DNNFaceDetector:
    """Face detection using DNN (Deep Neural Network)"""
    
    def __init__(self, confidence_threshold=0.5):
        print("\n🔧 Initializing DNN face detector...")
        
        self.net = cv2.dnn.readNetFromCaffe(DNN_PROTO_PATH, DNN_MODEL_PATH)
        self.confidence_threshold = confidence_threshold
        
        print("✅ DNN detector ready")
        print(f"   • Higher accuracy")
        print(f"   • Works on various angles")
        print(f"   • Confidence threshold: {confidence_threshold}")
        print(f"   • Slower than Haar (~10-15 FPS)")
    
    def detect(self, frame):
        """Detect faces using DNN"""
        (h, w) = frame.shape[:2]
        
        # Prepare blob from image
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0)
        )
        
        # Pass blob through network
        self.net.setInput(blob)
        detections = self.net.forward()
        
        results = []
        
        # Parse detections
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                # Get bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Ensure bounding box is within frame
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(w, endX)
                endY = min(h, endY)
                
                results.append({
                    'bbox': (startX, startY, endX - startX, endY - startY),
                    'confidence': float(confidence),
                    'eyes': []  # DNN doesn't detect eyes separately
                })
        
        return results

# ============================================================================
# VISUALIZATION & DEMO
# ============================================================================

def draw_detections(frame, detections, method_name, color=(0, 255, 0)):
    """Draw bounding boxes and labels on frame"""
    output = frame.copy()
    
    for detection in detections:
        x, y, w, h = detection['bbox']
        confidence = detection['confidence']
        
        # Draw face bounding box
        cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)
        
        # Draw label with confidence
        label = f"{method_name}: {confidence:.2f}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        
        # Background for text
        cv2.rectangle(output, 
                     (x, y - label_size[1] - 10),
                     (x + label_size[0], y),
                     color, -1)
        
        cv2.putText(output, label, (x, y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw eyes if detected
        for (ex, ey, ew, eh) in detection.get('eyes', []):
            cv2.rectangle(output, (ex, ey), (ex + ew, ey + eh), (255, 0, 0), 1)
            cv2.circle(output, (ex + ew//2, ey + eh//2), 2, (0, 0, 255), -1)
    
    return output

def demo_face_detection_live(camera, detector, method_name):
    """Live face detection demo"""
    print(f"\n🎥 Starting {method_name} face detection...")
    print("   Press 'q' to quit")
    print("   Press 's' to save snapshot")
    print("   Press 'c' to capture face only")
    
    fps_start = time.time()
    fps_counter = 0
    fps = 0
    
    face_counter = 0
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Detect faces
        detection_start = time.time()
        detections = detector.detect(frame)
        detection_time = (time.time() - detection_start) * 1000
        
        # Draw detections
        output = draw_detections(frame, detections, method_name)
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 30:
            fps_end = time.time()
            fps = fps_counter / (fps_end - fps_start)
            fps_start = fps_end
            fps_counter = 0
        
        # Draw info overlay
        info = [
            f"FPS: {fps:.1f}",
            f"Detection: {detection_time:.1f}ms",
            f"Faces: {len(detections)}"
        ]
        
        for i, text in enumerate(info):
            cv2.putText(output, text, (10, 30 + i*30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show frame
        cv2.imshow(f'{method_name} Face Detection (Press Q)', output)
        
        # Handle key press
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        
        elif key == ord('s'):
            filename = f"face_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, output)
            print(f"   📸 Snapshot saved: {filename}")
        
        elif key == ord('c'):
            # Save individual face crops
            for i, detection in enumerate(detections):
                x, y, w, h = detection['bbox']
                face_crop = frame[y:y+h, x:x+w]
                
                filename = f"face_{face_counter:04d}.jpg"
                cv2.imwrite(filename, face_crop)
                print(f"   👤 Face saved: {filename}")
                face_counter += 1
    
    cv2.destroyAllWindows()

def compare_methods(camera):
    """Compare Haar vs DNN side-by-side"""
    print("\n📊 Comparing Haar Cascade vs DNN...")
    print("   Press 'q' to quit")
    
    haar_detector = HaarCascadeFaceDetector()
    dnn_detector = DNNFaceDetector()
    
    haar_times = []
    dnn_times = []
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Haar detection
        start = time.time()
        haar_detections = haar_detector.detect(frame, detect_eyes=False)
        haar_time = (time.time() - start) * 1000
        haar_times.append(haar_time)
        
        # DNN detection
        start = time.time()
        dnn_detections = dnn_detector.detect(frame)
        dnn_time = (time.time() - start) * 1000
        dnn_times.append(dnn_time)
        
        # Keep last 30 measurements
        if len(haar_times) > 30:
            haar_times.pop(0)
            dnn_times.pop(0)
        
        # Create side-by-side comparison
        haar_frame = draw_detections(frame.copy(), haar_detections, "Haar", (0, 255, 0))
        dnn_frame = draw_detections(frame.copy(), dnn_detections, "DNN", (255, 0, 0))
        
        # Combine frames
        combined = np.hstack([haar_frame, dnn_frame])
        
        # Add comparison info
        avg_haar = np.mean(haar_times)
        avg_dnn = np.mean(dnn_times)
        
        cv2.putText(combined, f"Haar: {avg_haar:.0f}ms | Faces: {len(haar_detections)}", 
                   (10, combined.shape[0] - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(combined, f"DNN: {avg_dnn:.0f}ms | Faces: {len(dnn_detections)}", 
                   (frame.shape[1] + 10, combined.shape[0] - 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        cv2.imshow('Haar vs DNN Comparison (Press Q)', combined)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 Face Detection Tutorial")
    print("   Haar Cascade (classic) vs DNN (modern)")
    
    # Setup models
    if not setup_models():
        print("❌ Failed to download models")
        return
    
    # Try to open camera
    camera = None
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Initialize Camera")
        print("  2. Face Detection - Haar Cascade (Fast)")
        print("  3. Face Detection - DNN (Accurate)")
        print("  4. Compare Haar vs DNN (Side-by-side)")
        print("  5. Test on Static Image")
        print("  6. Release Camera")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            if camera:
                print("⚠️  Camera already initialized")
                continue
            
            cam_id = input("Camera ID (0 for default): ").strip()
            cam_id = int(cam_id) if cam_id.isdigit() else 0
            
            camera = cv2.VideoCapture(cam_id)
            if camera.isOpened():
                print(f"✅ Camera {cam_id} opened")
            else:
                print(f"❌ Cannot open camera {cam_id}")
                camera = None
        
        elif choice == "2":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            detector = HaarCascadeFaceDetector()
            demo_face_detection_live(camera, detector, "Haar")
        
        elif choice == "3":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            detector = DNNFaceDetector()
            demo_face_detection_live(camera, detector, "DNN")
        
        elif choice == "4":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            compare_methods(camera)
        
        elif choice == "5":
            image_path = input("Image path: ").strip()
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                continue
            
            frame = cv2.imread(image_path)
            
            haar_detector = HaarCascadeFaceDetector()
            dnn_detector = DNNFaceDetector()
            
            haar_faces = haar_detector.detect(frame)
            dnn_faces = dnn_detector.detect(frame)
            
            haar_result = draw_detections(frame.copy(), haar_faces, "Haar", (0, 255, 0))
            dnn_result = draw_detections(frame.copy(), dnn_faces, "DNN", (255, 0, 0))
            
            cv2.imshow('Haar Result', haar_result)
            cv2.imshow('DNN Result', dnn_result)
            print("   Press any key to close...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        elif choice == "6":
            if camera:
                camera.release()
                camera = None
                print("📷 Camera released")
        
        elif choice == "7":
            if camera:
                camera.release()
            break
        
        else:
            print("❌ Invalid choice")
    
    print("\n✅ Program finished!")
    print()
    print("🎓 What you learned:")
    print("  • Haar Cascade vs DNN face detection")
    print("  • Real-time face tracking")
    print("  • Performance comparison")
    print("  • Eye detection (Haar)")
    print("  • Confidence scoring (DNN)")
    print()
    print("📖 Next: Bab 16.2 - Face Recognition")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated")
        cv2.destroyAllWindows()
