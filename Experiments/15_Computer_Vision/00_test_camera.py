#!/usr/bin/env python3
"""
Bab 15: Test Camera - Basic
============================
Program sederhana untuk test kamera

Support:
- Pi Camera (Picamera2)
- USB Webcam (OpenCV)

Install:
  pip3 install opencv-python
"""

import cv2
import time

print("="*50)
print("Test Camera - Basic")
print("="*50)

camera = None
camera_type = None

try:
    from picamera2 import Picamera2
    camera = Picamera2()
    config = camera.create_preview_configuration(main={"size": (640, 480)})
    camera.configure(config)
    camera.start()
    time.sleep(2)
    camera_type = "Pi Camera"
    print("✅ Pi Camera detected")
except:
    pass

if camera is None:
    try:
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            camera_type = "USB Webcam"
            print("✅ USB Webcam detected")
        else:
            camera = None
    except:
        pass

if camera is None:
    print("❌ No camera found!")
    exit(1)

print(f"\nCamera type: {camera_type}")
print("Capturing frames... (5s)")
print("Press 'q' to quit early\n")

start_time = time.time()
frame_count = 0

try:
    while (time.time() - start_time) < 5:
        if camera_type == "Pi Camera":
            frame = camera.capture_array()
        else:
            ret, frame = camera.read()
            if not ret:
                break
        
        frame_count += 1
        
        cv2.imshow('Camera Test (Press Q)', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    
    print(f"\n✅ Test selesai!")
    print(f"   Frames captured: {frame_count}")
    print(f"   FPS: {fps:.1f}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

finally:
    if camera_type == "Pi Camera":
        camera.stop()
    else:
        camera.release()
    cv2.destroyAllWindows()

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test camera (Pi Camera atau USB Webcam) pada Raspberry Pi
menggunakan OpenCV untuk computer vision applications.

Camera Options:
1. Raspberry Pi Camera Module (Picamera2):
   - Camera khusus untuk Raspberry Pi, connect via CSI port
   - Kualitas bagus, low latency, terintegrasi dengan hardware
   - Perlu enable camera interface di raspi-config
   - Library: picamera2 (modern, replacement dari picamera legacy)

2. USB Webcam (OpenCV):
   - Standard USB webcam, plug and play
   - Compatible dengan berbagai webcam brands
   - Accessed via video4linux (v4l) di Linux
   - Device number: /dev/video0, /dev/video1, etc

Cara Kerja Program:
1. Camera Detection:
   - Try Picamera2 first (Pi Camera Module)
   - Jika gagal, fallback ke USB webcam via cv2.VideoCapture(0)
   - Device index 0 = first camera, 1 = second camera, dst

2. Pi Camera Setup:
   - Picamera2() create camera object
   - create_preview_configuration() set resolusi 640x480
   - configure() apply configuration
   - start() start camera stream
   - sleep(2) camera warm-up untuk auto exposure dan white balance

3. USB Camera Setup:
   - VideoCapture(0) open first video device
   - isOpened() check jika camera successfully opened

4. Frame Capture Loop:
   - Pi Camera: capture_array() langsung return NumPy array (BGR format)
   - USB Camera: read() return (success_flag, frame)
   - Display frame menggunakan cv2.imshow()
   - cv2.waitKey(1) wait 1ms untuk keyboard input dan window refresh

5. FPS Calculation:
   - FPS = Total Frames / Elapsed Time
   - Indicates camera and processing performance
   - Typical: Pi Camera ~30 FPS, USB webcam ~15-30 FPS

OpenCV Window Operations:
- cv2.imshow(window_name, image): display image di window
- cv2.waitKey(delay_ms): wait for keyboard input, return key code
- cv2.destroyAllWindows(): close all OpenCV windows
- 0xFF mask: untuk compatibility cross-platform (get lower 8 bits)

Image Format:
- OpenCV uses BGR (Blue, Green, Red) bukan RGB
- NumPy array shape: (height, width, channels)
- Data type: uint8 (0-255 untuk each channel)

Common Issues:
1. "No camera found":
   - Check hardware connection
   - Enable camera interface: sudo raspi-config
   - Check permissions: user harus di video group
   - Check device: ls /dev/video*

2. Low FPS:
   - Reduce resolution
   - Disable GUI (run headless)
   - Use hardware acceleration
   - Optimize processing code

3. Pi Camera not detected:
   - Update firmware: sudo apt update && sudo apt upgrade
   - Check ribbon cable connection
   - Test with: libcamera-hello

Performance Tips:
- Lower resolution = higher FPS (try 320x240 untuk fast processing)
- Hardware H.264 encoding available untuk Pi Camera
- Use threading untuk separate capture dan processing
- Consider using picamera2's capture arrays efficiently

Camera for Robot Applications:
- Object detection (faces, objects, traffic signs)
- Line following (detect line on floor)
- Color tracking (follow colored object)
- QR code reading
- Visual navigation
- Remote viewing (stream to web interface)
"""
