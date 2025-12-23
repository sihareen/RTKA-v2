# modules/motor.py
from config import *
from gpiozero import Motor
from modules.config_loader import cfg_mgr # IMPORT BARU

class MotorDriver:
    def __init__(self, simulation=False):
        self.simulation = simulation
        self.MIN_PWM = 0.40  
        
        print(f"[INIT] Motor Driver Start. User Mode: {cfg_mgr.use_user_config}")
        
        self.motor_FL = None 
        self.motor_RL = None 
        self.motor_FR = None 
        self.motor_RR = None 

        if not self.simulation:
            try:
                # --- MODIFIKASI: Ambil Pin dari ConfigManager ---
                # Sisi Kiri
                p_fl_fwd = cfg_mgr.get_pin("motor", "fl_fwd", PIN_FL_FWD)
                p_fl_bwd = cfg_mgr.get_pin("motor", "fl_bwd", PIN_FL_BWD)
                p_rl_fwd = cfg_mgr.get_pin("motor", "rl_fwd", PIN_RL_FWD)
                p_rl_bwd = cfg_mgr.get_pin("motor", "rl_bwd", PIN_RL_BWD)
                
                # Sisi Kanan
                p_fr_fwd = cfg_mgr.get_pin("motor", "fr_fwd", PIN_FR_FWD)
                p_fr_bwd = cfg_mgr.get_pin("motor", "fr_bwd", PIN_FR_BWD)
                p_rr_fwd = cfg_mgr.get_pin("motor", "rr_fwd", PIN_RR_FWD)
                p_rr_bwd = cfg_mgr.get_pin("motor", "rr_bwd", PIN_RR_BWD)

                # Init GPIOZero dengan Pin terpilih
                self.motor_FL = Motor(forward=p_fl_fwd, backward=p_fl_bwd)
                self.motor_RL = Motor(forward=p_rl_fwd, backward=p_rl_bwd)
                self.motor_FR = Motor(forward=p_fr_fwd, backward=p_fr_bwd)
                self.motor_RR = Motor(forward=p_rr_fwd, backward=p_rr_bwd)
                
                print(f"[HARDWARE] 4WD Motors Ready.")
            except Exception as e:
                print(f"[ERROR] Gagal init motor: {e}")
                self.simulation = True

    def close(self):
        """Melepas resource GPIO agar bisa dipakai User Define Mode"""
        print("[MOTOR] Closing resources...")
        if self.motor_FL: self.motor_FL.close()
        if self.motor_RL: self.motor_RL.close()
        if self.motor_FR: self.motor_FR.close()
        if self.motor_RR: self.motor_RR.close()
        self.motor_FL = None
        self.motor_RL = None
        self.motor_FR = None
        self.motor_RR = None

    def _map_speed(self, val):
        if abs(val) < 0.05: return 0.0
        sign = 1 if val > 0 else -1
        val_abs = abs(val)
        mapped_val = self.MIN_PWM + (val_abs * (1.0 - self.MIN_PWM))
        return mapped_val * sign

    def move(self, throttle, steering, speed_limit=100):
        left_val = throttle + steering
        right_val = throttle - steering

        left_val = max(-1.0, min(1.0, left_val))
        right_val = max(-1.0, min(1.0, right_val))
        
        scale = max(0, min(100, speed_limit)) / 100.0
        left_val *= scale
        right_val *= scale

        final_left = self._map_speed(left_val)
        final_right = self._map_speed(right_val)

        if self.simulation:
            self._visualize(final_left, final_right, speed_limit)
        else:
            if self.motor_FL: self.motor_FL.value = final_left
            if self.motor_RL: self.motor_RL.value = final_left
            if self.motor_FR: self.motor_FR.value = final_right
            if self.motor_RR: self.motor_RR.value = final_right

    def stop(self):
        if self.simulation: 
            pass
        else:
            if self.motor_FL: self.motor_FL.stop()
            if self.motor_RL: self.motor_RL.stop()
            if self.motor_FR: self.motor_FR.stop()
            if self.motor_RR: self.motor_RR.stop()

    def _visualize(self, left, right, limit):
        # ... (Visualisasi sama seperti sebelumnya) ...
        def get_bar(val):
            return "█" * int(abs(val) * 10) if val > 0 else "░" * int(abs(val) * 10)
        print(f"\r[PWM {limit}%] L:{left:+.2f} {get_bar(left):<10} | R:{right:+.2f} {get_bar(right):<10}", end="")
        pass
        