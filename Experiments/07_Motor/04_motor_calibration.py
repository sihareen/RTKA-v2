#!/usr/bin/env python3
"""
Bab 7.4: Kalibrasi Motor Kiri & Kanan
======================================
Motor kiri dan kanan sering berbeda karakteristiknya
Kalibrasi diperlukan agar robot jalan lurus

Masalah Umum:
- Robot belok sendiri saat maju lurus
- Motor kiri lebih kuat dari motor kanan (atau sebaliknya)
- Perbedaan RPM antar motor
- Friction roda berbeda

Solusi:
- Ukur kecepatan aktual setiap motor
- Buat faktor koreksi (calibration factor)
- Terapkan offset speed saat kontrol

Hardware:
- 2 Motor DC (Left & Right)
- L298N Motor Driver
"""

from gpiozero import Motor
from time import sleep, time

# Setup motors
motor_left = Motor(forward=17, backward=27)
motor_right = Motor(forward=22, backward=23)

# Calibration factors (akan diisi hasil kalibrasi)
LEFT_CALIBRATION = 1.0
RIGHT_CALIBRATION = 1.0

print("="*70)
print("Motor Calibration Tool")
print("="*70)

def test_straight_line():
    """Test robot jalan lurus tanpa kalibrasi"""
    print("\n[TEST 1] Robot maju lurus (TANPA kalibrasi)")
    print("Amati: apakah robot belok ke kiri/kanan?\n")
    
    speed = 0.5
    motor_left.forward(speed)
    motor_right.forward(speed)
    
    input("Motor running... Tekan ENTER untuk stop")
    
    motor_left.stop()
    motor_right.stop()
    
    print("\n❓ Hasil observasi:")
    print("  - Robot lurus? → Motor sudah balance")
    print("  - Belok kiri? → Motor kanan lebih kuat")
    print("  - Belok kanan? → Motor kiri lebih kuat")

def manual_calibration():
    """Kalibrasi manual dengan trial and error"""
    print("\n" + "="*70)
    print("[KALIBRASI MANUAL]")
    print("="*70)
    
    global LEFT_CALIBRATION, RIGHT_CALIBRATION
    
    print("\nProsedur:")
    print("1. Robot akan maju dengan speed berbeda")
    print("2. Amati hasilnya")
    print("3. Sesuaikan hingga robot jalan lurus\n")
    
    # Default values
    left_speed = 0.5
    right_speed = 0.5
    
    tests = [
        ("Base Speed (Equal)", 0.5, 0.5),
        ("Right Reduced 10%", 0.5, 0.45),
        ("Right Reduced 20%", 0.5, 0.40),
        ("Left Reduced 10%", 0.45, 0.5),
        ("Left Reduced 20%", 0.40, 0.5),
    ]
    
    for name, left, right in tests:
        print(f"\nTest: {name}")
        print(f"  Left: {left:.2f}, Right: {right:.2f}")
        
        motor_left.forward(left)
        motor_right.forward(right)
        
        sleep(3)
        
        motor_left.stop()
        motor_right.stop()
        
        response = input("  Hasilnya? (l=lurus, k=kiri, r=kanan, q=quit): ").lower()
        
        if response == 'l':
            print(f"\n✅ KALIBRASI DITEMUKAN!")
            print(f"  Left Speed: {left:.2f}")
            print(f"  Right Speed: {right:.2f}")
            LEFT_CALIBRATION = left / 0.5
            RIGHT_CALIBRATION = right / 0.5
            break
        elif response == 'q':
            break
        
        sleep(1)

def automatic_test():
    """Test otomatis dengan berbagai speed"""
    print("\n" + "="*70)
    print("[AUTO CALIBRATION TEST]")
    print("="*70)
    print("\nMenggunakan hasil kalibrasi:")
    print(f"  Left Factor: {LEFT_CALIBRATION:.3f}")
    print(f"  Right Factor: {RIGHT_CALIBRATION:.3f}\n")
    
    base_speeds = [0.3, 0.5, 0.7]
    
    for base_speed in base_speeds:
        left_speed = base_speed * LEFT_CALIBRATION
        right_speed = base_speed * RIGHT_CALIBRATION
        
        print(f"Base Speed: {base_speed:.1f}")
        print(f"  → Left: {left_speed:.3f}, Right: {right_speed:.3f}")
        
        motor_left.forward(left_speed)
        motor_right.forward(right_speed)
        
        sleep(2)
        
        motor_left.stop()
        motor_right.stop()
        
        sleep(1)

def save_calibration():
    """Simpan hasil kalibrasi ke file"""
    with open("motor_calibration.txt", "w") as f:
        f.write(f"LEFT_CALIBRATION={LEFT_CALIBRATION:.4f}\n")
        f.write(f"RIGHT_CALIBRATION={RIGHT_CALIBRATION:.4f}\n")
    
    print(f"\n💾 Kalibrasi disimpan ke: motor_calibration.txt")

def load_calibration():
    """Load kalibrasi dari file"""
    global LEFT_CALIBRATION, RIGHT_CALIBRATION
    
    try:
        with open("motor_calibration.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("LEFT_CALIBRATION"):
                    LEFT_CALIBRATION = float(line.split("=")[1])
                elif line.startswith("RIGHT_CALIBRATION"):
                    RIGHT_CALIBRATION = float(line.split("=")[1])
        
        print(f"📂 Kalibrasi loaded:")
        print(f"  Left: {LEFT_CALIBRATION:.4f}")
        print(f"  Right: {RIGHT_CALIBRATION:.4f}")
        return True
    except FileNotFoundError:
        print("⚠️  File kalibrasi tidak ditemukan")
        return False

def calibrated_move(base_speed, duration=2):
    """Gerak maju dengan kalibrasi"""
    left_speed = base_speed * LEFT_CALIBRATION
    right_speed = base_speed * RIGHT_CALIBRATION
    
    motor_left.forward(left_speed)
    motor_right.forward(right_speed)
    sleep(duration)
    motor_left.stop()
    motor_right.stop()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n📖 Tentang Kalibrasi Motor:")
    print("  - Setiap motor punya karakteristik berbeda")
    print("  - Kalibrasi = mencari speed offset yang tepat")
    print("  - Hasil kalibrasi bisa disimpan & dipakai ulang\n")
    
    # Coba load kalibrasi existing
    if not load_calibration():
        print("\nMemulai kalibrasi baru...\n")
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Test straight line (no calibration)")
        print("  2. Manual calibration")
        print("  3. Auto test with calibration")
        print("  4. Save calibration")
        print("  5. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            test_straight_line()
        elif choice == "2":
            manual_calibration()
        elif choice == "3":
            automatic_test()
        elif choice == "4":
            save_calibration()
        elif choice == "5":
            break
        else:
            print("❌ Pilihan tidak valid")

    print("\n✅ Program selesai")
    print("\n💡 Tips:")
    print("  - Lakukan kalibrasi di permukaan datar")
    print("  - Gunakan kalibrasi yang sudah disimpan di program utama")
    print("  - Re-kalibrasi jika ganti motor atau roda")

except KeyboardInterrupt:
    print("\n\nProgram dihentikan")
finally:
    motor_left.stop()
    motor_right.stop()
    print("\nMotor stopped")
