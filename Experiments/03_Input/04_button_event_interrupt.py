#!/usr/bin/env python3
"""
Bab 3 - Event-driven Input (Interrupt sederhana)
"""

from signal import pause

from gpiozero import Button, Device

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


BUTTON_PIN = 24


def on_press():
    print("Event: Tombol ditekan")


def on_release():
    print("Event: Tombol dilepas")


def main():
    button = Button(BUTTON_PIN)
    button.when_pressed = on_press
    button.when_released = on_release

    print("Menunggu event tombol. Ctrl+C untuk berhenti.")
    pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program dihentikan.")
