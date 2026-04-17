#!/usr/bin/env python3
"""
Bab 6 - Mini Project: Lampu Otomatis Berbasis Sensor

Implementasi ini menggunakan sensor jarak (ultrasonik) sebagai deteksi keberadaan.
Jika ada objek/manusia dalam jarak tertentu, lampu menyala otomatis.
"""

from time import sleep

from gpiozero import Device, DistanceSensor, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


TRIG_PIN = 5
ECHO_PIN = 6
LAMP_PIN = 27
PRESENCE_THRESHOLD_CM = 40
OFF_DELAY_SEC = 5


def main():
    sensor = DistanceSensor(trigger=TRIG_PIN, echo=ECHO_PIN, max_distance=4)
    lamp = LED(LAMP_PIN)

    print("Auto light aktif. Ctrl+C untuk berhenti.")
    print(f"Lampu ON jika objek < {PRESENCE_THRESHOLD_CM} cm")

    countdown = 0
    try:
        while True:
            distance_cm = sensor.distance * 100
            detected = distance_cm < PRESENCE_THRESHOLD_CM

            if detected:
                lamp.on()
                countdown = OFF_DELAY_SEC * 10
                state = "ON"
            else:
                if countdown > 0:
                    countdown -= 1
                    lamp.on()
                    state = "ON_DELAY"
                else:
                    lamp.off()
                    state = "OFF"

            print(f"distance={distance_cm:6.2f} cm | lamp={state}", end="\r")
            sleep(0.1)
    except KeyboardInterrupt:
        lamp.off()
        print("\nSelesai")


if __name__ == "__main__":
    main()
