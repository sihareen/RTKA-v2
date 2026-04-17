#!/usr/bin/env python3
"""
Bab 6 - Challenge dan Eksperimen Mandiri
Template sederhana untuk mencoba ide sendiri.
"""

import random
from time import sleep

from gpiozero import Buzzer, Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


LED_PIN = 17
BUZZER_PIN = 23


def random_pattern(led, buzzer):
    duration = random.choice([0.05, 0.1, 0.2, 0.3])
    led.toggle()
    buzzer.toggle()
    sleep(duration)


def main():
    print("Challenge mode:")
    print("1) Ubah pola random menjadi pola deterministik")
    print("2) Tambahkan input tombol untuk mengganti mode")
    print("3) Integrasikan sensor jarak untuk trigger otomatis")

    led = LED(LED_PIN)
    buzzer = Buzzer(BUZZER_PIN, active_high=False)

    try:
        while True:
            random_pattern(led, buzzer)
    except KeyboardInterrupt:
        led.off()
        buzzer.off()
        print("Program challenge selesai.")


if __name__ == "__main__":
    main()
