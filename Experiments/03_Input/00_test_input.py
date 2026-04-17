#!/usr/bin/env python3
"""
Bab 3 - Test Input Dasar
Menguji apakah button terbaca.
"""

from time import sleep

from gpiozero import Button, Device

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


BUTTON_PIN = 24


def main():
    button = Button(BUTTON_PIN)
    print("=== Test Input ===")
    print("Tekan tombol beberapa kali. Ctrl+C untuk berhenti.")

    try:
        while True:
            print("DITEKAN" if button.is_pressed else "LEPAS", end="\r")
            sleep(0.2)
    except KeyboardInterrupt:
        print("\nSelesai")


if __name__ == "__main__":
    main()
