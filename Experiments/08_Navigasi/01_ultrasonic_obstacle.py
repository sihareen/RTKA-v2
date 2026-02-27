#!/usr/bin/env python3
"""
Bab 8.1: Sensor Ultrasonik untuk Obstacle Detection
====================================================
HC-SR04 sensor ultrasonik untuk deteksi jarak dan halangan

Prinsip Kerja:
1. Trigger pin mengirim gelombang ultrasonik (40kHz)
2. Gelombang memantul dari objek
3. Echo pin menerima pantulan
4. Waktu tempuh dihitung untuk mendapat jarak

Formula:
  Jarak (cm) = (Waktu tempuh × Kecepatan suara) / 2
  Kecepatan suara = 343 m/s = 34300 cm/s

Spesifikasi HC-SR04:
- Range: 2cm - 400cm
- Akurasi: ±3mm
- Sudut deteksi: 15°
- Trigger: 10µs pulse

Hardware:
- HC-SR04 Ultrasonic Sensor
- Trigger: GPIO 26
- Echo: GPIO 20
"""

from gpiozero import DistanceSensor
from time import sleep
import statistics

# Setup sensor
sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)

print("="*70)
print("HC-SR04 Ultrasonic Sensor - Obstacle Detection")
print("="*70)

def basic_distance_reading():
    """Pembacaan jarak dasar"""
    print("\n[MODE 1] Basic Distance Reading")
    print("-" * 70)
    print("Dekatkan/jauhkan tangan di depan sensor...\n")
    
    for i in range(20):
        try:
            # Baca jarak (dalam meter)
            distance_m = sensor.distance
            distance_cm = distance_m * 100
            
            # Visual bar
            bars = int(distance_cm / 5)
            bar_visual = '█' * min(bars, 40)
            
            print(f"Jarak: {distance_cm:6.2f} cm [{bar_visual}]")
            sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            sleep(0.5)

def obstacle_detection():
    """Deteksi halangan dengan threshold"""
    print("\n[MODE 2] Obstacle Detection")
    print("-" * 70)
    
    THRESHOLD_CM = 30  # Jarak aman
    
    print(f"Threshold: {THRESHOLD_CM} cm")
    print("Status akan ditampilkan...\n")
    
    for i in range(20):
        distance_cm = sensor.distance * 100
        
        if distance_cm < THRESHOLD_CM:
            status = "🚨 OBSTACLE DETECTED!"
            indicator = "🔴"
        else:
            status = "✅ Clear"
            indicator = "🟢"
        
        print(f"{indicator} {distance_cm:6.2f} cm - {status}")
        sleep(0.5)

def multi_zone_detection():
    """Deteksi multi-zone (dekat, sedang, jauh)"""
    print("\n[MODE 3] Multi-Zone Detection")
    print("-" * 70)
    
    ZONE_NEAR = 15      # < 15cm = Sangat dekat
    ZONE_MEDIUM = 30    # 15-30cm = Dekat
    ZONE_FAR = 60       # 30-60cm = Sedang
    # > 60cm = Jauh
    
    print(f"Zones:")
    print(f"  🔴 Very Close: < {ZONE_NEAR} cm")
    print(f"  🟠 Close: {ZONE_NEAR}-{ZONE_MEDIUM} cm")
    print(f"  🟡 Medium: {ZONE_MEDIUM}-{ZONE_FAR} cm")
    print(f"  🟢 Far: > {ZONE_FAR} cm\n")
    
    for i in range(20):
        distance_cm = sensor.distance * 100
        
        if distance_cm < ZONE_NEAR:
            zone = "🔴 VERY CLOSE"
            action = "STOP!"
        elif distance_cm < ZONE_MEDIUM:
            zone = "🟠 CLOSE"
            action = "Slow down"
        elif distance_cm < ZONE_FAR:
            zone = "🟡 MEDIUM"
            action = "Proceed with caution"
        else:
            zone = "🟢 FAR"
            action = "Safe to move"
        
        print(f"{distance_cm:6.2f} cm → {zone:20s} → {action}")
        sleep(0.5)

def averaged_reading():
    """Pembacaan dengan averaging untuk stabilitas"""
    print("\n[MODE 4] Averaged Reading (Noise Reduction)")
    print("-" * 70)
    print("Menggunakan rata-rata 5 pembacaan untuk stabilitas\n")
    
    SAMPLE_SIZE = 5
    
    for i in range(15):
        readings = []
        
        # Ambil beberapa sample
        for _ in range(SAMPLE_SIZE):
            readings.append(sensor.distance * 100)
            sleep(0.05)
        
        # Hitung statistik
        avg = statistics.mean(readings)
        stdev = statistics.stdev(readings) if len(readings) > 1 else 0
        
        print(f"Avg: {avg:6.2f} cm  |  StdDev: {stdev:5.2f} cm  |  Samples: {readings[-3:]}")
        sleep(0.3)

def scan_environment():
    """Scan area (jika menggunakan servo untuk pan)"""
    print("\n[MODE 5] Environment Scan")
    print("-" * 70)
    print("Catatan: Mode ini memerlukan servo untuk pan scan")
    print("Untuk saat ini, hanya membaca jarak di posisi tetap\n")
    
    # Simulasi scan di 5 posisi
    positions = ["Far Left", "Left", "Center", "Right", "Far Right"]
    
    for pos in positions:
        distance_cm = sensor.distance * 100
        print(f"{pos:12s}: {distance_cm:6.2f} cm")
        sleep(0.8)

def measure_speed_of_sound():
    """Eksperimen: mengukur kecepatan suara (advanced)"""
    print("\n[EKSPERIMEN] Measuring Speed of Sound")
    print("-" * 70)
    print("Letakkan objek di jarak yang diketahui (misal 50cm)")
    
    input("\nTekan ENTER ketika siap...")
    
    actual_distance = float(input("Jarak sebenarnya (cm): "))
    
    # Ambil beberapa sample
    samples = []
    print("\nMengukur...")
    for i in range(10):
        samples.append(sensor.distance * 100)
        sleep(0.1)
    
    measured = statistics.mean(samples)
    error = abs(measured - actual_distance)
    error_percent = (error / actual_distance) * 100
    
    print(f"\nHasil:")
    print(f"  Jarak sebenarnya: {actual_distance:.2f} cm")
    print(f"  Jarak terukur: {measured:.2f} cm")
    print(f"  Error: {error:.2f} cm ({error_percent:.1f}%)")

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n📖 Tentang HC-SR04:")
    print("  - Sensor ultrasonik murah dan akurat")
    print("  - Range: 2-400 cm")
    print("  - Tidak terpengaruh cahaya")
    print("  - Sudut deteksi: ±15°")
    print("\n⚠️  Limitasi:")
    print("  - Permukaan miring/lembut kurang akurat")
    print("  - Perlu jarak minimal 2cm")
    print("  - Bisa terganggu oleh suara ultrasonik lain\n")
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Basic Distance Reading")
        print("  2. Obstacle Detection (Threshold)")
        print("  3. Multi-Zone Detection")
        print("  4. Averaged Reading (Noise Filter)")
        print("  5. Environment Scan")
        print("  6. Measure Speed of Sound (Experiment)")
        print("  7. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            basic_distance_reading()
        elif choice == "2":
            obstacle_detection()
        elif choice == "3":
            multi_zone_detection()
        elif choice == "4":
            averaged_reading()
        elif choice == "5":
            scan_environment()
        elif choice == "6":
            measure_speed_of_sound()
        elif choice == "7":
            break
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
finally:
    print("Sensor released")
