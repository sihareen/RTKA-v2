#!/usr/bin/env python3
"""
Bab 5 - Filtering Data Sensor Jarak
Moving average untuk meredam noise.
"""

from collections import deque
from statistics import mean
from time import sleep

from gpiozero import Device, DistanceSensor

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


TRIG_PIN = 5
ECHO_PIN = 6
WINDOW_SIZE = 5


def main():
    sensor = DistanceSensor(trigger=TRIG_PIN, echo=ECHO_PIN, max_distance=4)
    buffer = deque(maxlen=WINDOW_SIZE)

    print("Raw vs Filtered distance (moving average). Ctrl+C untuk berhenti.")

    try:
        while True:
            raw_cm = sensor.distance * 100
            buffer.append(raw_cm)
            filtered_cm = mean(buffer)

            print(f"raw={raw_cm:6.2f} cm | filtered={filtered_cm:6.2f} cm", end="\r")
            sleep(0.1)
    except KeyboardInterrupt:
        print("\nSelesai")


if __name__ == "__main__":
    main()
