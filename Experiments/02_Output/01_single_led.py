#!/usr/bin/env python3
"""
Bab 2 - Menyalakan LED Single
"""

from time import sleep

from gpiozero import Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


LED_PIN = 17


def main():
    led = LED(LED_PIN)
    print("LED ON 5 detik")
    led.on()
    sleep(5)
    led.off()
    print("LED OFF")


if __name__ == "__main__":
    main()
