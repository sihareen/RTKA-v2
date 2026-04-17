#!/usr/bin/env python3
"""
Bab 5 - Mengukur Jarak dengan HC-SR04
"""

from time import sleep

from gpiozero import Device, DistanceSensor

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


TRIG_PIN = 5
ECHO_PIN = 6


def main():
    sensor = DistanceSensor(trigger=TRIG_PIN, echo=ECHO_PIN, max_distance=4)
    print("Monitoring jarak real-time. Ctrl+C untuk berhenti.")

    try:
        while True:
            distance_cm = sensor.distance * 100
            print(f"Distance: {distance_cm:6.2f} cm", end="\r")
            sleep(0.1)
    except KeyboardInterrupt:
        print("\nSelesai")


if __name__ == "__main__":
    main()
