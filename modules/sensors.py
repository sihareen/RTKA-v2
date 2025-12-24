# modules/sensors.py
from gpiozero import DistanceSensor, LineSensor, DigitalInputDevice
from config import *
from modules.config_loader import cfg_mgr

class SensorManager:
    def __init__(self):
        # 1. ULTRASONIC (Tetap Sama)
        trig = cfg_mgr.get_pin("ultrasonic", "trig", PIN_HCSR_TRIG)
        echo = cfg_mgr.get_pin("ultrasonic", "echo", PIN_HCSR_ECHO)
        try:
            self.hcsr = DistanceSensor(echo=echo, trigger=trig)
            print(f"[SENSORS] HC-SR04 Active (T:{trig}, E:{echo})")
        except: self.hcsr = None

        # 2. LINE FOLLOWER (Tetap Sama)
        p_ll = cfg_mgr.get_pin("line", "ll", PIN_LINE_LL)
        p_l  = cfg_mgr.get_pin("line", "l",  PIN_LINE_L)
        p_m  = cfg_mgr.get_pin("line", "m",  PIN_LINE_M)
        p_r  = cfg_mgr.get_pin("line", "r",  PIN_LINE_R)
        p_rr = cfg_mgr.get_pin("line", "rr", PIN_LINE_RR)

        self.lines = {}
        try:
            self.lines["LL"] = LineSensor(p_ll)
            self.lines["L"]  = LineSensor(p_l)
            self.lines["M"]  = LineSensor(p_m)
            self.lines["R"]  = LineSensor(p_r)
            self.lines["RR"] = LineSensor(p_rr)
            print("[SENSORS] Line Sensors Active")
        except: print("[SENSORS] Line Sensors Failed")

        # 3. EMERGENCY SENSORS (BARU: BFD-1000 Extras)
        # Kita bungkus try-except agar AMAN (Tidak Crash)
        p_near = cfg_mgr.get_pin("emergency", "near", PIN_BFD_NEAR)
        p_clap = cfg_mgr.get_pin("emergency", "clap", PIN_BFD_CLAP)

        self.bfd_near = None
        self.bfd_clap = None

        try:
            # pull_up=True karena biasanya sensor ini Active LOW (Ground saat trigger)
            if p_near: 
                self.bfd_near = DigitalInputDevice(p_near, pull_up=True)
            if p_clap: 
                self.bfd_clap = DigitalInputDevice(p_clap, pull_up=True)
            
            print(f"[SENSORS] Emergency Sensors Ready (Near:{p_near}, Clap:{p_clap})")
        except Exception as e:
            print(f"[SENSORS] Emergency Sensors Failed (Safe Mode): {e}")
            # Program tetap jalan, tapi sensor ini dianggap tidak ada

    def close(self):
        if self.hcsr: self.hcsr.close()
        for s in self.lines.values(): s.close()
        if self.bfd_near: self.bfd_near.close()
        if self.bfd_clap: self.bfd_clap.close()
        
    def get_distance(self):
        if self.hcsr: return round(self.hcsr.distance * 100, 1)
        return 999.0

    def get_line_status(self):
        try:
            return [
                1 if self.lines["LL"].value == 1 else 0,
                1 if self.lines["L"].value  == 1 else 0,
                1 if self.lines["M"].value  == 1 else 0,
                1 if self.lines["R"].value  == 1 else 0,
                1 if self.lines["RR"].value == 1 else 0
            ]
        except: return [0,0,0,0,0]

    # --- FUNGSI BARU UNTUK CEK TABRAKAN ---
    def check_panic(self):
        """
        Mengembalikan True jika sensor Near ATAU Clap terpicu.
        Aman dipanggil walau sensor rusak/tidak dipasang.
        """
        is_panic = False
        
        # Cek Near (IR Proximity) - Active Low (0 berarti ada benda)
        if self.bfd_near is not None:
            if self.bfd_near.value == 0: 
                is_panic = True
                
        # Cek Clap (Limit Switch) - Active Low (0 berarti tertabrak)
        if self.bfd_clap is not None:
            if self.bfd_clap.value == 0: 
                is_panic = True
                
        return is_panic