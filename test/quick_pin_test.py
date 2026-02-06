#!/usr/bin/env python3
"""
QUICK PIN TEST - Khusus untuk GPIO 6 dan GPIO 24
Test cepat untuk diagnosa masalah
"""

import time
from gpiozero import OutputDevice, Device
from gpiozero.pins.lgpio import LGPIOFactory

# Setup
try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*60)
print("QUICK PIN TEST - GPIO 6 & GPIO 24")
print("="*60)

# Test GPIO 24 (FR Forward yang tidak jalan)
print("\n🔍 TEST GPIO 24 (Front Right Forward):")
print("-"*60)
try:
    pin24 = OutputDevice(24)
    
    for i in range(5):
        print(f"  Cycle {i+1}: ON ... ", end="", flush=True)
        pin24.on()
        time.sleep(0.5)
        print("OFF")
        pin24.off()
        time.sleep(0.5)
    
    pin24.close()
    print("✓ GPIO 24 test selesai (cek apakah motor maju?)")
    
except Exception as e:
    print(f"❌ ERROR GPIO 24: {e}")

# Test GPIO 6 (RR Backward yang jalan terus)
print("\n🔍 TEST GPIO 6 (Rear Right Backward):")
print("-"*60)
try:
    pin6 = OutputDevice(6)
    
    print("  Memastikan pin LOW (OFF)...")
    pin6.off()
    time.sleep(2)
    
    print("  Pin masih aktif? Cek motor rear right!")
    time.sleep(2)
    
    print("\n  Test ON/OFF 5x:")
    for i in range(5):
        print(f"  Cycle {i+1}: ON ... ", end="", flush=True)
        pin6.on()
        time.sleep(0.5)
        print("OFF")
        pin6.off()
        time.sleep(0.5)
    
    pin6.close()
    print("✓ GPIO 6 test selesai")
    
except Exception as e:
    print(f"❌ ERROR GPIO 6: {e}")

print("\n" + "="*60)
print("HASIL:")
print("="*60)
print("GPIO 24: Jika motor FR tidak bergerak sama sekali")
print("         → Kabel lepas / motor rusak / driver mati")
print()
print("GPIO 6:  Jika motor RR tetap mundur walau pin OFF")
print("         → Driver short / motor driver rusak")
print("         → Coba lepas kabel dari driver lalu test lagi")
print("="*60)
