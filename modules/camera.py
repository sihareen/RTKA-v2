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
        self.frame_count = 0  # Counter untuk frame skipping

        # Init AI
        self.ai = AIProcessor()

        # Logic Download Simulasi (Jika bukan hardware)
        if not self.is_hardware and ("youtube" in str(self.source)):
            self.source = self._download_sim(self.source)

    def _download_sim(self, url):
        path = "assets/colour.mp4"
        if not os.path.exists("assets"):
            os.makedirs("assets")

        if os.path.exists(path):
            return path

        try:
            print("[CAM] Downloading Simulation Video...")
            with yt_dlp.YoutubeDL(
                {'outtmpl': path, 'format': 'best[ext=mp4]/best'}
            ) as ydl:
                ydl.download([url])
            return path
        except Exception:
            return url

    def set_ai_mode(self, mode):
        self.ai.set_mode(mode)

    def generate_frames(self):
        # --- SETUP CAMERA ---
        if self.is_hardware:
            # PENTING: Flag CAP_V4L2 Wajib untuk Raspberry Pi
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)

            # Paksa resolusi rendah agar lancar
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
                    print("[CAM] Frame drop detected. Reconnecting...")
                    self.cap.release()
                    time.sleep(2)
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)

                    # Set ulang resolusi setelah reconnect
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
                continue

            # Resize standard
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            self.frame_count += 1

            # --- AI PROCESSING STRATEGY ---
            # Hardware → frame skipping untuk hemat CPU
            skip_rate = 2 if self.is_hardware else 1

            if self.frame_count % skip_rate == 0:
                frame = self.ai.process_frame(frame)

            # Encode JPEG (Quality 60%)
            ret, buffer = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            )
            if not ret:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )
