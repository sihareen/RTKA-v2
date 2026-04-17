#!/usr/bin/env python3
"""
Bab 1 - Tegangan dan Logika Digital
Mendemokan HIGH/LOW pada pin output.
"""

from time import sleep

from gpiozero import Device, OutputDevice

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


OUTPUT_PIN = 17


def main():
    print("=== Demo HIGH / LOW ===")
    print(f"Pin GPIO {OUTPUT_PIN} akan berganti HIGH/LOW setiap 1 detik")

    out = OutputDevice(OUTPUT_PIN, active_high=True, initial_value=False)

    try:
        while True:
            out.on()
            print("HIGH (3.3V)")
            sleep(1)

            out.off()
            print("LOW (0V)")
            sleep(1)
    except KeyboardInterrupt:
        out.off()
        print("Program dihentikan.")


if __name__ == "__main__":
    main()
