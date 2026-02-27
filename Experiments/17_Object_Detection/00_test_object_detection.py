#!/usr/bin/env python3
"""
Bab 17: Test Object Detection - Basic
======================================
Program sederhana untuk test OpenCV DNN object detection

Install:
  pip3 install opencv-python numpy

Menggunakan pre-trained MobileNet SSD dari OpenCV
"""

import cv2
import numpy as np

print("="*50)
print("Test Object Detection - Basic")
print("="*50)

CLASSES = ["background", "person", "bicycle", "car", "motorcycle", "airplane",
          "bus", "train", "truck", "boat", "traffic light", "fire hydrant",
          "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse",
          "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
          "umbrella", "handbag", "tie", "suitcase")

print("\nNote: Program ini test OpenCV DNN")
print("Untuk full object detection, gunakan program utama\n")

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("❌ Cannot open camera")
    exit(1)

print("✅ Camera opened")
print("Detecting objects... (Press 'q' to quit)\n")

detection_count = 0

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        edge_count = np.sum(edges > 0)
        
        if edge_count > 10000:
            detection_count += 1
            cv2.putText(frame, "Object detected!", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.putText(frame, f"Edge pixels: {edge_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.imshow('Object Detection Test (Press Q)', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"\n✅ Test selesai!")
    print(f"   Detections: {detection_count}")
    print("\nℹ️  Untuk object detection lengkap:")
    print("   ./01_mobilenet_ssd.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

finally:
    camera.release()
    cv2.destroyAllWindows()

"""
PENJELASAN PROGRAM:
==================
Program ini adalah test dasar untuk object detection. Program ini menggunakan simple
edge detection sebagai placeholder karena tidak load actual AI model (untuk test basic
camera dan image processing saja).

Object Detection Concepts:
Object detection adalah computer vision task untuk:
1. Detect objects dalam image/video
2. Classify object type (person, car, dog, etc)
3. Localize object position (bounding box coordinates)

Difference dari Image Classification:
- Classification: "Apa yang ada di image?" → single label untuk whole image
- Detection: "Apa saja yang ada dan dimana lokasinya?" → multiple objects dengan positions

Popular Object Detection Models:
1. YOLO (You Only Look Once):
   - Very fast (real-time detection)
   - Single-shot detector
   - Versions: YOLOv3, YOLOv4, YOLOv5, YOLOv8
   - Trade-off speed vs accuracy

2. MobileNet SSD:
   - Optimized untuk mobile/embedded devices
   - Good balance speed dan accuracy
   - Cocok untuk Raspberry Pi
   - Single Shot Detector (SSD)

3. Faster R-CNN:
   - Very accurate
   - Slower (not for real-time)
   - Two-stage detector

4. EfficientDet:
   - State-of-the-art accuracy dan efficiency
   - Scalable (D0 to D7)

COCO Dataset:
- Common Objects in Context
- 80 object classes (person, car, dog, cat, etc)
- Standard benchmark untuk object detection
- Pre-trained models biasanya trained on COCO

Placeholder Implementation (Program Ini):
Karena program ini hanya test basic, menggunakan edge detection sebagai placeholder:

1. Canny Edge Detection:
   - Algorithm untuk detect edges di image
   - Created by John Canny (1986)
   - Multi-stage algorithm: Gaussian blur, gradients, non-max suppression, hysteresis
   - Parameters: low threshold (50), high threshold (150)

2. Edge Count as "Object":
   - Hitung total edge pixels
   - Jika > 10000 pixels, consider as "object detected"
   - Ini bukan actual object detection, hanya simulasi

3. Visualization:
   - Display edge count
   - Show "Object detected!" jika threshold exceeded

Actual Object Detection (File 01_mobilenet_ssd.py):
Untuk real object detection, program lengkap akan:

1. Load Pre-trained Model:
   - MobileNet SSD model (.tflite atau .pb file)
   - Model weights trained on COCO dataset

2. Image Preprocessing:
   - Resize ke input size model (300x300 untuk MobileNet SSD)
   - Normalize pixel values (0-1 atau -1 to 1)
   - Convert ke format yang expected model (BGR/RGB, NCHW/NHWC)

3. Inference:
   - Feed preprocessed image ke model
   - Model output: bounding boxes, class IDs, confidence scores

4. Post-processing:
   - Filter detections by confidence threshold (contoh: > 0.5)
   - Non-Maximum Suppression (NMS) untuk remove duplicate detections
   - Map class IDs ke class names

5. Visualization:
   - Draw bounding boxes around detected objects
   - Add labels dengan class name dan confidence
   - Color code berdasarkan class

Performance Considerations:
- Raspberry Pi 4: ~1-5 FPS untuk MobileNet SSD
- Reduce input size untuk faster inference (trade-off accuracy)
- Use quantized models (int8) untuk 2-4x speedup
- Consider USB Neural Compute Stick (Intel Movidius) atau Coral Edge TPU untuk
  10-20x performance boost

Applications:
- Autonomous navigation (detect people, vehicles, obstacles)
- Security systems (detect intruders)
- Retail (detect products, count customers)
- Robotics (identify and manipulate objects)
- Traffic monitoring (count vehicles, detect violations)
- Wildlife monitoring (detect and classify animals)

Metrics untuk Evaluate Object Detection:
- Precision: berapa banyak detections yang correct
- Recall: berapa banyak actual objects yang detected
- mAP (mean Average Precision): standard metric untuk compare models
- FPS: frames per second (inference speed)
- IoU (Intersection over Union): overlap antara predicted dan ground truth boxes
"""
