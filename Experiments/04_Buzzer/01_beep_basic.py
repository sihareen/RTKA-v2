#!/usr/bin/env python3
"""
Bab 4 - Membuat Bunyi Beep
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
    print("Beep pendek 5 kali")
    for _ in range(5):
        buzzer.on()
        sleep(0.2)
        buzzer.off()
        sleep(0.2)


if __name__ == "__main__":
    main()
