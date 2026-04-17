#!/usr/bin/env python3
"""
Bab 2 - LED Blink dengan Delay
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
    print("Blink LED. Ctrl+C untuk berhenti.")
    try:
        while True:
            led.on()
            print("ON")
            sleep(1)
            led.off()
            print("OFF")
            sleep(1)
    except KeyboardInterrupt:
        led.off()
        print("Selesai")


if __name__ == "__main__":
    main()
