from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
import time

# =========================
# KONFIGURASI
# =========================
PIN_SERVO = 12

# =========================
# GPIO FACTORY (RPI 5)
# =========================
factory = LGPIOFactory()

servo = AngularServo(
    PIN_SERVO,
    min_angle=-90,
    max_angle=90,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    pin_factory=factory
)

# =========================
# HELPER
# =========================
def logical_to_servo(angle):
    return angle - 90  # 0–180 → -90–+90

# =========================
# INIT
# =========================
current_angle = 0
servo.angle = logical_to_servo(current_angle)
time.sleep(0.4)
servo.detach()

print("\n[INFO] MODE INPUT SUDUT MANUAL (DIRECT)")
print("[INFO] Servo langsung ke target")
print("[INFO] Ketik q untuk keluar\n")

# =========================
# LOOP UTAMA
# =========================
try:
    while True:
        user = input("Target sudut (0–180 | q): ").strip().lower()

        if user == "q":
            break

        if not user.isdigit():
            print("[WARNING] Input tidak valid\n")
            continue

        target = int(user)
        if not 0 <= target <= 180:
            print("[WARNING] Sudut harus 0–180\n")
            continue

        print(f"[MOVE] {current_angle}° → {target}° (direct)")

        servo.angle = logical_to_servo(target)
        current_angle = target

        time.sleep(0.3)   # beri waktu servo mencapai target
        servo.detach()
        print("[INFO] Servo detached\n")

except KeyboardInterrupt:
    print("\n[INFO] Dihentikan user")

finally:
    servo.detach()
    servo.close()
    print("[INFO] GPIO dilepas, program selesai")

