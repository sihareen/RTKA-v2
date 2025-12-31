from gpiozero import DistanceSensor, DigitalInputDevice, Device
from gpiozero.pins.lgpio import LGPIOFactory
from config import *
from modules.config_loader import cfg_mgr
import logging

logger = logging.getLogger(__name__)

# Setup Pin Factory (Khusus Raspberry Pi 5 / Bookworm)
try:
    factory = LGPIOFactory()
    Device.pin_factory = factory
except:
    pass 

class SensorManager:
    def __init__(self):
        # 1. ULTRASONIC (HC-SR04)
        trig = cfg_mgr.get_pin("ultrasonic", "trig", PIN_HCSR_TRIG)
        echo = cfg_mgr.get_pin("ultrasonic", "echo", PIN_HCSR_ECHO)
        
        try:
            # Init sensor (Non-blocking init)
            self.hcsr = DistanceSensor(echo=echo, trigger=trig, max_distance=4.0)
            logger.info(f"HC-SR04 Initialized (T:{trig}, E:{echo})")
        except Exception as e:
            logger.error(f"HC-SR04 Init Failed: {e}")
            self.hcsr = None

        # 2. LINE SENSORS (BFD-1000 5 Channel)
        # Menggunakan DigitalInputDevice agar lebih stabil di RPi 5
        self.line_map = {
            "LL": cfg_mgr.get_pin("line", "ll", PIN_LINE_LL),
            "L":  cfg_mgr.get_pin("line", "l",  PIN_LINE_L),
            "M":  cfg_mgr.get_pin("line", "m",  PIN_LINE_M),
            "R":  cfg_mgr.get_pin("line", "r",  PIN_LINE_R),
            "RR": cfg_mgr.get_pin("line", "rr", PIN_LINE_RR)
        }
        
        self.lines = {}
        for name, pin in self.line_map.items():
            try:
                # pull_up=False: Asumsi sensor output 1 (High) jika kena garis hitam
                self.lines[name] = DigitalInputDevice(pin, pull_up=False)
            except Exception:
                self.lines[name] = None

        # 3. EMERGENCY SENSORS (BFD Near & Clap)
        self.bfd_near = None
        self.bfd_clap = None
        
        p_near = cfg_mgr.get_pin("emergency", "near", PIN_BFD_NEAR)
        p_clap = cfg_mgr.get_pin("emergency", "clap", PIN_BFD_CLAP)

        try:
            # Sensor BFD biasanya Active LOW (0 = Deteksi) -> pull_up=True
            if p_near: self.bfd_near = DigitalInputDevice(p_near, pull_up=True)
            if p_clap: self.bfd_clap = DigitalInputDevice(p_clap, pull_up=True)
            logger.info("Emergency Sensors Initialized")
        except: pass

    def close(self):
        if self.hcsr: self.hcsr.close()
        for s in self.lines.values():
            if s: s.close()
        if self.bfd_near: self.bfd_near.close()
        if self.bfd_clap: self.bfd_clap.close()

    def get_distance(self):
        """
        Mengembalikan jarak dalam CM.
        Return None jika sensor error/disconnect/timeout.
        """
        if self.hcsr is None:
            return None
            
        try:
            # Membaca sensor (bisa blocking sebentar jika timeout)
            # Property .distance mengembalikan meter, kita ubah ke cm
            return round(self.hcsr.distance * 100, 1)
        except Exception:
            # Jika sensor dicabut atau timeout -> Return None
            return None

    def get_line_status(self):
        """
        Return list status [LL, L, M, R, RR].
        Nilai 1 = Garis Hitam, 0 = Putih.
        """
        res = []
        order = ["LL", "L", "M", "R", "RR"]
        for key in order:
            s = self.lines.get(key)
            res.append(s.value if s else 0)
        return res

    def check_panic(self):
        """
        Return True jika mau nabrak (Near/Clap active).
        Aman dipanggil walau sensor tidak dipasang (Return False).
        """
        # Cek Near (Active Low)
        if self.bfd_near and self.bfd_near.value == 0:
            return True
            
        # Cek Clap (Active Low)
        if self.bfd_clap and self.bfd_clap.value == 0:
            return True
            
        return False