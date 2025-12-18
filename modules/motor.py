# modules/motor.py
from config import *
from gpiozero import Motor

class MotorDriver:
    def __init__(self, simulation=False):
        self.simulation = simulation
        print(f"[INIT] Motor Driver Start. Simulation: {self.simulation}")
        
        self.motor_FL = None # Front Left
        self.motor_RL = None # Rear Left
        self.motor_FR = None # Front Right
        self.motor_RR = None # Rear Right

        if not self.simulation:
            try:
                # --- INISIALISASI 4 MOTOR ---
                # Sisi Kiri
                self.motor_FL = Motor(forward=PIN_FL_FWD, backward=PIN_FL_BWD)
                self.motor_RL = Motor(forward=PIN_RL_FWD, backward=PIN_RL_BWD)
                
                # Sisi Kanan
                self.motor_FR = Motor(forward=PIN_FR_FWD, backward=PIN_FR_BWD)
                self.motor_RR = Motor(forward=PIN_RR_FWD, backward=PIN_RR_BWD)
                
                print("[HARDWARE] 4WD Motors Connected via gpiozero.")
            except Exception as e:
                print(f"[ERROR] Gagal init motor: {e}")
                self.simulation = True

    def move(self, throttle, steering, speed_limit=100):
        # 1. Mixing Logic (Arcade Drive)
        left_val = throttle + steering
        right_val = throttle - steering

        # 2. Clamping (-1.0 s/d 1.0)
        left_val = max(-1.0, min(1.0, left_val))
        right_val = max(-1.0, min(1.0, right_val))
        
        # 3. Speed Limit Scaling
        scale = max(0, min(100, speed_limit)) / 100.0
        left_val *= scale
        right_val *= scale

        # 4. Output ke 4 Roda
        if self.simulation:
            self._visualize(left_val, right_val, speed_limit)
        else:
            # Grup Kiri
            if self.motor_FL: self.motor_FL.value = left_val
            if self.motor_RL: self.motor_RL.value = left_val
            
            # Grup Kanan
            if self.motor_FR: self.motor_FR.value = right_val
            if self.motor_RR: self.motor_RR.value = right_val

    def stop(self):
        if self.simulation: 
            print("\r[STOP] Motors Halted.                    ", end="")
        else:
            if self.motor_FL: self.motor_FL.stop()
            if self.motor_RL: self.motor_RL.stop()
            if self.motor_FR: self.motor_FR.stop()
            if self.motor_RR: self.motor_RR.stop()

    def _visualize(self, left, right, limit):
        def get_bar(val):
            return "█" * int(abs(val) * 10) if val > 0 else "░" * int(abs(val) * 10)
        print(f"\r[PWM {limit}%] L:{left:+.2f} {get_bar(left):<10} | R:{right:+.2f} {get_bar(right):<10}", end="")
