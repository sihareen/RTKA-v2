from gpiozero import DistanceSensor
from time import sleep
ultrasonic = DistanceSensor(echo=20, trigger=26)
try:
    while True:
        meter = ultrasonic.distance
        distance = meter * 100  # Jarak dalam meter (0.0 - 1.0)
        print(f"Jarak: {distance:.2f} cm")
        sleep(1)  
except KeyboardInterrupt:
    print("Program dihentikan")