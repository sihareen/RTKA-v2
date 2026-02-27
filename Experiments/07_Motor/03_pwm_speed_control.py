#!/usr/bin/env python3
"""
Bab 7.3: Kontrol Arah dan Kecepatan (PWM)
==========================================
PWM (Pulse Width Modulation) untuk kontrol kecepatan motor

Konsep PWM:
- PWM = sinyal digital yang di-switch on/off dengan cepat
- Duty Cycle = persentase waktu "ON" dalam satu periode
- Duty 0% = motor mati, 100% = motor full speed
- Frekuensi PWM standar: 1000 Hz (tidak terdengar)

Contoh:
  Duty 25%: ▂▔▂▔▂▔▂▔  → Speed 25%
  Duty 50%: ▂▂▔▔▂▂▔▔  → Speed 50%
  Duty 75%: ▂▂▂▔▂▂▂▔  → Speed 75%

Hardware:
- Motor dengan L298N
- GPIO 17, 27 (Motor 1)
"""

from gpiozero import Motor
from time import sleep

motor = Motor(forward=17, backward=27)

print("="*60)
print("PWM Speed Control - Kontrol Kecepatan Motor")
print("="*60)

def demonstrate_pwm():
    """Demonstrasi berbagai speed dengan PWM"""
    
    print("\n📊 PWM Duty Cycle vs Speed:\n")
    
    speeds = [
        (0.2, "20%", "Sangat Pelan"),
        (0.4, "40%", "Pelan"),
        (0.6, "60%", "Sedang"),
        (0.8, "80%", "Cepat"),
        (1.0, "100%", "Maximum"),
    ]
    
    for speed, percentage, description in speeds:
        print(f"Speed {percentage:5s} ({description:15s})", end="")
        print(f" {'█' * int(speed*20)}")
        motor.forward(speed)
        sleep(2)
    
    motor.stop()
    print()

def smooth_acceleration():
    """Percepatan halus dari 0 → 100%"""
    print("\n🚀 Smooth Acceleration (0% → 100%):")
    
    for speed in range(0, 101, 5):
        speed_decimal = speed / 100.0
        bar = '█' * (speed // 5)
        print(f"\rSpeed: {speed:3d}% [{bar:20s}]", end="", flush=True)
        motor.forward(speed_decimal)
        sleep(0.2)
    
    print()  # New line
    sleep(1)
    motor.stop()

def smooth_deceleration():
    """Perlambatan halus dari 100% → 0"""
    print("\n🛑 Smooth Deceleration (100% → 0%):")
    
    for speed in range(100, -1, -5):
        speed_decimal = speed / 100.0
        bar = '█' * (speed // 5)
        print(f"\rSpeed: {speed:3d}% [{bar:20s}]", end="", flush=True)
        motor.forward(speed_decimal)
        sleep(0.2)
    
    print()  # New line
    motor.stop()

def direction_with_speed():
    """Kontrol arah sekaligus kecepatan"""
    print("\n🔄 Direction + Speed Control:\n")
    
    # Forward slow
    print("Forward (slow 30%)")
    motor.forward(0.3)
    sleep(2)
    
    # Forward fast
    print("Forward (fast 80%)")
    motor.forward(0.8)
    sleep(2)
    
    # Decelerate
    print("Decelerating...")
    for s in range(80, 0, -10):
        motor.forward(s / 100.0)
        sleep(0.2)
    
    motor.stop()
    sleep(1)
    
    # Backward slow
    print("Backward (slow 30%)")
    motor.backward(0.3)
    sleep(2)
    
    # Backward fast
    print("Backward (fast 80%)")
    motor.backward(0.8)
    sleep(2)
    
    motor.stop()

try:
    print("\n📚 Teori PWM:")
    print("  - Frekuensi: 1000 Hz (1000 siklus/detik)")
    print("  - Periode: 1 ms (1/1000 detik)")
    print("  - Duty Cycle: 0-100%")
    print("  - Motor merespons rata-rata voltage\n")
    
    input("Tekan ENTER untuk demonstrasi PWM...\n")
    
    # Demo 1: Berbagai kecepatan
    demonstrate_pwm()
    sleep(1)
    
    # Demo 2: Smooth acceleration
    smooth_acceleration()
    sleep(1)
    
    # Demo 3: Smooth deceleration
    smooth_deceleration()
    sleep(1)
    
    # Demo 4: Direction + Speed
    direction_with_speed()
    
    print("\n" + "="*60)
    print("✅ Demonstrasi PWM selesai!")
    print("="*60)
    print("\n💡 Key Takeaways:")
    print("  1. PWM duty cycle menentukan kecepatan")
    print("  2. 0% = stop, 100% = full speed")
    print("  3. Smooth acceleration = better control")
    print("  4. Arah & speed bisa dikontrol bersamaan")

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
finally:
    motor.stop()
    print("\nMotor stopped")
