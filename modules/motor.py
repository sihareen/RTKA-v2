# modules/motor.py
from config import *
from gpiozero import Motor

class MotorDriver:
    def __init__(self, simulation=False):
        self.simulation = simulation
        # --- KONFIGURASI AMBANG BATAS ---
        self.MIN_PWM = 0.40  # 40% adalah batas bawah agar roda mulai berputar
        
        print(f"[INIT] Motor Driver Start. Simulation: {self.simulation}")
        
        self.motor_FL = None 
        self.motor_RL = None 
        self.motor_FR = None 
        self.motor_RR = None 

        if not self.simulation:
            try:
                # Sisi Kiri
                self.motor_FL = Motor(forward=PIN_FL_FWD, backward=PIN_FL_BWD)
                self.motor_RL = Motor(forward=PIN_RL_FWD, backward=PIN_RL_BWD)
                
                # Sisi Kanan
                self.motor_FR = Motor(forward=PIN_FR_FWD, backward=PIN_FR_BWD)
                self.motor_RR = Motor(forward=PIN_RR_FWD, backward=PIN_RR_BWD)
                
                print(f"[HARDWARE] 4WD Motors Ready. Min Speed set to {int(self.MIN_PWM*100)}%")
            except Exception as e:
                print(f"[ERROR] Gagal init motor: {e}")
                self.simulation = True

    def _map_speed(self, val):
        """
        Mengubah nilai 0.0 - 1.0 menjadi 0.4 - 1.0
        Agar saat gas disentuh sedikit, motor langsung punya tenaga.
        """
        # 1. Deadzone Stick (Abaikan getaran kecil joystick)
        if abs(val) < 0.05: 
            return 0.0
        
        # 2. Simpan Arah (+ atau -)
        sign = 1 if val > 0 else -1
        val_abs = abs(val)

        # 3. Rumus Mapping:
        # Output = 0.4 + (Input * (1.0 - 0.4))
        # Contoh: Input 0.1 (10%) -> 0.4 + 0.06 = 0.46 (46%)
        mapped_val = self.MIN_PWM + (val_abs * (1.0 - self.MIN_PWM))
        
        return mapped_val * sign

    def move(self, throttle, steering, speed_limit=100):
        # 1. Mixing Logic (Arcade)
        left_val = throttle + steering
        right_val = throttle - steering

        # 2. Clamping Dasar (-1.0 s/d 1.0)
        left_val = max(-1.0, min(1.0, left_val))
        right_val = max(-1.0, min(1.0, right_val))
        
        # 3. Terapkan Speed Limit dari Slider App
        # Misal limit 80%, maka max value jadi 0.8
        scale = max(0, min(100, speed_limit)) / 100.0
        left_val *= scale
        right_val *= scale

        # 4. Terapkan MINIMUM SPEED OFFSET (Revisi Anda)
        # Hanya apply jika nilainya tidak 0
        final_left = self._map_speed(left_val)
        final_right = self._map_speed(right_val)

        # 5. Output ke Hardware
        if self.simulation:
            self._visualize(final_left, final_right, speed_limit)
        else:
            # Grup Kiri
            if self.motor_FL: self.motor_FL.value = final_left
            if self.motor_RL: self.motor_RL.value = final_left
            
            # Grup Kanan
            if self.motor_FR: self.motor_FR.value = final_right
            if self.motor_RR: self.motor_RR.value = final_right

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