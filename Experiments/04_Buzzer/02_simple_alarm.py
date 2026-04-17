#!/usr/bin/env python3
"""
Bab 4 - Alarm Sederhana
"""

from time import sleep

from gpiozero import Buzzer, Device

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


BUZZER_PIN = 23


def main():
    buzzer = Buzzer(BUZZER_PIN, active_high=False)
    print("Mode alarm: 3 siklus (beep cepat)")

    for _ in range(3):
        for _ in range(6):
            buzzer.on()
            sleep(0.08)
            buzzer.off()
            sleep(0.08)
        sleep(0.5)

    print("Alarm selesai")


if __name__ == "__main__":
    main()
