#!/usr/bin/env python3
"""
Bab 4 - Test Buzzer
Menjelaskan buzzer aktif/pasif dan tes bunyi dasar.
"""

from time import sleep

from gpiozero import Device, OutputDevice

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


BUZZER_PIN = 23


def main():
    print("=== Buzzer Aktif vs Pasif ===")
    print("Buzzer aktif: cukup ON/OFF")
    print("Buzzer pasif: butuh PWM/frekuensi untuk nada")

    buzzer = OutputDevice(BUZZER_PIN, active_high=False, initial_value=False)
    # active_high=False => logika LOW akan dianggap ON (active low board)

    print("Tes beep 2x")
    for _ in range(2):
        buzzer.on()
        sleep(0.3)
        buzzer.off()
        sleep(0.3)

    print("Test selesai")


if __name__ == "__main__":
    main()
