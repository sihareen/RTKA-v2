#!/usr/bin/env python3
"""
Bab 7.2: Motor Driver (L298N / Sejenis)
========================================
Memahami motor driver dan cara penggunaannya

Konsep Motor Driver:
- Motor driver adalah H-Bridge yang mengatur polaritas
- Enable pin (ENA/ENB) untuk PWM speed control
- Input pins (IN1-IN4) untuk kontrol arah
- Membutuhkan power supply terpisah (baterai/adaptor)

Wiring L298N:
┌─────────────┐
│   L298N     │
│             │
│ IN1 → GPIO17│  Motor A (Kiri)
│ IN2 → GPIO27│
│ ENA → 5V    │  (atau GPIO untuk PWM)
│             │
│ IN3 → GPIO22│  Motor B (Kanan)
│ IN4 → GPIO23│
│ ENB → 5V    │
│             │
│ VCC → 12V   │  (dari baterai)
│ GND → GND   │
└─────────────┘

Hardware:
- 2x Motor DC
- L298N Motor Driver
- 12V Battery
- GPIO connections
"""

from gpiozero import Motor
from time import sleep

# Setup 2 motors (Left & Right)
motor_left = Motor(forward=17, backward=27)
motor_right = Motor(forward=22, backward=23)

print("="*60)
print("Motor Driver L298N - Dual Motor Control")
print("="*60)

def test_motor_driver():
    """Test motor driver dengan 2 motor"""
    
    print("\n[TEST 1] Motor Kiri - Forward")
    print("IN1=HIGH, IN2=LOW")
    motor_left.forward(0.5)
    sleep(2)
    motor_left.stop()
    sleep(1)
    
    print("\n[TEST 2] Motor Kanan - Forward")
    print("IN3=HIGH, IN4=LOW")
    motor_right.forward(0.5)
    sleep(2)
    motor_right.stop()
    sleep(1)
    
    print("\n[TEST 3] Kedua Motor - Forward (Robot Maju)")
    motor_left.forward(0.5)
    motor_right.forward(0.5)
    sleep(2)
    motor_left.stop()
    motor_right.stop()
    sleep(1)
    
    print("\n[TEST 4] Pivot Turn - Kiri")
    print("Motor Kiri Mundur, Motor Kanan Maju")
    motor_left.backward(0.5)
    motor_right.forward(0.5)
    sleep(1.5)
    motor_left.stop()
    motor_right.stop()
    sleep(1)
    
    print("\n[TEST 5] Pivot Turn - Kanan")
    print("Motor Kiri Maju, Motor Kanan Mundur")
    motor_left.forward(0.5)
    motor_right.backward(0.5)
    sleep(1.5)
    motor_left.stop()
    motor_right.stop()

def diagnose_motor_driver():
    """Diagnostic untuk troubleshooting"""
    print("\n" + "="*60)
    print("DIAGNOSTIC MODE")
    print("="*60)
    print("\n✓ Checklist:")
    print("  [1] Apakah LED power di L298N menyala?")
    print("  [2] Apakah kabel motor terpasang dengan benar?")
    print("  [3] Apakah ENA/ENB terhubung (jumper atau 5V)?")
    print("  [4] Apakah GND Raspberry Pi terhubung ke GND L298N?")
    print("  [5] Apakah voltage baterai cukup (minimal 7V)?")
    print("\n⚠️  Troubleshooting:")
    print("  - Motor tidak berputar? → Cek connection & battery")
    print("  - Motor lemah? → Battery low atau wiring resistance")
    print("  - Motor berputar terbalik? → Swap motor wires")
    print("  - Hanya 1 motor jalan? → Cek wiring IN1-IN4")

try:
    print("\n📚 Tentang L298N:")
    print("- Dual H-Bridge motor driver")
    print("- Dapat kontrol 2 motor DC / 1 stepper motor")
    print("- Input voltage: 5V-35V")
    print("- Max output current: 2A per channel")
    print("- Built-in 5V regulator (untuk logic)")
    print()
    
    input("Tekan ENTER untuk memulai test motor driver...")
    
    test_motor_driver()
    
    print("\n✅ Test selesai!")
    
    diagnose_motor_driver()

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
finally:
    motor_left.stop()
    motor_right.stop()
    print("\nSemua motor stopped")
