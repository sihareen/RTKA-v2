#!/usr/bin/env python3
"""
Bab 07: Test Motor DC - Basic
==============================
Program sederhana untuk test motor DC

Hardware:
- Raspberry Pi
- L298N Motor Driver
- DC Motor (2 buah)

Wiring:
- Motor Left FWD: GPIO 17
- Motor Left BWD: GPIO 27
- Motor Right FWD: GPIO 23
- Motor Right BWD: GPIO 24
"""

from gpiozero import Motor
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
import time

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*50)
print("Test Motor DC - Basic")
print("="*50)

try:
    motor_left = Motor(forward=17, backward=27)
    motor_right = Motor(forward=23, backward=24)
    
    print("\n✅ Motor initialized")
    print("\nTest sequence:")
    
    print("1. Forward (2s)")
    motor_left.forward(0.5)
    motor_right.forward(0.5)
    time.sleep(2)
    
    print("2. Backward (2s)")
    motor_left.backward(0.5)
    motor_right.backward(0.5)
    time.sleep(2)
    
    print("3. Turn Left (1s)")
    motor_left.backward(0.5)
    motor_right.forward(0.5)
    time.sleep(1)
    
    print("4. Turn Right (1s)")
    motor_left.forward(0.5)
    motor_right.backward(0.5)
    time.sleep(1)
    
    print("5. Stop")
    motor_left.stop()
    motor_right.stop()
    
    print("\n✅ Test selesai!")
    
except Exception as e:
    print(f"❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini adalah test dasar untuk motor DC pada robot RTKA. Program menggunakan library
gpiozero untuk mengontrol 2 buah motor DC melalui motor driver L298N.

Cara Kerja:
1. Import library gpiozero.Motor untuk kontrol motor DC dengan 2 pin (forward/backward)
2. Set pin factory ke LGPIOFactory untuk menggunakan lgpio sebagai backend GPIO yang lebih
   modern dan stabil dibanding RPi.GPIO
3. Inisialisasi 2 motor:
   - Motor kiri: GPIO 17 (forward) dan GPIO 27 (backward)
   - Motor kanan: GPIO 23 (forward) dan GPIO 24 (backward)
4. Jalankan test sequence:
   - Forward: kedua motor maju dengan speed 0.5 (50% PWM duty cycle) selama 2 detik
   - Backward: kedua motor mundur dengan speed 0.5 selama 2 detik  
   - Turn Left: motor kiri mundur, motor kanan maju (spot turn) selama 1 detik
   - Turn Right: motor kiri maju, motor kanan mundur (spot turn) selama 1 detik
   - Stop: hentikan kedua motor

Konsep Penting:
- Motor DC berputar saat dialiri arus listrik, arah putaran ditentukan oleh polaritas
- Motor driver (L298N) diperlukan karena GPIO hanya output 3.3V/16mA, tidak cukup untuk
  drive motor yang butuh voltage dan current lebih tinggi
- PWM (Pulse Width Modulation) digunakan untuk kontrol kecepatan motor. Speed 0.5 = 50%
  duty cycle, artinya signal HIGH 50% dari waktu, LOW 50% waktu
- Differential drive: dengan mengatur kecepatan dan arah kedua motor secara independen,
  robot bisa maju, mundur, belok, dan berputar di tempat (spot turn)

Error Handling:
- Try-except digunakan untuk catch error saat inisialisasi atau operasi motor
- Pin factory fallback ke default jika lgpio tidak tersedia di sistem
"""
