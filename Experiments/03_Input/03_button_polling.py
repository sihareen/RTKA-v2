#!/usr/bin/env python3
"""
Bab 3 - Polling Input Tombol
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
    print("Polling tombol (0.5 detik sekali). Ctrl+C untuk berhenti.")

    try:
        while True:
            if button.is_pressed:
                print("Tombol ditekan")
            else:
                print("Tombol tidak ditekan")
            sleep(0.5)
    except KeyboardInterrupt:
        print("Program dihentikan.")


if __name__ == "__main__":
    main()
