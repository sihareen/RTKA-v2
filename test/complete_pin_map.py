#!/usr/bin/env python3
"""
COMPLETE PIN ALLOCATION MAP - RTKAv2
Menampilkan SEMUA pin yang digunakan sistem
"""

import sys
sys.path.insert(0, '/home/pi/RTKAv2')
from config import *

print("="*70)
print("COMPLETE PIN ALLOCATION MAP - RTKAv2")
print("="*70)

# Kumpulkan semua pin
pin_map = {
    # Motor Pins
    PIN_FL_FWD: "Motor FL Forward (Front Left Maju)",
    PIN_FL_BWD: "Motor FL Backward (Front Left Mundur)",
    PIN_RL_FWD: "Motor RL Forward (Rear Left Maju)",
    PIN_RL_BWD: "Motor RL Backward (Rear Left Mundur)",
    PIN_FR_FWD: "Motor FR Forward (Front Right Maju) ⚠️",
    PIN_FR_BWD: "Motor FR Backward (Front Right Mundur)",
    PIN_RR_FWD: "Motor RR Forward (Rear Right Maju)",
    PIN_RR_BWD: "Motor RR Backward (Rear Right Mundur) 🚨",
    
    # Servo & Buzzer
    PIN_SERVO_PAN: "Servo Pan (Hardware PWM Ch0)",
    PIN_SERVO_TILT: "Servo Tilt (Hardware PWM Ch1)",
    PIN_BUZZER: "Buzzer (PWM)",
    
    # Sensors
    PIN_HCSR_TRIG: "Ultrasonic HC-SR04 Trigger",
    PIN_HCSR_ECHO: "Ultrasonic HC-SR04 Echo",
    PIN_LINE_LL: "Line Sensor Left-Left",
    PIN_LINE_L: "Line Sensor Left",
    PIN_LINE_M: "Line Sensor Middle",
    PIN_LINE_R: "Line Sensor Right",
    PIN_LINE_RR: "Line Sensor Right-Right",
    PIN_BFD_NEAR: "Emergency Near Sensor",
    PIN_BFD_CLAP: "Emergency Clap Sensor",
    
    # LEDs
    PIN_LED_R: "LED Red",
    PIN_LED_Y: "LED Yellow",
    PIN_LED_G: "LED Green"
}

# Sort by GPIO number
sorted_pins = sorted(pin_map.items())

print("\n┌──────────┬────────────────────────────────────────────────────┐")
print("│   GPIO   │                    FUNGSI                          │")
print("├──────────┼────────────────────────────────────────────────────┤")

for gpio, func in sorted_pins:
    print(f"│  {gpio:3d}     │ {func:<50} │")

print("└──────────┴────────────────────────────────────────────────────┘")

# Check for conflicts
print("\n🔍 CEK KONFLIK PIN:")
print("-"*70)

all_gpios = list(pin_map.keys())
duplicates = set([x for x in all_gpios if all_gpios.count(x) > 1])

if duplicates:
    print("❌ KONFLIK DITEMUKAN!")
    for gpio in sorted(duplicates):
        functions = [func for g, func in pin_map.items() if g == gpio]
        print(f"   GPIO {gpio} digunakan oleh:")
        for func in functions:
            print(f"     - {func}")
else:
    print("✓ Tidak ada konflik pin")

# Available GPIOs
print("\n📌 GPIO YANG MASIH TERSEDIA (untuk replacement):")
print("-"*70)

# GPIO yang bisa digunakan di RPi (exclude yang sudah terpakai)
all_available = [2, 3, 10, 16, 19, 27]  # Beberapa GPIO yang aman
used = set(all_gpios)
available = [g for g in all_available if g not in used]

if available:
    print(f"GPIO Available: {', '.join(map(str, sorted(available)))}")
else:
    print("Hampir semua GPIO sudah terpakai!")

print("\n⚠️  PIN YANG BERMASALAH (Reported by User):")
print("-"*70)
print(f"GPIO {PIN_RR_BWD:2d} (RR Backward) → Motor mundur terus (tidak terkontrol)")
print(f"GPIO {PIN_FR_FWD:2d} (FR Forward)  → Motor tidak bisa maju")

print("\n💡 REKOMENDASI FIX:")
print("-"*70)
print("1. QUICK FIX (Ganti Pin):")
print("   Edit config.py, ubah:")
print(f"     PIN_RR_BWD = 16  # Ganti dari {PIN_RR_BWD}")
print(f"     PIN_FR_FWD = 19  # Ganti dari {PIN_FR_FWD} (jika perlu)")
print()
print("2. HARDWARE FIX:")
print("   - Cabut semua kabel dari driver")
print("   - Test motor secara manual (tanpa driver)")
print("   - Ganti driver jika masih bermasalah")
print()
print("3. DIAGNOSTIC TEST:")
print("   Jalankan: python3 test/motor_wiring_test.py")
print("   Script ini akan test setiap pin secara individual")

print("\n" + "="*70)
print("NOTE: PIN_BUZZER = 116 kemungkinan typo!")
print("      GPIO 116 tidak ada di Raspberry Pi (max GPIO 27)")
print("      Seharusnya GPIO 16 atau ubah ke pin lain")
print("="*70)
