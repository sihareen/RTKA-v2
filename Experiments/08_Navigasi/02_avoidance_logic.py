#!/usr/bin/env python3
"""
Bab 8.2: Logika Avoidance Sederhana
====================================
Implementasi logika untuk menghindari halangan

Algoritma Avoidance:
1. Baca jarak dari sensor
2. Jika jarak < threshold → Ada halangan
3. Stop motor
4. Mundur sedikit
5. Belok (kiri atau kanan)
6. Lanjut maju

Flowchart:
┌─────────────┐
│   Maju      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Baca Sensor │◄──────┐
└──────┬──────┘       │
       │              │
   Jarak < 30cm?      │
       │              │
   ┌───┴───┐          │
   │  Ya   │   Tidak  │
   ▼       └──────────┘
┌─────────────┐
│    Stop     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Mundur    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Belok     │
└──────┬──────┘
       │
       └──────────────┘

Hardware:
- 4WD Robot
- HC-SR04 Ultrasonic
- Motor Driver
"""

from gpiozero import Motor, DistanceSensor
from time import sleep

# Setup motors (4WD)
motor_fl = Motor(forward=17, backward=27)
motor_rl = Motor(forward=22, backward=23)
motor_fr = Motor(forward=10, backward=25)
motor_rr = Motor(forward=16, backward=9)

# Setup sensor
sensor = DistanceSensor(echo=20, trigger=26, max_distance=4.0)

# Parameters
SAFE_DISTANCE = 30  # cm
SPEED = 0.4

print("="*70)
print("Obstacle Avoidance - Logika Dasar")
print("="*70)

def move_forward(speed=SPEED):
    """Gerak maju"""
    motor_fl.forward(speed)
    motor_rl.forward(speed)
    motor_fr.forward(speed)
    motor_rr.forward(speed)

def move_backward(speed=SPEED):
    """Gerak mundur"""
    motor_fl.backward(speed)
    motor_rl.backward(speed)
    motor_fr.backward(speed)
    motor_rr.backward(speed)

def turn_right(speed=SPEED):
    """Belok kanan (pivot)"""
    motor_fl.forward(speed)
    motor_rl.forward(speed)
    motor_fr.backward(speed)
    motor_rr.backward(speed)

def turn_left(speed=SPEED):
    """Belok kiri (pivot)"""
    motor_fl.backward(speed)
    motor_rl.backward(speed)
    motor_fr.forward(speed)
    motor_rr.forward(speed)

def stop_all():
    """Stop semua motor"""
    motor_fl.stop()
    motor_rl.stop()
    motor_fr.stop()
    motor_rr.stop()

def get_distance():
    """Baca jarak dari sensor"""
    return sensor.distance * 100  # Convert to cm

def simple_avoidance():
    """Avoidance sederhana - versi 1"""
    print("\n[Version 1] Simple Avoidance")
    print("Algoritma: Detect → Stop → Back → Turn Right\n")
    
    try:
        iteration = 0
        while iteration < 20:  # Batasi iterasi untuk demo
            distance = get_distance()
            print(f"[{iteration:02d}] Distance: {distance:6.2f} cm", end="")
            
            if distance < SAFE_DISTANCE:
                print(" → 🚨 OBSTACLE! Avoiding...")
                
                # Stop
                stop_all()
                sleep(0.3)
                
                # Mundur
                print("     └─ Backing up...")
                move_backward(0.4)
                sleep(0.8)
                
                # Stop
                stop_all()
                sleep(0.2)
                
                # Belok kanan
                print("     └─ Turning right...")
                turn_right(0.4)
                sleep(0.7)
                
                # Stop
                stop_all()
                sleep(0.2)
            else:
                print(" → ✅ Clear, moving forward")
                move_forward(0.4)
            
            sleep(0.2)
            iteration += 1
        
    finally:
        stop_all()

def smart_avoidance():
    """Avoidance pintar - dengan scan kiri/kanan"""
    print("\n[Version 2] Smart Avoidance")
    print("Algoritma: Detect → Stop → Scan → Choose best path\n")
    print("Catatan: Memerlukan servo untuk scan (simulasi saja)\n")
    
    try:
        iteration = 0
        while iteration < 20:
            distance = get_distance()
            print(f"[{iteration:02d}] Distance: {distance:6.2f} cm", end="")
            
            if distance < SAFE_DISTANCE:
                print(" → 🚨 OBSTACLE!")
                
                # Stop
                stop_all()
                sleep(0.3)
                
                # Scan (simulasi - sebenarnya perlu servo)
                print("     └─ Scanning...")
                
                # Simulasi: random pilih kiri atau kanan
                import random
                direction = random.choice(["left", "right"])
                
                if direction == "left":
                    print("     └─ Left is clearer, turning left...")
                    move_backward(0.4)
                    sleep(0.6)
                    stop_all()
                    sleep(0.2)
                    turn_left(0.4)
                    sleep(0.7)
                else:
                    print("     └─ Right is clearer, turning right...")
                    move_backward(0.4)
                    sleep(0.6)
                    stop_all()
                    sleep(0.2)
                    turn_right(0.4)
                    sleep(0.7)
                
                stop_all()
                sleep(0.2)
            else:
                print(" → ✅ Moving forward")
                move_forward(0.4)
            
            sleep(0.2)
            iteration += 1
    
    finally:
        stop_all()

def gradual_slowdown():
    """Avoidance dengan perlambatan bertahap"""
    print("\n[Version 3] Gradual Slowdown")
    print("Algoritma: Makin dekat → makin pelan\n")
    
    ZONE_1 = 50  # Slow down
    ZONE_2 = 30  # Very slow
    ZONE_3 = 15  # Stop
    
    try:
        iteration = 0
        while iteration < 25:
            distance = get_distance()
            
            if distance > ZONE_1:
                # Jauh - aman
                speed = 0.5
                action = "Full speed"
                emoji = "🟢"
            elif distance > ZONE_2:
                # Sedang - pelan
                speed = 0.3
                action = "Slowing down"
                emoji = "🟡"
            elif distance > ZONE_3:
                # Dekat - sangat pelan
                speed = 0.15
                action = "Very slow"
                emoji = "🟠"
            else:
                # Terlalu dekat - stop dan hindari
                speed = 0
                action = "AVOIDING!"
                emoji = "🔴"
                
                stop_all()
                sleep(0.3)
                move_backward(0.4)
                sleep(0.8)
                stop_all()
                turn_right(0.4)
                sleep(0.7)
                stop_all()
                sleep(0.2)
                iteration += 1
                continue
            
            print(f"{emoji} [{iteration:02d}] {distance:5.1f}cm → {action:15s} (Speed: {speed*100:.0f}%)")
            move_forward(speed)
            sleep(0.2)
            iteration += 1
    
    finally:
        stop_all()

# ============================================================================
# MAIN PROGRAM
# ============================================================================

try:
    print("\n📖 Logika Avoidance:")
    print("  1. Simple: Detect → Avoid → Continue")
    print("  2. Smart: Detect → Scan → Choose best path")
    print("  3. Gradual: Slow down based on distance")
    print()
    print("⚠️  Safety:")
    print("  - Pastikan area tes aman dan luas")
    print("  - Robot akan bergerak otomatis")
    print("  - Siapkan emergency stop (Ctrl+C)")
    print()
    
    while True:
        print("\n" + "="*70)
        print("MENU:")
        print("  1. Simple Avoidance (Fixed pattern)")
        print("  2. Smart Avoidance (Scan & choose)")
        print("  3. Gradual Slowdown (Distance-based speed)")
        print("  4. Exit")
        print("="*70)
        
        choice = input("\nPilihan: ").strip()
        
        if choice == "1":
            input("\n⚠️  Robot akan bergerak! Tekan ENTER untuk mulai...")
            simple_avoidance()
            print("\n✅ Simple avoidance selesai")
        elif choice == "2":
            input("\n⚠️  Robot akan bergerak! Tekan ENTER untuk mulai...")
            smart_avoidance()
            print("\n✅ Smart avoidance selesai")
        elif choice == "3":
            input("\n⚠️  Robot akan bergerak! Tekan ENTER untuk mulai...")
            gradual_slowdown()
            print("\n✅ Gradual slowdown selesai")
        elif choice == "4":
            break
        else:
            print("❌ Pilihan tidak valid")
    
    print("\n✅ Program selesai!")
    print("\n💡 Next Steps:")
    print("  - Tambahkan sensor tambahan (multiple ultrasonic)")
    print("  - Implementasi state machine untuk behavior lebih kompleks")
    print("  - Kombinasikan dengan line follower atau other features")

except KeyboardInterrupt:
    print("\n\n🛑 Emergency Stop!")
finally:
    stop_all()
    print("All motors stopped")
