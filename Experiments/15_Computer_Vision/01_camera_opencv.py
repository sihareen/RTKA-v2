#!/usr/bin/env python3
"""
Bab 15.1: OpenCV dan Camera Streaming
======================================
Pengenalan OpenCV dan streaming dari Raspberry Pi Camera

Topics:
- Setup Raspberry Pi Camera / USB Webcam
- Capture image & video stream
- OpenCV basics (read, display, save)
- Frame processing pipeline

Hardware Requirements:
- Raspberry Pi Camera Module v2/v3 atau USB Webcam

Install:
  sudo apt install -y python3-opencv python3-picamera2
  pip3 install opencv-python pillow numpy
"""

import cv2
import numpy as np
import time
from datetime import datetime
import os

# Try import PiCamera2 (for Pi Camera)
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False

print("="*70)
print("OpenCV dan Camera Streaming - Computer Vision Foundation")
print("="*70)

# ============================================================================
# CAMERA CLASSES
# ============================================================================

class PiCameraStream:
    """Raspberry Pi Camera Stream using Picamera2"""
    
    def __init__(self, resolution=(640, 480), framerate=30):
        if not PICAMERA_AVAILABLE:
            raise ImportError("Picamera2 not installed")
        
        print("\n📷 Initializing Pi Camera...")
        
        self.picam = Picamera2()
        config = self.picam.create_preview_configuration(
            main={"size": resolution, "format": "RGB888"}
        )
        self.picam.configure(config)
        self.picam.start()
        
        time.sleep(2)  # Camera warm-up
        
        print(f"✅ Pi Camera ready: {resolution[0]}x{resolution[1]} @ {framerate}fps")
    
    def read(self):
        """Read frame from camera"""
        frame = self.picam.capture_array()
        return True, frame
    
    def release(self):
        """Release camera"""
        self.picam.stop()
        print("📷 Pi Camera released")

class USBCameraStream:
    """USB Webcam Stream using OpenCV"""
    
    def __init__(self, camera_id=0, resolution=(640, 480), framerate=30):
        print(f"\n📹 Initializing USB Camera (ID: {camera_id})...")
        
        self.cap = cv2.VideoCapture(camera_id)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_id}")
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, framerate)
        
        # Verify settings
        actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        print(f"✅ USB Camera ready: {int(actual_w)}x{int(actual_h)} @ {int(actual_fps)}fps")
    
    def read(self):
        """Read frame from camera"""
        return self.cap.read()
    
    def release(self):
        """Release camera"""
        self.cap.release()
        print("📹 USB Camera released")

def detect_available_cameras():
    """Detect available cameras"""
    print("\n🔍 Detecting available cameras...")
    
    available = []
    
    # Check for Pi Camera
    if PICAMERA_AVAILABLE:
        try:
            picam = Picamera2()
            picam.close()
            available.append("Pi Camera")
            print("   ✓ Raspberry Pi Camera detected")
        except:
            pass
    
    # Check USB cameras (0-4)
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(f"USB Camera {i}")
            print(f"   ✓ USB Camera /dev/video{i} detected")
            cap.release()
    
    if not available:
        print("   ✗ No cameras found!")
    
    return available

# ============================================================================
# OPENCV BASICS
# ============================================================================

def demo_basic_operations(frame):
    """Demonstrate basic OpenCV operations"""
    print("\n🎨 Applying image transformations...")
    
    # Original
    cv2.imshow('1. Original', frame)
    
    # Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('2. Grayscale', gray)
    
    # Blur
    blurred = cv2.GaussianBlur(frame, (15, 15), 0)
    cv2.imshow('3. Gaussian Blur', blurred)
    
    # Edge detection (Canny)
    edges = cv2.Canny(gray, 50, 150)
    cv2.imshow('4. Edge Detection', edges)
    
    # Color threshold (example: detect blue)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    cv2.imshow('5. Blue Mask', mask)
    
    # Resize
    resized = cv2.resize(frame, (320, 240))
    cv2.imshow('6. Resized (320x240)', resized)
    
    print("   Press any key on image windows to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def demo_drawing(frame):
    """Demonstrate drawing on frame"""
    print("\n✏️  Drawing on frame...")
    
    canvas = frame.copy()
    height, width = canvas.shape[:2]
    
    # Rectangle
    cv2.rectangle(canvas, (50, 50), (200, 150), (0, 255, 0), 2)
    cv2.putText(canvas, "Rectangle", (55, 45), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Circle
    cv2.circle(canvas, (width//2, height//2), 50, (255, 0, 0), 2)
    cv2.putText(canvas, "Circle", (width//2 - 30, height//2 - 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    # Line
    cv2.line(canvas, (300, 100), (450, 200), (0, 0, 255), 2)
    cv2.putText(canvas, "Line", (310, 95), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # Polygon
    pts = np.array([[400, 300], [450, 350], [420, 400], [380, 380]], np.int32)
    cv2.polylines(canvas, [pts], True, (255, 255, 0), 2)
    
    # Text with background
    text = "OpenCV Drawing Demo"
    font = cv2.FONT_HERSHEY_DUPLEX
    (text_width, text_height), _ = cv2.getTextSize(text, font, 1, 2)
    cv2.rectangle(canvas, (10, height-50), (20 + text_width, height-10), (0, 0, 0), -1)
    cv2.putText(canvas, text, (15, height-20), font, 1, (255, 255, 255), 2)
    
    cv2.imshow('Drawing Demo', canvas)
    print("   Press any key to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return canvas

def demo_video_stream(camera):
    """Demonstrate live video streaming"""
    print("\n🎥 Starting video stream...")
    print("   Press 'q' to quit")
    print("   Press 's' to save snapshot")
    print("   Press 'r' to start/stop recording")
    
    recording = False
    video_writer = None
    snapshot_counter = 0
    
    fps_start_time = time.time()
    fps_counter = 0
    fps = 0
    
    while True:
        ret, frame = camera.read()
        
        if not ret:
            print("   ✗ Failed to grab frame")
            break
        
        # Calculate FPS
        fps_counter += 1
        if fps_counter >= 30:
            fps_end_time = time.time()
            fps = fps_counter / (fps_end_time - fps_start_time)
            fps_start_time = fps_end_time
            fps_counter = 0
        
        # Add FPS overlay
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Recording indicator
        if recording:
            cv2.circle(frame, (frame.shape[1] - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (frame.shape[1] - 80, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Display frame
        cv2.imshow('Camera Stream (Press Q to quit)', frame)
        
        # Record if enabled
        if recording and video_writer is not None:
            video_writer.write(frame)
        
        # Handle key press
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        
        elif key == ord('s'):
            # Save snapshot
            snapshot_path = f"snapshot_{snapshot_counter:04d}.jpg"
            cv2.imwrite(snapshot_path, frame)
            print(f"   📸 Snapshot saved: {snapshot_path}")
            snapshot_counter += 1
        
        elif key == ord('r'):
            # Toggle recording
            if not recording:
                # Start recording
                video_path = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, 
                                               (frame.shape[1], frame.shape[0]))
                recording = True
                print(f"   🔴 Recording started: {video_path}")
            else:
                # Stop recording
                recording = False
                if video_writer:
                    video_writer.release()
                    video_writer = None
                print(f"   ⏹️  Recording stopped")
    
    # Cleanup
    if video_writer:
        video_writer.release()
    
    cv2.destroyAllWindows()

def demo_performance_test(camera, duration=10):
    """Test camera performance"""
    print(f"\n⏱️  Running {duration}s performance test...")
    
    frame_count = 0
    start_time = time.time()
    
    while (time.time() - start_time) < duration:
        ret, frame = camera.read()
        if ret:
            frame_count += 1
        
        # Show progress
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        print(f"   Frames: {frame_count} | FPS: {fps:.1f} | Time: {elapsed:.1f}s", end='\r')
    
    print()  # New line
    
    total_time = time.time() - start_time
    avg_fps = frame_count / total_time
    
    print(f"\n📊 Performance Results:")
    print(f"   Total frames: {frame_count}")
    print(f"   Duration: {total_time:.2f}s")
    print(f"   Average FPS: {avg_fps:.2f}")
    
    if avg_fps >= 25:
        print("   Performance: Excellent ✓✓")
    elif avg_fps >= 15:
        print("   Performance: Good ✓")
    else:
        print("   Performance: Consider lower resolution")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n📚 OpenCV Camera Tutorial")
    
    # Detect cameras
    cameras = detect_available_cameras()
    
    if not cameras:
        print("\n❌ No camera detected!")
        print("   Troubleshooting:")
        print("   • Enable camera: sudo raspi-config")
        print("   • Check connection")
        print("   • Install picamera2: sudo apt install python3-picamera2")
        return
    
    camera = None
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Initialize Camera")
        print("  2. Capture Single Image")
        print("  3. Basic Image Operations Demo")
        print("  4. Drawing Demo")
        print("  5. Live Video Stream")
        print("  6. Performance Test")
        print("  7. Release Camera")
        print("  8. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            if camera:
                print("⚠️  Camera already initialized")
                continue
            
            print("\nSelect camera:")
            for i, cam in enumerate(cameras):
                print(f"  {i+1}. {cam}")
            
            cam_choice = input("Choice: ").strip()
            
            try:
                cam_idx = int(cam_choice) - 1
                selected = cameras[cam_idx]
                
                if "Pi Camera" in selected:
                    camera = PiCameraStream(resolution=(640, 480))
                else:
                    usb_id = int(selected.split()[-1])
                    camera = USBCameraStream(camera_id=usb_id, resolution=(640, 480))
            
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif choice == "2":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            ret, frame = camera.read()
            if ret:
                filename = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"✅ Image saved: {filename}")
                print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   Size: {os.path.getsize(filename) / 1024:.1f} KB")
            else:
                print("❌ Failed to capture frame")
        
        elif choice == "3":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            ret, frame = camera.read()
            if ret:
                demo_basic_operations(frame)
        
        elif choice == "4":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            ret, frame = camera.read()
            if ret:
                demo_drawing(frame)
        
        elif choice == "5":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            demo_video_stream(camera)
        
        elif choice == "6":
            if not camera:
                print("❌ Initialize camera first!")
                continue
            
            duration = input("Test duration (seconds, default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            demo_performance_test(camera, duration)
        
        elif choice == "7":
            if camera:
                camera.release()
                camera = None
            else:
                print("⚠️  No camera to release")
        
        elif choice == "8":
            if camera:
                camera.release()
            break
        
        else:
            print("❌ Invalid choice")
    
    print("\n✅ Program finished!")
    print()
    print("🎓 What you learned:")
    print("  • Camera initialization (Pi Camera & USB)")
    print("  • Capturing images & video streams")
    print("  • Basic OpenCV operations")
    print("  • Drawing on frames")
    print("  • FPS measurement")
    print("  • Video recording")
    print()
    print("📖 Next: Bab 15.2 - Image Processing")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated")
        cv2.destroyAllWindows()
