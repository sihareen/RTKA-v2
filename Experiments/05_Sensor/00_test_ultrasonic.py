#!/usr/bin/env python3
"""
Bab 5 - Test Sensor Ultrasonik
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
    print("=== Test Ultrasonik ===")

    for _ in range(20):
        distance_cm = sensor.distance * 100
        print(f"Jarak: {distance_cm:5.1f} cm")
        sleep(0.2)

    print("Test selesai")


if __name__ == "__main__":
    main()
