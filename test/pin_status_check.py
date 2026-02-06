#!/usr/bin/env python3
"""
PIN MAPPING VISUALIZER - RTKAv2
Menampilkan mapping pin motor secara visual
"""

import sys
sys.path.insert(0, '/home/pi/RTKAv2')
from config import *

print("="*70)
print("PIN MAPPING VISUALIZATION - RTKAv2 ROBOT")
print("="*70)

print("""
┌─────────────────────────────────────────────────────────────────┐
│                    KONFIGURASI MOTOR 4WD                        │
└─────────────────────────────────────────────────────────────────┘
""")

# Tampilkan dalam format tabel
print("┌─────────────┬──────────┬─────────┬──────────────────────────┐")
print("│   MOTOR     │   PIN    │  GPIO   │       FUNGSI             │")
print("├─────────────┼──────────┼─────────┼──────────────────────────┤")
print(f"│ Front Left  │ Forward  │  GPIO {PIN_FL_FWD:2d} │  Roda Depan Kiri Maju   │")
print(f"│     (FL)    │ Backward │  GPIO {PIN_FL_BWD:2d} │  Roda Depan Kiri Mundur │")
print("├─────────────┼──────────┼─────────┼──────────────────────────┤")
print(f"│ Rear Left   │ Forward  │  GPIO {PIN_RL_FWD:2d} │  Roda Belakang Kiri Maju│")
print(f"│     (RL)    │ Backward │  GPIO {PIN_RL_BWD:2d} │  Roda Belakang Kiri Mdur│")
print("├─────────────┼──────────┼─────────┼──────────────────────────┤")
print(f"│ Front Right │ Forward  │  GPIO {PIN_FR_FWD:2d} │  Roda Depan Kanan Maju  │ ⚠️")
print(f"│     (FR)    │ Backward │  GPIO {PIN_FR_BWD:2d} │  Roda Depan Kanan Mundur│")
print("├─────────────┼──────────┼─────────┼──────────────────────────┤")
print(f"│ Rear Right  │ Forward  │  GPIO {PIN_RR_FWD:2d}  │  Roda Belakang Kanan Mj │")
print(f"│     (RR)    │ Backward │  GPIO {PIN_RR_BWD:2d}  │  Roda Belakang Kanan Md │ 🚨")
print("└─────────────┴──────────┴─────────┴──────────────────────────┘")

print("""
🚨 MASALAH YANG DILAPORKAN:
""")

print("┌─────────────────────────────────────────────────────────────────┐")
print("│ 1. GPIO 6 (RR Backward) - TERUS MUNDUR                         │")
print("│    Lokasi: Roda Belakang Kanan (Rear Right)                    │")
print("│    Gejala: Motor mundur terus walau tidak ada perintah         │")
print("│                                                                 │")
print("│    Penyebab Kemungkinan:                                        │")
print("│    ✗ Motor driver channel rusak (short circuit)                │")
print("│    ✗ Kabel GPIO ke driver short dengan VCC                     │")
print("│    ✗ Pin terbalik (FWD dan BWD tertukar di fisik)              │")
print("│    ✗ Pull-down resistor di driver tidak berfungsi              │")
print("│                                                                 │")
print("│ 2. GPIO 24 (FR Forward) - TIDAK BISA MAJU                      │")
print("│    Lokasi: Roda Depan Kanan (Front Right)                      │")
print("│    Gejala: Motor tidak bergerak saat diberi perintah maju      │")
print("│                                                                 │")
print("│    Penyebab Kemungkinan:                                        │")
print("│    ✗ Kabel GPIO 24 ke driver putus/lepas                       │")
print("│    ✗ Motor driver channel mati                                 │")
print("│    ✗ Motor fisik rusak (test dengan supply langsung)           │")
print("│    ✗ GPIO 24 rusak di Raspberry Pi (test dengan LED)           │")
print("└─────────────────────────────────────────────────────────────────┘")

print("""
💡 SOLUSI YANG BISA DICOBA:
""")

print("┌─────────────────────────────────────────────────────────────────┐")
print("│ UNTUK GPIO 6 (RR Backward - Jalan Terus):                      │")
print("│                                                                 │")
print("│ A. Quick Test:                                                  │")
print("│    1. Cabut kabel GPIO 6 dari driver                            │")
print("│    2. Cek apakah motor tetap mundur?                            │")
print("│       → Ya = Driver rusak (ganti driver)                        │")
print("│       → Tidak = Pin bermasalah                                  │")
print("│                                                                 │")
print("│ B. Tukar Pin (Sementara):                                       │")
print("│    Ganti PIN_RR_BWD dari 6 ke pin lain (misalnya 16)           │")
print("│    Edit di config.py:                                           │")
print("│    PIN_RR_BWD = 16  # Ganti dari 6                             │")
print("│                                                                 │")
print("│ C. Cek Wiring:                                                  │")
print("│    Pastikan GPIO 6 terhubung ke IN4 driver (bukan VCC/GND)     │")
print("└─────────────────────────────────────────────────────────────────┘")

print("┌─────────────────────────────────────────────────────────────────┐")
print("│ UNTUK GPIO 24 (FR Forward - Tidak Jalan):                      │")
print("│                                                                 │")
print("│ A. Test Hardware:                                               │")
print("│    1. Colok LED antara GPIO 24 dan GND                          │")
print("│    2. Jalankan test: python3 test/quick_pin_test.py            │")
print("│    3. LED nyala? → Pin OK, masalah di driver/kabel              │")
print("│       LED mati?  → Pin rusak, ganti pin                         │")
print("│                                                                 │")
print("│ B. Cek Koneksi Driver:                                          │")
print("│    Pastikan GPIO 24 terhubung ke IN3 driver yang benar         │")
print("│    Test dengan multimeter (harus 3.3V saat HIGH)               │")
print("│                                                                 │")
print("│ C. Test Motor Langsung:                                         │")
print("│    Colok motor FR langsung ke power supply (tanpa driver)      │")
print("│    Jika motor mati → Ganti motor                                │")
print("│    Jika motor OK → Masalah di driver                            │")
print("└─────────────────────────────────────────────────────────────────┘")

print("""
🔧 KONFIGURASI PIN ALTERNATIF (Jika Perlu Ganti):
""")

print("Pin GPIO yang masih available untuk motor driver:")
print("  GPIO 16, 19, 20, 21, 26 (jika tidak dipakai sensor lain)")
print()
print("Untuk mengganti, edit file: config.py")
print("  Contoh:")
print("    PIN_RR_BWD = 16  # Ganti dari 6")
print("    PIN_FR_FWD = 19  # Ganti dari 24")
print()

print("="*70)
print("Untuk test otomatis, jalankan:")
print("  python3 test/pin_diagnostic.py")
print("="*70)
