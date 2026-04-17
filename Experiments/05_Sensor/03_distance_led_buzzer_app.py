#!/usr/bin/env python3
"""
Bab 5 - Aplikasi Sensor Jarak + LED/Buzzer
LED dan buzzer aktif saat objek terlalu dekat.
"""

from time import sleep

from gpiozero import Buzzer, Device, DistanceSensor, LED

try:
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
except Exception:
    pass


TRIG_PIN = 5
ECHO_PIN = 6
LED_PIN = 17
BUZZER_PIN = 23
THRESHOLD_CM = 20


def main():
    sensor = DistanceSensor(trigger=TRIG_PIN, echo=ECHO_PIN, max_distance=4)
    led = LED(LED_PIN)
    buzzer = Buzzer(BUZZER_PIN, active_high=False)

    print(f"Alarm aktif jika jarak < {THRESHOLD_CM} cm. Ctrl+C untuk berhenti.")

    try:
        while True:
            distance_cm = sensor.distance * 100
            if distance_cm < THRESHOLD_CM:
                led.on()
                buzzer.on()
                status = "DEKAT"
            else:
                led.off()
                buzzer.off()
                status = "AMAN"

            print(f"jarak={distance_cm:6.2f} cm | status={status}", end="\r")
            sleep(0.1)
    except KeyboardInterrupt:
        led.off()
        buzzer.off()
        print("\nSelesai")


if __name__ == "__main__":
    main()
