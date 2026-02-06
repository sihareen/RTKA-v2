#!/usr/bin/env python3
"""
MOTOR WIRING TEST - Isolasi Masalah GPIO 6 dan GPIO 24
"""

import time
from gpiozero import Motor, OutputDevice, Device
from gpiozero.pins.lgpio import LGPIOFactory

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*70)
print("MOTOR WIRING TEST - DIAGNOSA MASALAH")
print("="*70)

# ==========================================
# TEST 1: GPIO 24 (FR Forward)
# ==========================================
print("\n📍 TEST 1: GPIO 24 (Front Right Forward)")
print("-"*70)
print("Instruksi: Perhatikan apakah RODA DEPAN KANAN bergerak MAJU")
print()

input("Tekan ENTER untuk mulai test GPIO 24...")

try:
    pin24 = OutputDevice(24)
    
    print("\n  → Mengaktifkan GPIO 24 selama 3 detik...")
    pin24.on()
    time.sleep(3)
    pin24.off()
    
    pin24.close()
    
    print("\n  Apakah roda depan kanan (FR) bergerak MAJU?")
    result = input("  Jawab (y/n): ").strip().lower()
    
    if result == 'y':
        print("  ✓ GPIO 24 NORMAL - Pin dan driver OK")
        print("  ⚠ Jika motor tidak kuat, cek power supply atau motor rusak")
    else:
        print("  ✗ GPIO 24 BERMASALAH")
        print("  Kemungkinan:")
        print("    1. Kabel GPIO 24 lepas dari driver")
        print("    2. Driver channel IN3 rusak")
        print("    3. Motor FR putus")
        
except Exception as e:
    print(f"  ✗ ERROR: {e}")

# ==========================================
# TEST 2: GPIO 25 (FR Backward)
# ==========================================
print("\n📍 TEST 2: GPIO 25 (Front Right Backward)")
print("-"*70)
print("Instruksi: Perhatikan apakah RODA DEPAN KANAN bergerak MUNDUR")
print()

input("Tekan ENTER untuk mulai test GPIO 25...")

try:
    pin25 = OutputDevice(25)
    
    print("\n  → Mengaktifkan GPIO 25 selama 3 detik...")
    pin25.on()
    time.sleep(3)
    pin25.off()
    
    pin25.close()
    
    print("\n  Apakah roda depan kanan (FR) bergerak MUNDUR?")
    result = input("  Jawab (y/n): ").strip().lower()
    
    if result == 'y':
        print("  ✓ GPIO 25 NORMAL")
        print("  💡 Kesimpulan: Motor FR OK, hanya GPIO 24 bermasalah")
    else:
        print("  ✗ GPIO 25 JUGA BERMASALAH")
        print("  💡 Kesimpulan: Kemungkinan besar driver channel mati")
        
except Exception as e:
    print(f"  ✗ ERROR: {e}")

# ==========================================
# TEST 3: GPIO 6 (RR Backward) - Idle Test
# ==========================================
print("\n📍 TEST 3: GPIO 6 (Rear Right Backward) - IDLE TEST")
print("-"*70)
print("Test ini untuk cek apakah GPIO 6 'bocor' (jalan sendiri)")
print()

input("Tekan ENTER untuk mulai test GPIO 6...")

try:
    pin6 = OutputDevice(6)
    
    print("\n  → Memastikan GPIO 6 dalam kondisi OFF...")
    pin6.off()
    
    print("  → Tunggu 5 detik, perhatikan roda belakang kanan...")
    for i in range(5, 0, -1):
        print(f"     {i}...", end=" ", flush=True)
        time.sleep(1)
    
    print("\n\n  Apakah roda belakang kanan (RR) bergerak MUNDUR?")
    result = input("  Jawab (y/n): ").strip().lower()
    
    if result == 'y':
        print("  ✗ MASALAH TERDETEKSI!")
        print("  💡 GPIO 6 aktif walau seharusnya OFF")
        print("\n  Penyebab:")
        print("    1. Driver channel short (IN4 terhubung langsung ke VCC)")
        print("    2. Kabel GPIO 6 terjepit/short dengan kabel lain")
        print("    3. Motor driver rusak (ganti driver)")
        print("\n  Solusi Sementara:")
        print("    Ganti PIN_RR_BWD di config.py:")
        print("    PIN_RR_BWD = 16  # Atau pin lain yang available")
    else:
        print("  ✓ GPIO 6 NORMAL saat OFF")
        
    # Test ON
    print("\n  → Test GPIO 6 ON (motor harus mundur lebih kencang)...")
    pin6.on()
    time.sleep(2)
    pin6.off()
    
    pin6.close()
    
    print("\n  Apakah ada perbedaan kecepatan saat GPIO 6 ON?")
    result2 = input("  Jawab (y/n): ").strip().lower()
    
    if result2 == 'n':
        print("  ✗ PIN TIDAK BERPENGARUH - Driver pasti rusak!")
    
except Exception as e:
    print(f"  ✗ ERROR: {e}")

# ==========================================
# TEST 4: GPIO 5 (RR Forward)
# ==========================================
print("\n📍 TEST 4: GPIO 5 (Rear Right Forward)")
print("-"*70)
print("Instruksi: Perhatikan apakah RODA BELAKANG KANAN bergerak MAJU")
print()

input("Tekan ENTER untuk mulai test GPIO 5...")

try:
    pin5 = OutputDevice(5)
    
    print("\n  → Mengaktifkan GPIO 5 selama 3 detik...")
    pin5.on()
    time.sleep(3)
    pin5.off()
    
    pin5.close()
    
    print("\n  Apakah roda belakang kanan (RR) bergerak MAJU?")
    result = input("  Jawab (y/n): ").strip().lower()
    
    if result == 'y':
        print("  ✓ GPIO 5 NORMAL")
    else:
        print("  ✗ GPIO 5 JUGA BERMASALAH")
        
except Exception as e:
    print(f"  ✗ ERROR: {e}")

# ==========================================
# KESIMPULAN
# ==========================================
print("\n" + "="*70)
print("KESIMPULAN & REKOMENDASI")
print("="*70)

print("""
Berdasarkan hasil test di atas:

A. Jika GPIO 24 tidak jalan & GPIO 25 jalan:
   → Masalah: Pin GPIO 24 atau koneksi ke driver
   → Solusi: Ganti pin di config.py atau perbaiki kabel

B. Jika GPIO 24 & 25 tidak jalan sama sekali:
   → Masalah: Driver channel mati atau motor FR rusak
   → Solusi: Ganti driver atau motor

C. Jika GPIO 6 jalan sendiri (walau OFF):
   → Masalah: Driver short circuit atau pull-down rusak
   → Solusi Cepat: Ganti pin GPIO 6 ke pin lain
   → Solusi Permanen: Ganti motor driver

D. Jika semua bermasalah:
   → Masalah: Power supply tidak cukup atau ground tidak bagus
   → Solusi: Cek ground connection & power supply 5-12V
""")

print("="*70)
print("Untuk ganti pin, edit file: config.py")
print("Lalu restart robot dengan: sudo systemctl restart raspbot")
print("="*70)
