#!/usr/bin/env python3
import time
from modules.motor import MotorDriver

def main():
    print("=== MOTOR CONTINUOUS TEST ===")
    print("CTRL + C untuk berhenti\n")

    motor = MotorDriver(simulation=False)

    try:
        while True:
            # =========================
            # MAJU LURUS TANPA HENTI
            # throttle = 0.3  (30%)
            # steering = 0.0  (lurus)
            # =========================
            motor.move(
                throttle=0.3,
                steering=0.0,
                speed_limit=100
            )

            time.sleep(0.1)  # jaga CPU tetap adem

    except KeyboardInterrupt:
        print("\n[STOP] Motor dihentikan oleh user")

    finally:
        motor.stop()
        motor.close()
        print("[DONE] Motor OFF & GPIO released")

if __name__ == "__main__":
    main()
