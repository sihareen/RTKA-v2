#!/usr/bin/env python3
"""
Bab 6 - Mini Project: Sistem Alarm Jarak
"""

from collections import deque
from statistics import mean
from time import sleep

from gpiozero import Buzzer, Device, DistanceSensor, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


TRIG_PIN = 5
ECHO_PIN = 6
LED_PIN = 17
BUZZER_PIN = 23

LEVEL_NEAR = 15
LEVEL_MID = 30


def alarm_pattern(buzzer, mode):
    if mode == "near":
        buzzer.on()
    elif mode == "mid":
        buzzer.on()
        sleep(0.05)
        buzzer.off()
    else:
        buzzer.off()


def main():
    sensor = DistanceSensor(trigger=TRIG_PIN, echo=ECHO_PIN, max_distance=4)
    led = LED(LED_PIN)
    buzzer = Buzzer(BUZZER_PIN, active_high=False)

    window = deque(maxlen=5)

    print("Distance Alarm System aktif. Ctrl+C untuk berhenti.")
    try:
        while True:
            raw_cm = sensor.distance * 100
            window.append(raw_cm)
            distance_cm = mean(window)

            if distance_cm < LEVEL_NEAR:
                mode = "near"
                led.blink(on_time=0.1, off_time=0.1, background=True)
            elif distance_cm < LEVEL_MID:
                mode = "mid"
                led.blink(on_time=0.3, off_time=0.3, background=True)
            else:
                mode = "safe"
                led.off()

            alarm_pattern(buzzer, mode)
            print(f"distance={distance_cm:6.2f} cm | mode={mode}", end="\r")
            sleep(0.1)
    except KeyboardInterrupt:
        led.off()
        buzzer.off()
        print("\nSelesai")


if __name__ == "__main__":
    main()
