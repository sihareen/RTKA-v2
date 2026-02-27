#!/usr/bin/env python3
"""
Bab 08: Test Ultrasonic Sensor - Basic
=======================================
Program sederhana untuk test sensor ultrasonik HC-SR04

Hardware:
- HC-SR04 Ultrasonic Sensor

Wiring:
- TRIG: GPIO 5
- ECHO: GPIO 6
- VCC: 5V
- GND: GND
"""

from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
import time

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*50)
print("Test Ultrasonic Sensor - Basic")
print("="*50)

try:
    sensor = DistanceSensor(echo=6, trigger=5, max_distance=4)
    
    print("✅ Sensor initialized")
    print("\nMengukur jarak... (Press Ctrl+C to stop)\n")
    
    while True:
        distance_cm = sensor.distance * 100
        
        bar_length = int(min(distance_cm, 100) / 5)
        bar = "█" * bar_length
        
        print(f"Jarak: {distance_cm:6.1f} cm  {bar}", end='\r')
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\n✅ Test selesai!")
except Exception as e:
    print(f"\n❌ Error: {e}")

"""
PENJELASAN PROGRAM:
==================
Program ini untuk test sensor ultrasonik HC-SR04 yang digunakan untuk mengukur jarak
pada robot RTKA.

Cara Kerja Sensor HC-SR04:
1. Program mengirim trigger pulse (10μs HIGH signal) ke pin TRIG
2. Sensor memancarkan 8 burst gelombang ultrasonik 40kHz
3. Gelombang memantul dari objek dan kembali ke sensor
4. Sensor menerima echo dan mengaktifkan pin ECHO HIGH
5. Durasi ECHO HIGH = waktu tempuh pulang-pergi gelombang
6. Jarak dihitung: distance = (waktu × kecepatan_suara) / 2
   Kecepatan suara ~343 m/s pada suhu ruangan

Implementasi Program:
- Menggunakan gpiozero.DistanceSensor yang sudah handle timing dan kalkulasi otomatis
- GPIO 5 untuk TRIG (trigger pin)
- GPIO 6 untuk ECHO (echo pin)
- max_distance=4 meter adalah range maksimum sensor
- sensor.distance return nilai dalam meter (0.0 - 4.0)
- Konversi ke cm dengan * 100 untuk display yang lebih intuitif

Visualisasi:
- Program menampilkan jarak dalam cm dengan bar visualization
- Bar length proporsional dengan jarak (1 karakter = 5cm)
- Update 10 Hz (setiap 100ms) untuk real-time monitoring
- Output di-overwrite pada line yang sama menggunakan '\r' untuk efek live update

Keuntungan Ultrasonic Sensor:
- Murah dan mudah digunakan
- Akurat untuk jarak 2cm - 400cm
- Tidak terpengaruh warna atau transparansi objek (beda dengan IR sensor)
- Cocok untuk obstacle avoidance dan navigation
"""
