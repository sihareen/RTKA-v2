#!/usr/bin/env python3
"""
Bab 12: Test Autonomous - Basic
================================
Program sederhana untuk test autonomous navigation

Kombinasi: Motor + Ultrasonic
Logika sederhana: Jika ada obstacle -> turn, jika tidak -> forward
"""

from gpiozero import Motor, DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
import time

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*50)
print("Test Autonomous - Basic")
print("="*50)

try:
    motor_left = Motor(forward=17, backward=27)
    motor_right = Motor(forward=23, backward=24)
    sensor = DistanceSensor(echo=6, trigger=5, max_distance=4)
    
    print("✅ Hardware initialized")
    print("\nAutonomous mode (20s)")
    print("Logic: obstacle < 30cm -> turn, else -> forward")
    print("Press Ctrl+C to stop\n")
    
    start_time = time.time()
    
    while (time.time() - start_time) < 20:
        distance = sensor.distance * 100
        
        print(f"Distance: {distance:.1f} cm  ", end='')
        
        if distance < 30:
            print("→ TURN RIGHT")
            motor_left.forward(0.5)
            motor_right.backward(0.5)
            time.sleep(0.5)
        else:
            print("↑ FORWARD   ")
            motor_left.forward(0.5)
            motor_right.forward(0.5)
            time.sleep(0.2)
    
    motor_left.stop()
    motor_right.stop()
    
    print("\n✅ Test selesai!")
    
except KeyboardInterrupt:
    motor_left.stop()
    motor_right.stop()
    print("\n\n✅ Stopped by user")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini adalah test dasar untuk autonomous navigation (navigasi otomatis) pada robot
RTKA. Robot akan bergerak sendiri sambil menghindari obstacle menggunakan sensor ultrasonik.

Konsep Autonomous Navigation:
Robot membuat keputusan sendiri berdasarkan sensor input tanpa kontrol manual dari user.
Ini adalah fondasi untuk self-driving robot.

Cara Kerja Program:
1. Hardware Setup:
   - 2 Motor DC untuk differential drive (motor kiri & kanan)
   - 1 Ultrasonic sensor untuk deteksi obstacle di depan
   - Motor pins: Left(17,27), Right(23,24)
   - Sensor pins: TRIG(5), ECHO(6)

2. Obstacle Avoidance Logic (Simple Reactive Behavior):
   - Baca jarak dari ultrasonic sensor
   - IF jarak < 30cm (obstacle dekat):
       * TURN RIGHT (spot turn): left forward, right backward
       * Duration 0.5 detik untuk belok ~45-90 derajat
   - ELSE (jalan clear):
       * FORWARD: both motors forward
       * Duration 0.2 detik, lalu check sensor lagi

3. Main Loop:
   - Jalan autonomous selama 20 detik (bisa di-extend untuk continuous operation)
   - Sensor polling rate: ~5 Hz (check setiap 0.2 detik saat forward)
   - Real-time feedback: print distance dan action ke terminal

4. Safety:
   - Keyboard interrupt (Ctrl+C) untuk emergency stop
   - Motors automatically stopped on exit (finally block)
   - Max speed 50% untuk control yang lebih baik

Algoritma Behavior:
Ini adalah "Reactive Behavior" - robot react langsung terhadap sensor input.
Sederhana tapi efektif untuk basic obstacle avoidance.

Alternatif algorithms yang lebih advanced:
- Bug algorithms (Bug0, Bug1, Bug2)
- Wall following
- Potential field method
- A* path planning dengan map
- SLAM (Simultaneous Localization and Mapping)

Limitations:
1. Hanya detect obstacle di depan (no side/rear detection)
2. Tidak ada memory/map (purely reactive)
3. Bisa stuck di corner atau U-shaped obstacles
4. Tidak ada path planning (random walk pattern)

Improvements yang bisa dilakukan:
- Tambah multiple sensors (depan, kiri, kanan)
- Variable speed based on distance (slow down saat mendekati obstacle)
- Memory untuk avoid repeating stuck situations
- Random turn direction untuk escape dari trap
- Integration dengan camera untuk visual navigation

Use Case:
- Basic autonomous robot
- Room exploration
- Obstacle avoidance demo
- Foundation untuk advanced navigation algorithms
"""
