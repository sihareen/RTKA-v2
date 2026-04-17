#!/usr/bin/env python3
"""
Bab 1 - Test Setup GPIO
Menguji apakah library dan akses GPIO siap digunakan.
"""

from time import sleep

from gpiozero import Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    # Fallback ke default pin factory jika lgpio tidak tersedia.
    pass


LED_PIN = 17


def main():
    print("=== Test GPIO Setup ===")
    print(f"Menguji LED pada GPIO {LED_PIN}")

    try:
        led = LED(LED_PIN)
        led.on()
        print("LED ON (1 detik)")
        sleep(1)
        led.off()
        print("LED OFF")
        print("Setup GPIO siap digunakan.")
    except Exception as exc:
        print(f"Gagal akses GPIO: {exc}")
        print("Cek wiring, permission, atau jalankan di Raspberry Pi.")


if __name__ == "__main__":
    main()
