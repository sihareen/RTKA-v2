# modules/motor.py
from config import *

class MotorDriver:
    def __init__(self, simulation=True):
        self.simulation = simulation
        print(f"[INIT] Motor Driver Start. Simulation: {self.simulation}")
        
        if not self.simulation:
            # from gpiozero import Motor
            # self.motor_left = Motor(PIN_MOTOR_L_FWD, PIN_MOTOR_L_BWD)
            # self.motor_right = Motor(PIN_MOTOR_R_FWD, PIN_MOTOR_R_BWD)
            pass

    def move(self, throttle, steering, speed_limit=100):
        # 1. Arcade Drive Mixing
        left = throttle + steering
        right = throttle - steering

        # 2. Clamping (-1.0 to 1.0)
        left = max(-1.0, min(1.0, left))
        right = max(-1.0, min(1.0, right))
        
        # 3. Apply Speed Scaling
        scale = max(0, min(100, speed_limit)) / 100.0
        left *= scale
        right *= scale

        # 4. Output
        if self.simulation:
            self._visualize(left, right, speed_limit)
        else:
            # self.motor_left.value = left
            # self.motor_right.value = right
            pass

    def stop(self):
        if self.simulation: print("\r[STOP] Motors Halted.                    ", end="")
        else: pass # self.motor_left.stop()

    def _visualize(self, left, right, limit):
        def get_bar(val):
            return "█" * int(abs(val) * 15) if val > 0 else "░" * int(abs(val) * 15)
        print(f"\r[PWM {limit}%] L:{left:+.2f} {get_bar(left):<15} | R:{right:+.2f} {get_bar(right):<15}", end="")
