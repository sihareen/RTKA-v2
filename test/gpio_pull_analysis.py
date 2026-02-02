#!/usr/bin/env python3
"""
RASPBERRY PI GPIO PULL RESISTOR ANALYSIS
Menganalisis kenapa beberapa GPIO punya pull-up/down
"""

import subprocess

print("="*70)
print("RASPBERRY PI GPIO PULL RESISTOR CONFIGURATION")
print("="*70)

# Jalankan pinctrl untuk semua GPIO
result = subprocess.run(['pinctrl'], capture_output=True, text=True)
lines = result.stdout.split('\n')

# Kategorikan berdasarkan pull resistor
pull_up_pins = []
pull_down_pins = []
pull_none_pins = []
pull_none_high = []

for line in lines[:28]:  # GPIO 0-27
    if ':' not in line:
        continue
    
    parts = line.split()
    if len(parts) < 3:
        continue
        
    gpio_num = parts[0].rstrip(':')
    if not gpio_num.isdigit():
        continue
    
    gpio_num = int(gpio_num)
    pull_type = parts[1]
    state = parts[3]
    
    if pull_type == 'pu':
        pull_up_pins.append((gpio_num, state))
    elif pull_type == 'pd':
        pull_down_pins.append((gpio_num, state))
    elif pull_type == 'pn':
        pull_none_pins.append((gpio_num, state))
        if state == 'hi':
            pull_none_high.append(gpio_num)

print("\n📊 STATISTIK PULL RESISTOR:")
print("-"*70)
print(f"Pull-UP pins:   {len(pull_up_pins)} pin")
print(f"Pull-DOWN pins: {len(pull_down_pins)} pin")
print(f"Pull-NONE pins: {len(pull_none_pins)} pin")
print(f"  └─ NONE tapi HIGH: {len(pull_none_high)} pin ⚠️")

print("\n⬆️  GPIO dengan PULL-UP (ditarik ke 3.3V):")
print("-"*70)
for gpio, state in pull_up_pins:
    print(f"  GPIO {gpio:2d}: {state}")

print("\n⚠️  GPIO PULL-NONE tapi HIGH (BERMASALAH!):")
print("-"*70)
for gpio in pull_none_high:
    print(f"  GPIO {gpio:2d}")

print("\n\n" + "="*70)
print("PENJELASAN TEKNIS")
print("="*70)

print("""
KENAPA GPIO 5 & 6 STUCK di HIGH?

Berdasarkan diagnostic:
1. Output `pinctrl` menunjukkan: "ip pn | hi" (pull-none, HIGH)
2. Tapi saat test dengan pull-down software → TETAP HIGH
3. Ini menunjukkan ada PULL-UP HARDWARE yang kuat

PENYEBAB:
┌─────────────────────────────────────────────────────────────┐
│  GPIO 5 & 6 di Raspberry Pi 5 MUNGKIN punya pull-up        │
│  internal yang TIDAK BISA DI-DISABLE oleh software!        │
│                                                              │
│  Atau ada hardware external (motor driver) yang inject     │
│  tegangan balik ke pin ini.                                 │
└─────────────────────────────────────────────────────────────┘

FAKTA HARDWARE RASPBERRY PI:
- GPIO 0, 1: Reserved untuk ID EEPROM (pull-up)
- GPIO 2, 3: I2C (SDA/SCL) - ALWAYS pull-up 1.8kΩ
- GPIO 5, 6: Di beberapa RPi model punya pull-up untuk boot config
- GPIO 14, 15: UART (bisa punya pull)

TESTING LEBIH LANJUT:

1. Cek apakah GPIO 5/6 digunakan untuk boot mode selection:
   → Beberapa RPi menggunakan GPIO tertentu untuk boot mode
   → Pull-up permanen, tidak bisa di-override

2. Cek device tree overlay:
   → Ada kemungkinan overlay mengaktifkan pull-up

3. Cek motor driver board:
   → Motor driver seperti L298N/TB6612 punya pull-up 10kΩ di input
   → Untuk menjaga pin HIGH saat floating (safety)

SOLUSI:

A. JANGAN GUNAKAN GPIO berikut untuk OUTPUT ke motor driver:
   ❌ GPIO 0, 1  (ID EEPROM)
   ❌ GPIO 2, 3  (I2C - pull-up permanen)
   ❌ GPIO 5, 6  (Pull-up hardware/boot config)

B. GUNAKAN GPIO yang aman (pull-none, LOW default):
   ✅ GPIO 4, 7, 8, 9, 10, 11
   ✅ GPIO 16, 17, 18, 19
   ✅ GPIO 20, 21, 22, 23, 24, 25, 26, 27

C. Jika HARUS pakai GPIO 5/6:
   → Set sebagai OUTPUT dengan initial value LOW
   → Tapi tetap tidak ideal karena saat boot akan HIGH dulu

D. Isolasi Motor Driver:
   → Gunakan optocoupler atau level shifter
   → Pisahkan ground digital dan power motor

""")

print("="*70)
print("REKOMENDASI FINAL UNTUK SISTEM ANDA:")
print("="*70)
print("""
Konfigurasi motor yang AMAN:

SISI KIRI (Driver 1):
  FL Forward:  GPIO 17 ✅
  FL Backward: GPIO 27 ✅
  RL Forward:  GPIO 22 ✅
  RL Backward: GPIO 23 ✅

SISI KANAN (Driver 2):
  FR Forward:  GPIO 10 ✅  (sudah diganti dari 24)
  FR Backward: GPIO 25 ✅
  RR Forward:  GPIO 16 ✅
  RR Backward: GPIO 9  ✅  (sudah diganti dari 6)

Semua pin di atas AMAN (tidak ada pull-up permanen)
""")

print("="*70)
