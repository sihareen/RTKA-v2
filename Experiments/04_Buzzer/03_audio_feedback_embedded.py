#!/usr/bin/env python3
"""
Bab 4 - Feedback Audio untuk Sistem Embedded
Pola bunyi untuk status: OK, WARNING, ERROR.
"""

from time import sleep

from gpiozero import Buzzer, Device

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


BUZZER_PIN = 23


def beep(buzzer, on_time, off_time, repeat):
    for _ in range(repeat):
        buzzer.on()
        sleep(on_time)
        buzzer.off()
        sleep(off_time)


def feedback_ok(buzzer):
    beep(buzzer, 0.08, 0.05, 1)


def feedback_warning(buzzer):
    beep(buzzer, 0.12, 0.08, 2)


def feedback_error(buzzer):
    beep(buzzer, 0.2, 0.1, 3)


def main():
    buzzer = Buzzer(BUZZER_PIN, active_high=False)
    print("Demo feedback audio: OK -> WARNING -> ERROR")

    feedback_ok(buzzer)
    sleep(0.5)
    feedback_warning(buzzer)
    sleep(0.5)
    feedback_error(buzzer)


if __name__ == "__main__":
    main()
