from rpi_hardware_pwm import HardwarePWM
from gpiozero import PWMOutputDevice, LED, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time
import threading
import math
import os
from config import *
from modules.config_loader import cfg_mgr

# --- INIT PIN FACTORY ---
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except: pass 

# =========================
# DATABASE LAGU & NADA
# =========================
NOTES = { "C": 262, "D": 294, "E": 330, "F": 349, "G": 392, "A": 440, "B": 494, "C5": 523, "P": 0 }
SONGS = {
    "merry_christmas": (["G","C","C","D","C","B","A", "A","D","D","E","D","C","B","G", "G","E","C","D","C"],[0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.8, 1.0]),
    "twinkle": (["C","C","G","G","A","A","G", "F","F","E","E","D","D","C"],[0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.4,0.8]),
    "mary_lamb": (["E","D","C","D","E","E","E", "D","D","D", "E","G","G"],[0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.8, 0.4,0.4,0.8]),
    "balonku": (["G","E","C","E","G","G", "A","G","E","C"],[0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.8]),
    "cicak": (["E","G","A","A","A", "G","E","G","A","G","E"],[0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.4,0.8]),
    "pelangi": (["C","E","G","G","A","G","E", "D","E","F","E","C"],[0.4,0.4,0.4,0.4,0.4,0.4,0.8, 0.4,0.4,0.4,0.4,0.8]),
    "happy_birthday": (["C","C","D","C","F","E",  "C","C","D","C","G","F",  "C","C","C5","A","F","E","D", "F","F","A","F","G","F"],[0.3,0.3,0.6,0.6,0.6,1.0,  0.3,0.3,0.6,0.6,0.6,1.0,  0.3,0.3,0.6,0.6,0.6,0.6,1.0, 0.3,0.3,0.6,0.6,0.6,1.2])
}

class ExtraDrivers:
    def __init__(self):
        # 1. INIT PINS BUZZER
        pin_buzzer = cfg_mgr.get_pin("buzzer", "pin", PIN_BUZZER)
        print(f"[EXTRAS] Init. Buzzer:{pin_buzzer}")
        try:
            self.buzzer = PWMOutputDevice(pin_buzzer, initial_value=0, frequency=440)
        except: self.buzzer = None

        # 2. INIT SERVO (HARDWARE PWM)
        # Sesuai data Anda:
        # Channel 0 = GPIO 12 (Pan)
        # Channel 1 = GPIO 13 (Tilt)
        
        # DETEKSI OTOMATIS CHIP (Khusus RPi 5)
        # RPi 5 sering menggunakan pwmchip2 untuk GPIO, RPi 4 pwmchip0
        target_chip = 0
        if os.path.exists("/sys/class/pwm/pwmchip2"):
            target_chip = 2 # Kemungkinan RPi 5
            print("[EXTRAS] Deteksi RPi 5 (Using pwmchip2)")
        
        try:
            # Init PWM Channel 0 (Pan - GPIO 12)
            self.pwm_pan = HardwarePWM(pwm_channel=0, hz=50, chip=target_chip)
            self.pwm_pan.start(0) 

            # Init PWM Channel 1 (Tilt - GPIO 13)
            self.pwm_tilt = HardwarePWM(pwm_channel=1, hz=50, chip=target_chip)
            self.pwm_tilt.start(0) 
            
            self.last_pan_angle = 0
            self.last_tilt_angle = 0
            
            # Reset ke Tengah
            self.move_servo("pan", 0)
            self.move_servo("tilt", 0)
            time.sleep(0.5)
            self.detach_servos()
            
            print(f"[EXTRAS] Hardware PWM Ready (Ch0 & Ch1 on Chip {target_chip})")
            
        except Exception as e:
            print(f"[EXTRAS] Error Hardware PWM: {e}")
            print("TIPS: Cek overlay di /boot/firmware/config.txt -> dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4")
            self.pwm_pan = None
            self.pwm_tilt = None

        # 3. INIT LED
        p_r = cfg_mgr.get_pin("led", "r", PIN_LED_R)
        p_y = cfg_mgr.get_pin("led", "y", PIN_LED_Y)
        p_g = cfg_mgr.get_pin("led", "g", PIN_LED_G)

        try:
            self.led_r = LED(p_r); self.led_y = LED(p_y); self.led_g = LED(p_g)
        except:
            self.led_r = None; self.led_y = None; self.led_g = None

    def close(self):
        if self.buzzer: self.buzzer.close()
        if self.pwm_pan: self.pwm_pan.stop() 
        if self.pwm_tilt: self.pwm_tilt.stop()
        if self.led_r: self.led_r.close()
        if self.led_y: self.led_y.close()
        if self.led_g: self.led_g.close()

    def detach_servos(self):
        if self.pwm_pan: self.pwm_pan.change_duty_cycle(0)
        if self.pwm_tilt: self.pwm_tilt.change_duty_cycle(0)

    def _angle_to_duty(self, angle):
        """
        Konversi Sudut (-90 s/d 90) ke Duty Cycle Hardware PWM (%).
        -90 deg = 2.5% duty (0.5ms)
          0 deg = 7.5% duty (1.5ms)
         90 deg = 12.5% duty (2.5ms)
        """
        angle = max(-90, min(90, angle))
        duty = 7.5 + (angle / 90.0) * 5.0
        return duty

    # ==========================================================
    # 1. MOVE SERVO (HARDWARE PWM)
    # ==========================================================
    # ==========================================================
    # 1. MOVE SERVO (HARDWARE PWM - SOFT TUNED)
    # ==========================================================
    def move_servo(self, type, angle):
        angle = int(max(-90, min(90, angle)))
        
        target_pwm = None
        last_angle = 0
        
        if type == "pan" and self.pwm_pan:
            target_pwm = self.pwm_pan
            last_angle = self.last_pan_angle
        elif type == "tilt" and self.pwm_tilt:
            target_pwm = self.pwm_tilt
            last_angle = self.last_tilt_angle
            
        if target_pwm:
            diff = abs(angle - last_angle)
            
            # Deadzone: Abaikan pergerakan < 2 derajat (dikurangi dari 3)
            # Hardware PWM presisi, jadi kita bisa lebih sensitif
            if diff < 2: return 

            # --- SOFT TUNING ---
            # Karena Hardware PWM kuat, kita kurangi pancingannya.
            THRESHOLD_MACET = 3   # Turun dari 15 ke 8
            MICRO_KICK = 0        # Turun drastis dari 6 ke 2

            if diff < THRESHOLD_MACET:
                # Logika Pancingan Halus (Hanya ditambah 2 derajat)
                overshoot_angle = 0
                if angle > last_angle: overshoot_angle = angle + MICRO_KICK
                else: overshoot_angle = angle - MICRO_KICK
                
                overshoot_angle = max(-90, min(90, overshoot_angle))

                target_pwm.change_duty_cycle(self._angle_to_duty(overshoot_angle))
                time.sleep(0.05) 
                
                target_pwm.change_duty_cycle(self._angle_to_duty(angle))
                time.sleep(0.10) # Waktu tunggu dipercepat
            else:
                # Gerakan Normal
                target_pwm.change_duty_cycle(self._angle_to_duty(angle))
                time.sleep(0.15) # Waktu tunggu dipercepat

            # Matikan sinyal (Detach)
            target_pwm.change_duty_cycle(0)
            
            # Simpan posisi
            if type == "pan": self.last_pan_angle = angle
            else: self.last_tilt_angle = angle

    # ==========================================================
    # 2. SWIPE MOVE
    # ==========================================================
    def swipe_move(self, type, target_angle, duration=1.0, fps=50):
        target_pwm = None
        start_angle = 0
        
        if type == "pan" and self.pwm_pan:
            target_pwm = self.pwm_pan
            start_angle = self.last_pan_angle
        elif type == "tilt" and self.pwm_tilt:
            target_pwm = self.pwm_tilt
            start_angle = self.last_tilt_angle
            
        if target_pwm is None: return

        target_angle = max(-90, min(90, target_angle))
        
        if abs(target_angle - start_angle) < 15:
            self.move_servo(type, target_angle)
            return

        steps = int(duration * fps)
        for i in range(steps + 1):
            t = i / steps 
            eased = (1 - math.cos(math.pi * t)) / 2
            current_angle = start_angle + (target_angle - start_angle) * eased
            
            target_pwm.change_duty_cycle(self._angle_to_duty(current_angle))
            time.sleep(1 / fps)
            
        target_pwm.change_duty_cycle(self._angle_to_duty(target_angle))
        time.sleep(0.1)
        target_pwm.change_duty_cycle(0) 
        
        if type == "pan": self.last_pan_angle = target_angle
        else: self.last_tilt_angle = target_angle

    # --- LED & BUZZER (SAMA SEPERTI SEBELUMNYA) ---
    def set_led(self, color, state):
        target = None
        if color == "r": target = self.led_r
        elif color == "y": target = self.led_y
        elif color == "g": target = self.led_g
        if target:
            if state == "on" or state == 1: target.on()
            else: target.off()

    def set_buzzer(self, state):
        if self.buzzer is None: return
        if state == "on":
            self.buzzer.frequency = 2000; self.buzzer.value = 0.5      
        else: self.buzzer.off()

    def _play_worker(self, song_name):
        if self.buzzer is None: return
        notes, durations = SONGS[song_name]
        for note, duration in zip(notes, durations):
            freq = NOTES.get(note, 0)
            if freq > 0:
                self.buzzer.frequency = freq; self.buzzer.value = 0.5 
            else: self.buzzer.off()
            time.sleep(duration); self.buzzer.off(); time.sleep(0.05) 
        self.buzzer.off()

    def play_melody(self, song_name):
        if song_name not in SONGS: return 0
        notes, durations = SONGS[song_name]
        total_time = sum(durations) + (len(durations) * 0.05)
        t = threading.Thread(target=self._play_worker, args=(song_name,))
        t.start()
        return total_time