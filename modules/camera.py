import cv2
import yt_dlp
import os
import time
from config import *
from modules.ai import AIProcessor

class VideoStreamer:
    def __init__(self):
        self.cap = None
        self.source = VIDEO_SOURCE
        self.is_hardware = isinstance(self.source, int)
        self.frame_count = 0 # Counter untuk frame skipping
        
        # Init AI
        self.ai = AIProcessor()

        # Logic Download Simulasi (Jika bukan hardware)
        if not self.is_hardware and ("youtube" in str(self.source)):
            self.source = self._download_sim(self.source)

    def _download_sim(self, url):
        path = "assets/sim.mp4"
        if not os.path.exists("assets"): os.makedirs("assets")
        if os.path.exists(path): return path
        try:
            print("[CAM] Downloading Simulation Video...")
            with yt_dlp.YoutubeDL({'outtmpl': path, 'format':'best[ext=mp4]/best'}) as ydl:
                ydl.download([url])
            return path
        except: return url

    def set_ai_mode(self, mode):
        self.ai.set_mode(mode)

    def generate_frames(self):
        # --- SETUP CAMERA ---
        if self.is_hardware:
            # PENTING: Flag CAP_V4L2 Wajib untuk Raspberry Pi
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
            
            # Paksa resolusi rendah agar lancar (640x480)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        else:
            self.cap = cv2.VideoCapture(self.source)

        while True:
            success, frame = self.cap.read()
            if not success:
                # Reconnection Logic
                if not self.is_hardware: 
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else: 
                    self.cap.release()
                    time.sleep(1)
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
                continue

            # Resize standard
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            self.frame_count += 1

            # --- AI PROCESSING STRATEGY ---
            # Jika hardware asli, lakukan Frame Skipping untuk hemat CPU
            # Logic: Proses AI hanya pada frame GENAP (setiap 2 frame sekali)
            # frame_count % 1 == 0 -> Proses semua (Terberat)
            # frame_count % 2 == 0 -> Proses setengah (Sedang)
            # frame_count % 3 == 0 -> Proses sepertiga (Ringan)
            
            skip_rate = 2 if self.is_hardware else 1 

            if self.frame_count % skip_rate == 0:
                frame = self.ai.process_frame(frame)
            else:
                # Pada frame yang diskip, lewatkan frame mentah 
                # (Video lancar, tapi kotak AI mungkin berkedip. Ini trade-off performa)
                pass 

            # Encode Quality 60% (Cukup untuk FPV)
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ret: continue
            
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
