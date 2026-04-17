#!/usr/bin/env python3
"""
Bab 1 - Konsep Input Output
Button sebagai input, LED sebagai output.
"""

from signal import pause

from gpiozero import Button, Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


LED_PIN = 17
BUTTON_PIN = 24


def main():
    print("=== Demo Konsep Input/Output ===")
    print("Saat tombol ditekan -> LED menyala")
    print("Saat tombol dilepas -> LED mati")

    led = LED(LED_PIN)
    button = Button(BUTTON_PIN)

    button.when_pressed = led.on
    button.when_released = led.off

    print("Menunggu event tombol. Ctrl+C untuk keluar.")
    pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Program dihentikan.")
