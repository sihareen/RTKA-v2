from gpiozero import PWMOutputDevice, AngularServo, LED, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time
import threading
import math
from config import *
from modules.config_loader import cfg_mgr

# --- INIT PIN FACTORY ---
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass 

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
        # 1. INIT PINS
        pin_buzzer = cfg_mgr.get_pin("buzzer", "pin", PIN_BUZZER)
        pin_pan = cfg_mgr.get_pin("servo", "pan_pin", PIN_SERVO_PAN)
        pin_tilt = cfg_mgr.get_pin("servo", "tilt_pin", PIN_SERVO_TILT)

        print(f"[EXTRAS] Init. Buzzer:{pin_buzzer}, Pan:{pin_pan}, Tilt:{pin_tilt}")
        
        try:
            self.buzzer = PWMOutputDevice(pin_buzzer, initial_value=0, frequency=440)
        except: self.buzzer = None

        try:
            # KONFIGURASI SERVO (SESUAI TEMUAN TUNING)
            # Range: -90 s/d 90
            self.servo_pan = AngularServo(
                pin_pan, 
                min_angle=-90, max_angle=90, 
                min_pulse_width=0.5/1000, 
                max_pulse_width=2.5/1000
            )
            self.servo_tilt = AngularServo(
                pin_tilt, 
                min_angle=-90, max_angle=90, 
                min_pulse_width=0.5/1000, 
                max_pulse_width=2.5/1000
            )
            
            # Simpan posisi terakhir
            self.last_pan_angle = 0
            self.last_tilt_angle = 0
            
            # Reset ke Tengah saat booting
            self.servo_pan.angle = 0
            self.servo_tilt.angle = 0
            time.sleep(0.5)
            self.detach_servos()
            print("[EXTRAS] Servos Ready (Micro-Overshoot Mode)")
            
        except Exception as e:
            print(f"[EXTRAS] Error Servo: {e}")
            self.servo_pan = None
            self.servo_tilt = None

        # 2. INIT LED
        p_r = cfg_mgr.get_pin("led", "r", PIN_LED_R)
        p_y = cfg_mgr.get_pin("led", "y", PIN_LED_Y)
        p_g = cfg_mgr.get_pin("led", "g", PIN_LED_G)

        try:
            self.led_r = LED(p_r)
            self.led_y = LED(p_y)
            self.led_g = LED(p_g)
        except:
            self.led_r = None; self.led_y = None; self.led_g = None

    def close(self):
        if self.buzzer: self.buzzer.close()
        if self.servo_pan: self.servo_pan.close()
        if self.servo_tilt: self.servo_tilt.close()
        if self.led_r: self.led_r.close()
        if self.led_y: self.led_y.close()
        if self.led_g: self.led_g.close()

    def detach_servos(self):
        """Mematikan sinyal servo total"""
        if self.servo_pan: self.servo_pan.detach()
        if self.servo_tilt: self.servo_tilt.detach()

    # ==========================================================
    # 1. MOVE SERVO (REVISI: MICRO-OVERSHOOT)
    # ==========================================================
    def move_servo(self, type, angle):
        """
        Menggerakkan servo dengan logika 'Micro-Overshoot'.
        Hanya 'melebihkan' sedikit (5-8 derajat) agar tidak macet,
        tapi tidak terlalu kasar.
        """
        angle = int(max(-90, min(90, angle)))
        
        target_servo = None
        last_angle = 0
        
        if type == "pan" and self.servo_pan:
            target_servo = self.servo_pan
            last_angle = self.last_pan_angle
        elif type == "tilt" and self.servo_tilt:
            target_servo = self.servo_tilt
            last_angle = self.last_tilt_angle
            
        if target_servo:
            diff = abs(angle - last_angle)
            
            # 1. Deadzone: Jika perubahan < 3 derajat, abaikan saja.
            # Ini mencegah servo 'menggigil' tidak perlu.
            if diff < 3:
                return 

            # 2. Ambang Batas Macet (Stiction)
            # Jika pergerakan antara 3 s/d 15 derajat, servo rentan macet.
            THRESHOLD_MACET = 15  
            MICRO_KICK = 6  # Cukup 6 derajat tambahannya (sebelumnya 30!)

            if diff < THRESHOLD_MACET:
                # --- LOGIKA MICRO-OVERSHOOT ---
                # Kita targetkan sedikit LEBIH JAUH dari tujuan asli
                # agar momentum cukup, lalu koreksi balik.
                
                overshoot_pos = 0
                
                # Cek arah gerak:
                if angle > last_angle: 
                    # Sedang bergerak ke arah Positif (+)
                    overshoot_pos = angle + MICRO_KICK
                else: 
                    # Sedang bergerak ke arah Negatif (-)
                    overshoot_pos = angle - MICRO_KICK
                
                # Pastikan overshoot tidak menabrak batas fisik -90/90
                overshoot_pos = max(-90, min(90, overshoot_pos))

                # Step A: Gerak ke posisi lebih (Pancingan Halus)
                target_servo.angle = overshoot_pos
                time.sleep(0.05) # Jeda sangat cepat
                
                # Step B: Koreksi ke posisi asli
                target_servo.angle = angle
                time.sleep(0.15) # Tunggu stabil

            else:
                # --- LOGIKA NORMAL (Jarak Jauh) ---
                # Jika jarak > 15 derajat, momentum sudah cukup besar.
                # Tidak perlu pancingan.
                target_servo.angle = angle
                time.sleep(0.2) 

            # Matikan sinyal (Detach)
            target_servo.detach()
            
            # Simpan posisi
            if type == "pan": self.last_pan_angle = angle
            else: self.last_tilt_angle = angle

    # ==========================================================
    # 2. SWIPE MOVE
    # ==========================================================
    def swipe_move(self, type, target_angle, duration=1.0, fps=50):
        target_servo = None
        start_angle = 0
        
        if type == "pan" and self.servo_pan:
            target_servo = self.servo_pan
            start_angle = self.last_pan_angle
        elif type == "tilt" and self.servo_tilt:
            target_servo = self.servo_tilt
            start_angle = self.last_tilt_angle
            
        if target_servo is None: return

        target_angle = max(-90, min(90, target_angle))
        
        # Jika jarak dekat, gunakan move_servo biasa agar aman dari macet
        if abs(target_angle - start_angle) < 15:
            self.move_servo(type, target_angle)
            return

        steps = int(duration * fps)
        for i in range(steps + 1):
            t = i / steps 
            eased = (1 - math.cos(math.pi * t)) / 2
            current_angle = start_angle + (target_angle - start_angle) * eased
            
            target_servo.angle = current_angle
            time.sleep(1 / fps)
            
        target_servo.angle = target_angle
        time.sleep(0.1)
        target_servo.detach()
        
        if type == "pan": self.last_pan_angle = target_angle
        else: self.last_tilt_angle = target_angle

    # --- LED & BUZZER ---
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
            self.buzzer.frequency = 2000 
            self.buzzer.value = 0.5      
        else:
            self.buzzer.off()

    def _play_worker(self, song_name):
        if self.buzzer is None: return
        notes, durations = SONGS[song_name]
        for note, duration in zip(notes, durations):
            freq = NOTES.get(note, 0)
            if freq > 0:
                self.buzzer.frequency = freq
                self.buzzer.value = 0.5 
            else:
                self.buzzer.off()
            time.sleep(duration)
            self.buzzer.off()
            time.sleep(0.05) 
        self.buzzer.off()

    def play_melody(self, song_name):
        if song_name not in SONGS: return 0
        notes, durations = SONGS[song_name]
        total_time = sum(durations) + (len(durations) * 0.05)
        t = threading.Thread(target=self._play_worker, args=(song_name,))
        t.start()
        return total_time
