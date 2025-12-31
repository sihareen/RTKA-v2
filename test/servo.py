from gpiozero import AngularServo
from gpiozero.pins.lgpio import LGPIOFactory
import time

# =========================
# KONFIGURASI
# =========================
PIN_SERVO = 12
STEP_DELAY = 0.25   # cukup lambat agar kelihatan respons

# =========================
# LGPIO FACTORY (RPI 5)
# =========================
factory = LGPIOFactory()

# ⚠️ Range servo dipersempit
servo = AngularServo(
    PIN_SERVO,
    min_angle=-30,
    max_angle=30,
    min_pulse_width=0.5/1000,
    max_pulse_width=2.5/1000,
    pin_factory=factory
)

print("\n[INFO] UJI RANGE SERVO -30° s/d +30°")
print("[INFO] Gerak step 1° (eksperimen deadband)\n")

# =========================
# POSISI AWAL
# =========================
servo.angle = 0
time.sleep(1)

# =========================
# GERAK STEP 1°
# =========================
try:
    for angle in range(-30, 31):
        servo.angle = angle
        print(f"Sudut: {angle}°")
        time.sleep(STEP_DELAY)

except KeyboardInterrupt:
    print("\n[INFO] Dihentikan user")

finally:
    servo.detach()
    print("[INFO] Servo dilepas")
