#!/usr/bin/env python3
"""
Bab 19: Test Sensor Fusion - Basic
===================================
Program sederhana untuk test sensor fusion
Kombinasi: Camera + Ultrasonic

Hardware:
- Camera
- HC-SR04 Ultrasonic
"""

import cv2
import time
from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*50)
print("Test Sensor Fusion - Basic")
print("="*50)

try:
    camera = cv2.VideoCapture(0)
    ultrasonic = DistanceSensor(echo=6, trigger=5, max_distance=4)
    print("✅ Camera & Ultrasonic initialized")
except Exception as e:
    print(f"❌ Hardware error: {e}")
    exit(1)

print("\nSensor fusion active (10s)")
print("Combining camera + ultrasonic data\n")

start_time = time.time()
fusion_count = 0

try:
    while (time.time() - start_time) < 10:
        ret, frame = camera.read()
        distance = ultrasonic.distance * 100
        
        if not ret:
            continue
        
        fusion_count += 1
        
        cv2.putText(frame, f"Distance: {distance:.1f} cm", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        if distance < 30:
            color = (0, 0, 255)
            status = "OBSTACLE CLOSE!"
        elif distance < 60:
            color = (0, 255, 255)
            status = "Caution"
        else:
            color = (0, 255, 0)
            status = "Clear"
        
        cv2.putText(frame, status, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        bar_length = int(min(distance, 100) * 5)
        cv2.rectangle(frame, (10, 100), (bar_length, 120), color, -1)
        
        cv2.imshow('Sensor Fusion Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"\n✅ Test selesai!")
    print(f"   Fusion frames: {fusion_count}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

finally:
    camera.release()
    cv2.destroyAllWindows()

"""
PENJELASAN PROGRAM:
==================
Program ini demonstrates sensor fusion - combining data dari multiple sensors (camera
dan ultrasonic) untuk enhanced perception dan decision making.

Sensor Fusion:
Sensor fusion adalah proses menggabungkan data dari multiple sensors untuk produce more
accurate dan reliable information daripada menggunakan single sensor.

Keuntungan Sensor Fusion:
1. Redundancy: jika satu sensor fail, masih ada backup
2. Complementary: sensors cover each other's weaknesses
3. Accuracy: combining measurements reduce errors
4. Robustness: less affected oleh individual sensor limitations

Types of Sensor Fusion:
1. Complementary:
   - Sensors measure different aspects dari environment
   - Contoh: camera (visual) + ultrasonic (distance)
   - This program uses complementary fusion

2. Competitive:
   - Multiple sensors measure sama thing
   - Voting atau averaging untuk reliability
   - Contoh: 3 ultrasonic sensors measuring same distance

3. Cooperative:
   - Sensors work together untuk derive information
   - Neither sensor alone could provide 
   - Contoh: stereo vision (2 cameras untuk depth)

Camera vs Ultrasonic:

Camera Strengths:
+ Rich visual information (colors, shapes, textures)
+ Identify specific objects (face, sign, color)
+ Wide field of view
+ Passive sensor (no emissions)

Camera Weaknesses:
- Tidak direct distance measurement
- Affected by lighting conditions
- Compute intensive processing
- Calibration required untuk depth

Ultrasonic Strengths:
+ Direct distance measurement
+ Works di darkness
+ Simple dan reliable
+ Low computational cost
+ Tidak affected oleh colors/textures

Ultrasonic Weaknesses:
- No visual information
- Narrow field of view (~15 degrees)
- Affected by surface angles
- Limited range (~4 meters)
- Can have specular reflections

Fusion Strategy (Program Ini):
1. Camera provides visual context
2. Ultrasonic provides accurate distance
3. Overlay distance data pada video feed
4. Color-coded status based on distance:
   - Red (<30cm): Obstacle sangat dekat
   - Yellow (30-60cm): Caution zone
   - Green (>60cm): Safe distance

Real-world Fusion Applications:

1. Autonomous Vehicles:
   - Camera: lane detection, sign recognition, object classification
   - LIDAR: precise 3D mapping
   - Radar: long-range detection, speed measurement
   - Ultrasonic: parking assistance
   - IMU: vehicle motion dan orientation
   - GPS: global positioning

2. Drones:
   - Camera: visual navigation
   - IMU: orientation
   - Barometer: altitude
   - GPS: position
   - Ultrasonic: height above ground

3. Robotics:
   - Camera: object recognition
   - Ultrasonic/LIDAR: obstacle avoidance
   - IMU: orientation
   - Encoders: wheel rotation
   - Force sensors: grip strength

Fusion Algorithms:

1. Kalman Filter:
   - Optimal untuk linear systems dengan Gaussian noise
   - Predict + Update cycle
   - Widely used untuk sensor fusion

2. Extended Kalman Filter (EKF):
   - For non-linear systems
   - Linearization via Taylor series

3. Particle Filter:
   - For non-Gaussian distributions
   - Monte Carlo sampling

4. Bayesian Networks:
   - Probabilistic reasoning
   - Handle uncertainty

5. Deep Learning:
   - Neural networks learn fusion strategy
   - End-to-end learning dari raw sensor data

Program Implementation:

1. Hardware Setup:
   - Camera: visual sensor
   - Ultrasonic: distance sensor
   - Both running simultaneously

2. Data Acquisition:
   - Camera: 30 FPS video frames
   - Ultrasonic: ~10 Hz distance readings
   - Different sampling rates (asynchronous fusion)

3. Data Integration:
   - Overlay ultrasonic distance pada camera frame
   - Synchronize by matching timestamps
   - Visual representation dengan color coding

4. Decision Making:
   - Distance thresholds untuk status
   - Visual feedback untuk operator/system
   - Could trigger actions (stop robot, warning, etc)

Enhancements Possible:
1. Add more sensors:
   - Multiple ultrasonics (front, sides, back)
   - IMU untuk orientation
   - IR sensors untuk close-range
   - Gyroscope untuk motion

2. Advanced processing:
   - Kalman filter untuk smooth distance readings
   - Object detection pada camera untuk identify obstacles
   - 3D reconstruction dari stereo camera + distance

3. Data logging:
   - Record sensor data untuk analysis
   - Training data untuk machine learning
   - Debugging dan optimization

4. Real-time decision making:
   - Automatic obstacle avoidance
   - Adaptive speed control
   - Path planning

Challenges in Sensor Fusion:
1. Time synchronization (sensors run at different rates)
2. Coordinate frame alignment (sensors di different positions)
3. Calibration (ensuring accuracy)
4. Computational cost (processing multiple streams)
5. Sensor degradation over time
6. Environmental conditions affecting sensors differently

This program adalah foundation untuk more complex multi-sensor systems commonly
used di autonomous robots, self-driving cars, dan intelligent systems.
"""
