# modules/sensors.py
from gpiozero import DistanceSensor, LineSensor
from config import *
from modules.config_loader import cfg_mgr

class SensorManager:
    def __init__(self):
        # 1. ULTRASONIC
        trig = cfg_mgr.get_pin("ultrasonic", "trig", PIN_HCSR_TRIG)
        echo = cfg_mgr.get_pin("ultrasonic", "echo", PIN_HCSR_ECHO)
        
        try:
            self.hcsr = DistanceSensor(echo=echo, trigger=trig)
            print(f"[SENSORS] HC-SR04 Active (T:{trig}, E:{echo})")
        except:
            self.hcsr = None

        # 2. LINE FOLLOWER (5 Channel)
        # Ambil pin dari config atau user define
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
        except:
            print("[SENSORS] Line Sensors Failed")

    def close(self):
        """Melepas resource GPIO"""
        if self.hcsr: self.hcsr.close()
        for s in self.lines.values(): s.close()
        
    def get_distance(self):
        if self.hcsr: return round(self.hcsr.distance * 100, 1)
        return 0

    def get_line_status(self):
        # Return list [1, 0, 1, 0, 0] (Active High/Low logic)
        res = []
        keys = ["LL", "L", "M", "R", "RR"]
        for k in keys:
            if k in self.lines:
                # Sesuaikan logic (LineSensor value 1 jika active/hitam)
                res.append(int(self.lines[k].value))
            else:
                res.append(0)
        return res