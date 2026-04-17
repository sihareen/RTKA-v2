#!/usr/bin/env python3
"""
Bab 3 - Push Button sebagai Input Digital
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
    print("Monitoring tombol digital...")
    print("True = ditekan, False = tidak ditekan")

    try:
        while True:
            print(f"is_pressed: {button.is_pressed}")
            sleep(0.5)
    except KeyboardInterrupt:
        print("Program dihentikan.")


if __name__ == "__main__":
    main()
