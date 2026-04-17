#!/usr/bin/env python3
"""
Bab 2 - Test Output Dasar
Menguji LED tunggal dan LED sequence.
"""

from time import sleep

from gpiozero import Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


PINS = [17, 27, 22]


def main():
    leds = [LED(pin) for pin in PINS]
    print("=== Test Output Dasar ===")

    for i, led in enumerate(leds, start=1):
        led.on()
        print(f"LED-{i} ON")
        sleep(0.4)
        led.off()

    print("Output test selesai.")


if __name__ == "__main__":
    main()
