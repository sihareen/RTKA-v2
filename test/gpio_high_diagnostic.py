#!/usr/bin/env python3
"""
GPIO HIGH DIAGNOSTIC - Analisis kenapa GPIO 5 dan 6 stuck di HIGH
"""

import subprocess
import time
from gpiozero import Device, DigitalInputDevice, DigitalOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory

try:
    Device.pin_factory = LGPIOFactory()
except:
    pass

print("="*70)
print("GPIO HIGH DIAGNOSTIC - ROOT CAUSE ANALYSIS")
print("="*70)

# ==========================================
# 1. CEK STATUS AWAL
# ==========================================
print("\n📊 STEP 1: CEK STATUS AWAL SEMUA PIN")
print("-"*70)

result = subprocess.run(['pinctrl'], capture_output=True, text=True)
lines = result.stdout.split('\n')

problem_pins = []
for line in lines[:28]:  # GPIO 0-27
    if 'GPIO' in line and '| hi' in line:
        parts = line.split()
        gpio_num = parts[0].rstrip(':')
        status = ' '.join(parts[1:4])
        comment = line.split('//')[-1].strip()
        
        # Filter hanya GPIO biasa (bukan special function)
        if 'GPIO' in comment and '=' in comment:
            gpio_name = comment.split('=')[0].strip()
            if gpio_name.startswith('GPIO') and gpio_name[4:].isdigit():
                print(f"⚠️  GPIO {gpio_num:2s}: {status} | {comment}")
                problem_pins.append(int(gpio_num))

print(f"\nTotal pin yang HIGH: {len(problem_pins)}")
print(f"Pin bermasalah: {problem_pins}")

# ==========================================
# 2. ANALISIS PENYEBAB GPIO 5 & 6
# ==========================================
print("\n🔍 STEP 2: ANALISIS GPIO 5 & 6")
print("-"*70)

target_pins = [5, 6]

for pin in target_pins:
    print(f"\n📌 GPIO {pin}:")
    
    # Cek pull resistor
    result = subprocess.run(['pinctrl', 'get', str(pin)], capture_output=True, text=True)
    status_line = result.stdout.strip()
    
    if 'pu' in status_line:
        print(f"  ⚠️  Ada PULL-UP hardware (pin ditarik ke 3.3V)")
        print(f"     → Ini normal behavior, bukan error!")
    elif 'pd' in status_line:
        print(f"  ✓ Pull-down aktif (seharusnya LOW)")
    elif 'pn' in status_line:
        print(f"  ⚠️  PULL-NONE (floating pin)")
        print(f"     → Pin floating bisa terpengaruh noise/EMI")
        print(f"     → Atau ada arus balik dari external device")
    
    # Test force ke LOW
    print(f"\n  🧪 Test: Force GPIO {pin} ke LOW dengan pull-down...")
    try:
        # Set sebagai input dengan pull-down
        test_pin = DigitalInputDevice(pin, pull_up=False)
        time.sleep(0.1)
        
        initial_val = test_pin.value
        print(f"     Nilai setelah pull-down: {initial_val}")
        
        if initial_val == 1:
            print(f"     ❌ MASIH HIGH walau sudah pull-down!")
            print(f"     → Kemungkinan:")
            print(f"        1. Ada kabel terhubung ke 3.3V (hardware short)")
            print(f"        2. Motor driver inject arus balik ke pin")
            print(f"        3. Pin rusak (internal short ke VCC)")
        else:
            print(f"     ✓ Berhasil jadi LOW")
        
        test_pin.close()
        
    except Exception as e:
        print(f"     ❌ Error: {e}")

# ==========================================
# 3. TEST HARDWARE SHORT
# ==========================================
print("\n\n🔌 STEP 3: TEST HARDWARE SHORT")
print("-"*70)
print("Instruksi: CABUT SEMUA KABEL dari GPIO 5 dan GPIO 6")
input("Tekan ENTER setelah kabel dicabut...")

for pin in target_pins:
    print(f"\nGPIO {pin} (kabel dicabut):")
    try:
        test_pin = DigitalInputDevice(pin, pull_up=False)
        time.sleep(0.2)
        val = test_pin.value
        
        if val == 1:
            print(f"  ❌ TETAP HIGH walau kabel dicabut!")
            print(f"  → Pin rusak atau ada short internal di board")
        else:
            print(f"  ✓ Jadi LOW (masalah dari kabel external)")
        
        test_pin.close()
    except Exception as e:
        print(f"  Error: {e}")

# ==========================================
# 4. TEST MOTOR DRIVER LEAKAGE
# ==========================================
print("\n\n⚡ STEP 4: TEST MOTOR DRIVER LEAKAGE")
print("-"*70)
print("Instruksi: Colok kembali kabel GPIO 5 & 6 ke motor driver")
print("           Tapi MATIKAN power supply motor driver!")
input("Tekan ENTER setelah siap...")

for pin in target_pins:
    print(f"\nGPIO {pin} (driver OFF, kabel terpasang):")
    try:
        test_pin = DigitalInputDevice(pin, pull_up=False)
        time.sleep(0.2)
        val = test_pin.value
        
        if val == 1:
            print(f"  ⚠️  HIGH walau driver OFF")
            print(f"  → Ada pull-up di motor driver board")
            print(f"  → Atau ada kapasitor yang masih menyimpan charge")
        else:
            print(f"  ✓ LOW (normal)")
        
        test_pin.close()
    except Exception as e:
        print(f"  Error: {e}")

# ==========================================
# 5. CEK BOOT CONFIG
# ==========================================
print("\n\n🔧 STEP 5: CEK BOOT CONFIGURATION")
print("-"*70)

config_files = [
    '/boot/firmware/config.txt',
    '/boot/config.txt'
]

for config_file in config_files:
    try:
        result = subprocess.run(['cat', config_file], capture_output=True, text=True, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            content = result.stdout
            
            # Cek GPIO related config
            gpio_lines = [line for line in content.split('\n') if 'gpio' in line.lower() and not line.strip().startswith('#')]
            
            if gpio_lines:
                print(f"\nDari {config_file}:")
                for line in gpio_lines:
                    print(f"  {line}")
            break
    except:
        pass

# ==========================================
# 6. KESIMPULAN & REKOMENDASI
# ==========================================
print("\n\n" + "="*70)
print("KESIMPULAN & REKOMENDASI")
print("="*70)

print("""
PENYEBAB UMUM PIN STUCK di HIGH:

A. **FLOATING PIN** (pn | hi):
   Penyebab: Pin tanpa pull resistor terpengaruh noise elektromagnetik
   Solusi: 
   - Gunakan pin dengan pull-down di software
   - Atau hindari pin yang floating

B. **MOTOR DRIVER PULL-UP**:
   Penyebab: Motor driver punya pull-up resistor internal (10K-47K ke VCC)
   Solusi:
   - Normal behavior untuk beberapa driver (L298N, TB6612)
   - Ganti pin ke yang tidak terhubung driver
   - Atau set pin sebagai output untuk override pull-up

C. **HARDWARE SHORT**:
   Penyebab: Kabel short ke 3.3V, atau PCB track rusak
   Solusi:
   - Cek visual solderan/breadboard
   - Ganti kabel jumper
   - Ganti pin GPIO

D. **CAPACITIVE COUPLING**:
   Penyebab: Motor menginduksi tegangan balik ke GPIO
   Solusi:
   - Tambahkan diode flyback di motor
   - Tambahkan capacitor 100nF di input driver
   - Pisahkan ground digital dan power

E. **PREVIOUS OUTPUT STATE**:
   Penyebab: Pin di-set output HIGH oleh program lain, tidak di-reset
   Solusi:
   - Reboot Raspberry Pi
   - Set pin ke input dengan pull-down saat startup

REKOMENDASI UNTUK SISTEM ANDA:

1. **Jangan gunakan GPIO 0, 2, 3, 5, 6** untuk motor
   → Pin ini bermasalah (pull-up atau stuck HIGH)

2. **Gunakan pin yang status awal LOW**:
   → GPIO 1, 4, 7, 8, 9, 10, 11, dst

3. **Tambahkan pull-down di config motor.py**:
   → Modifikasi gpiozero init dengan pull_up=False

4. **Isolasi ground**:
   → Pisahkan ground Pi dengan ground motor driver jika memungkinkan
""")

print("="*70)
print("Diagnostic selesai!")
print("="*70)
