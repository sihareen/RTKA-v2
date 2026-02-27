#!/usr/bin/env python3
"""
Bab 7.1: Motor DC dan Prinsip Kerja
===================================
Memahami cara kerja motor DC dan kontrol dasar

Konsep:
- Motor DC berputar saat dialiri arus listrik
- Arah putaran ditentukan oleh polaritas arus
- Motor driver diperlukan untuk kontrol dari GPIO

Hardware:
- Motor DC
- Motor Driver (L298N/TB6612)
- Power supply terpisah untuk motor
- GPIO 17 (Forward), 27 (Backward)
"""

from gpiozero import Motor
from time import sleep

# Setup motor
motor = Motor(forward=17, backward=27)

print("="*50)
print("Motor DC - Prinsip Kerja")
print("="*50)
print("\nKonsep:")
print("1. GPIO HIGH pada pin Forward → Motor maju")
print("2. GPIO HIGH pada pin Backward → Motor mundur")
print("3. Kedua LOW → Motor stop")
print("4. Motor driver mengamplifikasi sinyal GPIO\n")
print("="*50)

def demonstrate_motor():
    """Demonstrasi cara kerja motor DC"""
    
    # 1. Motor Maju
    print("\n[1] Motor FORWARD")
    print("    → GPIO 17 = HIGH, GPIO 27 = LOW")
    motor.forward(speed=0.5)  # 50% speed
    sleep(2)
    motor.stop()
    sleep(1)
    
    # 2. Motor Mundur
    print("\n[2] Motor BACKWARD")
    print("    → GPIO 17 = LOW, GPIO 27 = HIGH")
    motor.backward(speed=0.5)
    sleep(2)
    motor.stop()
    sleep(1)
    
    # 3. Motor Stop
    print("\n[3] Motor STOP")
    print("    → GPIO 17 = LOW, GPIO 27 = LOW")
    motor.stop()
    sleep(1)
    
    # 4. Variable Speed (PWM)
    print("\n[4] Variable Speed dengan PWM")
    print("    → PWM duty cycle mengatur kecepatan")
    
    for speed in [0.3, 0.5, 0.7, 1.0]:
        print(f"    Speed: {speed*100:.0f}%")
        motor.forward(speed)
        sleep(1)
    
    motor.stop()

try:
    print("\nMemulai demonstrasi...")
    print("Tekan Ctrl+C untuk berhenti\n")
    sleep(1)
    
    demonstrate_motor()
    
    print("\n" + "="*50)
    print("Demonstrasi selesai!")
    print("="*50)
    print("\n📝 Catatan:")
    print("- Motor driver melindungi GPIO dari arus tinggi")
    print("- PWM mengatur kecepatan tanpa mengubah voltage")
    print("- Frekuensi PWM standar: 1000 Hz")
    
except KeyboardInterrupt:
    print("\n\nProgram dihentikan oleh user")
finally:
    motor.stop()
    print("Motor stopped & GPIO released")
