#!/usr/bin/env python3
"""
Bab 17.1: Object Detection dengan MobileNet SSD
================================================
Deteksi objek real-time menggunakan MobileNet SSD TensorFlow Lite
Model dapat mendeteksi 80+ kelas objek dari COCO dataset

Hardware:
- Raspberry Pi 4/5 (4GB+ RAM recommended)
- Pi Camera v2/v3 atau USB Webcam

Install:
  pip3 install opencv-python numpy pillow tflite-runtime

Model akan di-download otomatis dari TensorFlow Hub
"""

import cv2
import numpy as np
import time
import os
import urllib.request
from datetime import datetime

try:
    import tflite_runtime.interpreter as tflite
except:
    import tensorflow.lite as tflite

print("="*70)
print("Object Detection - MobileNet SSD TFLite")
print("="*70)

# ============================================================================
# MODEL SETUP
# ============================================================================

MODEL_URL = "https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "detect.tflite")
LABELS_PATH = os.path.join(MODEL_DIR, "labelmap.txt")

# COCO dataset labels (80 classes)
COCO_LABELS = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
    'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

def download_model():
    """Download and extract MobileNet SSD model"""
    if os.path.exists(MODEL_PATH):
        print("✅ Model already downloaded")
        return True
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("📥 Downloading MobileNet SSD model (~4MB)...")
    zip_path = os.path.join(MODEL_DIR, "model.zip")
    
    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        print("✅ Download complete")
        
        # Extract zip
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(MODEL_DIR)
        
        os.remove(zip_path)
        
        # Create labels file
        with open(LABELS_PATH, 'w') as f:
            f.write('???\n')  # Index 0 is background
            for label in COCO_LABELS:
                f.write(label + '\n')
        
        print("✅ Model extracted and ready")
        return True
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

# ============================================================================
# OBJECT DETECTOR CLASS
# ============================================================================

class MobileNetSSDDetector:
    """TensorFlow Lite MobileNet SSD object detector"""
    
    def __init__(self, model_path=MODEL_PATH, labels_path=LABELS_PATH, 
                 confidence_threshold=0.5, num_threads=4):
        """Initialize object detector"""
        
        print("\n🔧 Initializing MobileNet SSD detector...")
        
        self.confidence_threshold = confidence_threshold
        
        # Load labels
        with open(labels_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        
        print(f"   • Loaded {len(self.labels)} class labels")
        
        # Initialize TFLite interpreter
        self.interpreter = tflite.Interpreter(
            model_path=model_path,
            num_threads=num_threads
        )
        self.interpreter.allocate_tensors()
        
        # Get input and output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.input_shape = self.input_details[0]['shape']
        self.input_height = self.input_shape[1]
        self.input_width = self.input_shape[2]
        
        print(f"   • Model input size: {self.input_width}x{self.input_height}")
        print(f"   • Confidence threshold: {confidence_threshold}")
        print(f"   • CPU threads: {num_threads}")
        print("✅ Detector ready")
    
    def preprocess(self, frame):
        """Preprocess frame for model input"""
        # Resize to model input size
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Add batch dimension
        input_data = np.expand_dims(rgb, axis=0)
        
        return input_data
    
    def detect(self, frame):
        """Detect objects in frame"""
        # Preprocess
        input_data = self.preprocess(frame)
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        # Run inference
        start_time = time.time()
        self.interpreter.invoke()
        inference_time = (time.time() - start_time) * 1000
        
        # Get output tensors
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
        num_detections = int(self.interpreter.get_tensor(self.output_details[3]['index'])[0])
        
        # Parse detections
        detections = []
        height, width = frame.shape[:2]
        
        for i in range(num_detections):
            score = scores[i]
            
            if score > self.confidence_threshold:
                # Get bounding box (normalized coordinates)
                ymin, xmin, ymax, xmax = boxes[i]
                
                # Convert to pixel coordinates
                x1 = int(xmin * width)
                y1 = int(ymin * height)
                x2 = int(xmax * width)
                y2 = int(ymax * height)
                
                # Get class label
                class_id = int(classes[i])
                label = self.labels[class_id] if class_id < len(self.labels) else 'unknown'
                
                detections.append({
                    'bbox': (x1, y1, x2, y2),
                    'class': label,
                    'class_id': class_id,
                    'confidence': float(score)
                })
        
        return detections, inference_time

# ============================================================================
# VISUALIZATION
# ============================================================================

# Color map for different classes (BGR format)
COLORS = [
    (0, 255, 0),    # Green
    (255, 0, 0),    # Blue
    (0, 0, 255),    # Red
    (255, 255, 0),  # Cyan
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Yellow
    (128, 0, 128),  # Purple
    (255, 165, 0),  # Orange
]

def get_color_for_class(class_id):
    """Get consistent color for class"""
    return COLORS[class_id % len(COLORS)]

def draw_detections(frame, detections):
    """Draw bounding boxes and labels"""
    output = frame.copy()
    
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox']
        label = detection['class']
        confidence = detection['confidence']
        class_id = detection['class_id']
        
        # Get color for this class
        color = get_color_for_class(class_id)
        
        # Draw bounding box
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        
        # Prepare label text
        label_text = f"{label}: {confidence:.2f}"
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        
        # Draw label background
        cv2.rectangle(output,
                     (x1, y1 - text_height - baseline - 5),
                     (x1 + text_width, y1),
                     color, -1)
        
        # Draw label text
        cv2.putText(output, label_text,
                   (x1, y1 - baseline - 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return output

# ============================================================================
# DEMOS
# ============================================================================

def demo_live_detection(camera, detector):
    """Live object detection demo"""
    print("\n🎥 Starting live object detection...")
    print("   Press 'q' to quit")
    print("   Press 's' to save snapshot")
    print("   Press '+' to increase confidence")
    print("   Press '-' to decrease confidence")
    
    fps_start = time.time()
    fps_counter = 0
    fps = 0
    
    object_counter = {}
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        # Detect objects
        detections, inference_time = detector.detect(frame)
        
        # Draw detections
        output = draw_detections(frame, detections)
        
        # Count objects
        for detection in detections:
            obj_class = detection['class']
            object_counter[obj_class] = object_counter.get(obj_class, 0) + 1
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 30:
            fps_end = time.time()
            fps = fps_counter / (fps_end - fps_start)
            fps_start = fps_end
            fps_counter = 0
        
        # Draw info overlay
        info_y = 30
        cv2.putText(output, f"FPS: {fps:.1f}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info_y += 25
        cv2.putText(output, f"Inference: {inference_time:.0f}ms", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info_y += 25
        cv2.putText(output, f"Objects: {len(detections)}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        info_y += 25
        cv2.putText(output, f"Confidence: {detector.confidence_threshold:.2f}", (10, info_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Show detected objects list
        if detections:
            objects_text = ", ".join([d['class'] for d in detections])
            cv2.putText(output, objects_text[:50], (10, output.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Object Detection (Press Q)', output)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, output)
            print(f"   📸 Saved: {filename}")
        elif key == ord('+'):
            detector.confidence_threshold = min(0.95, detector.confidence_threshold + 0.05)
            print(f"   Confidence: {detector.confidence_threshold:.2f}")
        elif key == ord('-'):
            detector.confidence_threshold = max(0.1, detector.confidence_threshold - 0.05)
            print(f"   Confidence: {detector.confidence_threshold:.2f}")
    
    cv2.destroyAllWindows()
    
    # Print statistics
    print("\n📊 Detection Statistics:")
    for obj_class, count in sorted(object_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"   {obj_class}: {count} detections")

def demo_static_image(detector, image_path):
    """Detect objects in static image"""
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    frame = cv2.imread(image_path)
    
    print(f"\n🖼️  Processing: {image_path}")
    
    # Detect
    detections, inference_time = detector.detect(frame)
    
    print(f"   ⏱️  Inference time: {inference_time:.1f}ms")
    print(f"   🎯 Detected {len(detections)} objects:")
    
    for i, det in enumerate(detections, 1):
        print(f"      {i}. {det['class']} ({det['confidence']:.2f})")
    
    # Draw and show
    output = draw_detections(frame, detections)
    cv2.imshow('Detection Result (Press any key)', output)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n💡 MobileNet SSD Object Detection")
    print("   80+ object classes from COCO dataset")
    
    # Download model
    if not download_model():
        return
    
    camera = None
    detector = None
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Initialize Detector")
        print("  2. Open Camera")
        print("  3. Live Object Detection")
        print("  4. Detect in Static Image")
        print("  5. Show Detectable Classes")
        print("  6. Performance Test")
        print("  7. Release Resources")
        print("  8. Exit")
        print("="*70)
        
        choice = input("\nChoice: ").strip()
        
        if choice == "1":
            confidence = input("Confidence threshold (0.1-0.9) [0.5]: ").strip()
            confidence = float(confidence) if confidence else 0.5
            
            threads = input("CPU threads (1-4) [4]: ").strip()
            threads = int(threads) if threads.isdigit() else 4
            
            detector = MobileNetSSDDetector(
                confidence_threshold=confidence,
                num_threads=threads
            )
        
        elif choice == "2":
            cam_id = input("Camera ID [0]: ").strip()
            cam_id = int(cam_id) if cam_id.isdigit() else 0
            
            camera = cv2.VideoCapture(cam_id)
            if camera.isOpened():
                print(f"✅ Camera {cam_id} opened")
            else:
                print("❌ Cannot open camera")
                camera = None
        
        elif choice == "3":
            if not detector:
                print("❌ Initialize detector first!")
                continue
            if not camera:
                print("❌ Open camera first!")
                continue
            
            demo_live_detection(camera, detector)
        
        elif choice == "4":
            if not detector:
                print("❌ Initialize detector first!")
                continue
            
            image_path = input("Image path: ").strip()
            demo_static_image(detector, image_path)
        
        elif choice == "5":
            print("\n📋 Detectable Object Classes (80):")
            for i, label in enumerate(COCO_LABELS, 1):
                print(f"   {i:2d}. {label}")
        
        elif choice == "6":
            if not detector:
                print("❌ Initialize detector first!")
                continue
            
            print("\n⚡ Performance Test...")
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            
            times = []
            for i in range(50):
                _, inference_time = detector.detect(test_frame)
                times.append(inference_time)
                print(f"   Frame {i+1}/50: {inference_time:.1f}ms", end='\r')
            
            print(f"\n   Average: {np.mean(times):.1f}ms")
            print(f"   Min: {np.min(times):.1f}ms")
            print(f"   Max: {np.max(times):.1f}ms")
            print(f"   FPS: {1000/np.mean(times):.1f}")
        
        elif choice == "7":
            if camera:
                camera.release()
                camera = None
            detector = None
            print("📷 Resources released")
        
        elif choice == "8":
            if camera:
                camera.release()
            break
    
    print("\n✅ Program finished!")
    print("\n🎓 What you learned:")
    print("  • MobileNet SSD architecture")
    print("  • TensorFlow Lite inference")
    print("  • Real-time object detection")
    print("  • COCO dataset classes")
    print("  • Confidence thresholding")
    print("\n📖 Next: Bab 18 - Gesture Recognition")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated")
        cv2.destroyAllWindows()
