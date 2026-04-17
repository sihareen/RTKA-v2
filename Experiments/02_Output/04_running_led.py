#!/usr/bin/env python3
"""
Bab 2 - Pola LED (Running LED)
"""

from time import sleep

from gpiozero import Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


LED_PINS = [17, 27, 22]


def main():
    leds = [LED(pin) for pin in LED_PINS]
    print("Running LED. Ctrl+C untuk berhenti.")

    try:
        while True:
            for led in leds:
                led.on()
                sleep(0.2)
                led.off()
    except KeyboardInterrupt:
        for led in leds:
            led.off()
        print("Selesai")


if __name__ == "__main__":
    main()
