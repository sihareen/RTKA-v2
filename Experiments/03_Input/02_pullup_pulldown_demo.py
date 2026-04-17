#!/usr/bin/env python3
"""
Bab 3 - Pull-up dan Pull-down Resistor
Demo dua konfigurasi button.
"""

from time import sleep

from gpiozero import Button, Device

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


PIN_PULLUP = 24
PIN_PULLDOWN = 25


def main():
    print("=== Demo Pull-up/Pull-down ===")
    print("GPIO24: pull_up=True (default di gpiozero)")
    print("GPIO25: pull_up=False")

    btn_pullup = Button(PIN_PULLUP, pull_up=True)
    btn_pulldown = Button(PIN_PULLDOWN, pull_up=False)

    try:
        while True:
            print(
                f"pull_up(GPIO24)={btn_pullup.is_pressed} | "
                f"pull_down(GPIO25)={btn_pulldown.is_pressed}",
                end="\r",
            )
            sleep(0.2)
    except KeyboardInterrupt:
        print("\nSelesai")


if __name__ == "__main__":
    main()
