#!/usr/bin/env python3
"""
Bab 2 - Kontrol LED dengan Fungsi Python
"""

from time import sleep

from gpiozero import Device, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


LED_PIN = 17
led = LED(LED_PIN)


def led_on():
    led.on()


def led_off():
    led.off()


def led_blink(delay_time=0.5, repeat=5):
    for _ in range(repeat):
        led_on()
        sleep(delay_time)
        led_off()
        sleep(delay_time)


def main():
    print("LED ON selama 2 detik")
    led_on()
    sleep(2)
    print("LED Blink 5 kali")
    led_blink(0.5, 5)
    led_off()


if __name__ == "__main__":
    try:
        main()
    finally:
        led_off()
