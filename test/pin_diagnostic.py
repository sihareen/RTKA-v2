#!/usr/bin/env python3
"""
PIN DIAGNOSTIC TOOL - RTKAv2
Untuk mengecek status pin dan menguji motor satu per satu
"""

import sys
import time
from gpiozero import Motor, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Setup Pin Factory
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
    print("✓ LGPIOFactory initialized (RPi 5 compatible)")
except Exception as e:
    print(f"⚠ Warning: {e}")

# Import config
sys.path.insert(0, '/home/pi/RTKAv2')
from config import *

print("="*60)
print("PIN DIAGNOSTIC TOOL - RTKAv2")
print("="*60)

# ==========================================
# 1. TAMPILKAN KONFIGURASI PIN SAAT INI
# ==========================================
print("\n📌 KONFIGURASI PIN MOTOR (dari config.py):")
print("-"*60)
print("SISI KIRI (Driver 1):")
print(f"  Front Left  FWD: GPIO {PIN_FL_FWD:2d}  |  BWD: GPIO {PIN_FL_BWD:2d}")
print(f"  Rear Left   FWD: GPIO {PIN_RL_FWD:2d}  |  BWD: GPIO {PIN_RL_BWD:2d}")
print("\nSISI KANAN (Driver 2):")
print(f"  Front Right FWD: GPIO {PIN_FR_FWD:2d}  |  BWD: GPIO {PIN_FR_BWD:2d}")
print(f"  Rear Right  FWD: GPIO {PIN_RR_FWD:2d}  |  BWD: GPIO {PIN_RR_BWD:2d}")

# ==========================================
# 2. CEK KONFLIK PIN
# ==========================================
print("\n🔍 CEK KONFLIK PIN:")
print("-"*60)
all_pins = [PIN_FL_FWD, PIN_FL_BWD, PIN_RL_FWD, PIN_RL_BWD,
            PIN_FR_FWD, PIN_FR_BWD, PIN_RR_FWD, PIN_RR_BWD]
pin_names = ["FL_FWD", "FL_BWD", "RL_FWD", "RL_BWD",
             "FR_FWD", "FR_BWD", "RR_FWD", "RR_BWD"]

duplicates = []
for i, pin in enumerate(all_pins):
    count = all_pins.count(pin)
    if count > 1:
        duplicates.append((pin, pin_names[i]))

if duplicates:
    print("❌ KONFLIK TERDETEKSI!")
    seen = set()
    for pin, name in duplicates:
        if pin not in seen:
            conflicting = [n for p, n in zip(all_pins, pin_names) if p == pin]
            print(f"   GPIO {pin:2d} digunakan oleh: {', '.join(conflicting)}")
            seen.add(pin)
else:
    print("✓ Tidak ada konflik pin")

# ==========================================
# 3. ANALISIS MASALAH USER
# ==========================================
print("\n🚨 ANALISIS MASALAH YANG DILAPORKAN:")
print("-"*60)
print(f"Masalah 1: GPIO 6 terus mundur")
print(f"  → GPIO 6 = PIN_RR_BWD (Rear Right Backward)")
print(f"  → Kemungkinan: Motor RR terbalik atau driver error")
print()
print(f"Masalah 2: GPIO 24 tidak bisa maju")
print(f"  → GPIO 24 = PIN_FR_FWD (Front Right Forward)")
print(f"  → Kemungkinan: Kabel lepas, motor rusak, atau driver error")

# ==========================================
# 4. UJI MOTOR SATU PER SATU
# ==========================================
print("\n⚙️  UJI MOTOR INDIVIDU")
print("-"*60)
print("Setiap motor akan diuji Forward → Backward → Stop")
print("Perhatikan apakah arah putaran sesuai!")
print()

def test_motor(name, fwd_pin, bwd_pin, duration=1.5):
    """Test satu motor secara individual"""
    print(f"\n🔧 Testing {name} (FWD:{fwd_pin}, BWD:{bwd_pin})")
    try:
        motor = Motor(forward=fwd_pin, backward=bwd_pin)
        
        # Test Forward
        print(f"   → FORWARD (GPIO {fwd_pin}) ... ", end="", flush=True)
        motor.forward(speed=0.5)
        time.sleep(duration)
        motor.stop()
        time.sleep(0.3)
        print("OK")
        
        # Test Backward
        print(f"   → BACKWARD (GPIO {bwd_pin}) ... ", end="", flush=True)
        motor.backward(speed=0.5)
        time.sleep(duration)
        motor.stop()
        time.sleep(0.3)
        print("OK")
        
        motor.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

# Tanya user apakah mau test
response = input("\nJalankan test motor? (y/n): ").strip().lower()

if response == 'y':
    print("\n" + "="*60)
    print("MULAI TESTING MOTOR")
    print("="*60)
    
    test_motor("Front Left (FL)",  PIN_FL_FWD, PIN_FL_BWD)
    test_motor("Rear Left (RL)",   PIN_RL_FWD, PIN_RL_BWD)
    test_motor("Front Right (FR)", PIN_FR_FWD, PIN_FR_BWD)
    test_motor("Rear Right (RR)",  PIN_RR_FWD, PIN_RR_BWD)
    
    print("\n" + "="*60)
    print("TESTING SELESAI")
    print("="*60)

# ==========================================
# 5. REKOMENDASI
# ==========================================
print("\n💡 REKOMENDASI:")
print("-"*60)
print("1. Jika motor berputar TERBALIK:")
print("   → Tukar pin FWD dan BWD di config.py")
print()
print("2. Jika motor TIDAK BERPUTAR sama sekali:")
print("   → Cek kabel di breadboard/driver")
print("   → Cek power supply motor driver")
print("   → Cek apakah motor rusak (test manual)")
print()
print("3. Untuk GPIO 6 (RR_BWD) yang jalan sendiri:")
print("   → Kemungkinan floating pin atau driver short")
print("   → Coba tukar dengan pin lain")
print()
print("4. Untuk GPIO 24 (FR_FWD) yang tidak jalan:")
print("   → Cek kabel jumper dari Pi ke driver")
print("   → Ukur voltage di pin GPIO (harus 3.3V saat HIGH)")
print("   → Test dengan LED untuk pastikan pin output berfungsi")
print()
print("="*60)
print("Script selesai!")
print("="*60)
