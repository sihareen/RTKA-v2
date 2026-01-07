#!/usr/bin/env python3
import os
import sys
import json
import time
import asyncio
import logging
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# =========================================================
# CONFIG INLINE
# =========================================================

HOST = "0.0.0.0"
PORT = 8000

VIDEO_SOURCE = -1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- MOTOR ---
PIN_FL_FWD = 17
PIN_FL_BWD = 27
PIN_RL_FWD = 22
PIN_RL_BWD = 23
PIN_FR_FWD = 24
PIN_FR_BWD = 25
PIN_RR_FWD = 5
PIN_RR_BWD = 6
MIN_PWM = 0.40

# --- BUZZER ---
PIN_BUZZER = 16

# --- QR ---
MIN_QR_AREA_RATIO = 0.01
QR_COOLDOWN = 2.0   # detik

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-qr-command")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"

# =========================================================
# HARDWARE
# =========================================================

from gpiozero import Motor, PWMOutputDevice
import cv2
import numpy as np
from pyzbar.pyzbar import decode

class MotorDriver:
    def __init__(self):
        self.FL = Motor(PIN_FL_FWD, PIN_FL_BWD)
        self.RL = Motor(PIN_RL_FWD, PIN_RL_BWD)
        self.FR = Motor(PIN_FR_FWD, PIN_FR_BWD)
        self.RR = Motor(PIN_RR_FWD, PIN_RR_BWD)

    def _map(self, v):
        if abs(v) < 0.05: return 0
        sign = 1 if v > 0 else -1
        v = abs(v)
        return sign * (MIN_PWM + v * (1 - MIN_PWM))

    def move(self, throttle):
        val = self._map(throttle)
        for m in (self.FL, self.RL, self.FR, self.RR):
            m.value = val

    def stop(self):
        for m in (self.FL, self.RL, self.FR, self.RR):
            m.stop()

class Buzzer:
    def __init__(self):
        self.buzzer = PWMOutputDevice(PIN_BUZZER)

    def beep(self, freq=2000, dur=0.2):
        self.buzzer.frequency = freq
        self.buzzer.value = 0.5
        time.sleep(dur)
        self.buzzer.off()

    def play_song(self, notes):
        for freq, dur in notes:
            if freq == 0:
                self.buzzer.off()
            else:
                self.buzzer.frequency = freq
                self.buzzer.value = 0.5
            time.sleep(dur)
        self.buzzer.off()

SONGS = {
    "TWINKLE": [(262,0.3),(262,0.3),(392,0.3),(392,0.3),(440,0.3),(440,0.3),(392,0.6)],
    "MERRY": [(392,0.3),(523,0.3),(523,0.3),(587,0.3),(523,0.3)],
    "BIRTHDAY": [(262,0.3),(262,0.3),(294,0.6),(262,0.6),(349,0.6),(330,1.0)]
}

# =========================================================
# AI PROCESSOR (QR)
# =========================================================

class AIProcessor:
    def __init__(self):
        self.last_qr = None
        self.last_time = 0
        self.last_text = "---"

    def process_frame(self, frame):
        h, w, _ = frame.shape
        decoded = decode(frame)
        now = time.time()

        for obj in decoded:
            text = obj.data.decode("utf-8").strip().upper()
            x,y,wq,hq = obj.rect
            area_ratio = (wq*hq)/(w*h)

            if area_ratio < MIN_QR_AREA_RATIO:
                continue

            if text != self.last_qr or (now - self.last_time) > QR_COOLDOWN:
                self.last_qr = text
                self.last_time = now
                self.last_text = text
                handle_qr_command(text)

            pts = np.array(obj.polygon, np.int32).reshape((-1,1,2))
            cv2.polylines(frame, [pts], True, (255,0,255), 3)

        cv2.rectangle(frame, (5,5), (400,40), (0,0,0), -1)
        cv2.putText(frame, f"QR: {self.last_text}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        return frame

# =========================================================
# COMMAND HANDLER
# =========================================================

motor = MotorDriver()
buzzer = Buzzer()

def handle_qr_command(cmd):
    logger.info(f"[QR CMD] {cmd}")

    def run():
        if cmd == "MAJU":
            motor.move(0.4)
            time.sleep(2)
            motor.stop()

        elif cmd == "MUNDUR":
            motor.move(-0.4)
            time.sleep(2)
            motor.stop()

        elif cmd == "STOP":
            motor.stop()

        elif cmd == "BEEP":
            buzzer.beep()

        elif cmd in SONGS:
            buzzer.play_song(SONGS[cmd])

    threading.Thread(target=run, daemon=True).start()

# =========================================================
# CAMERA
# =========================================================

class VideoStreamer:
    def __init__(self):
        self.cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.ai = AIProcessor()

    def generate_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            frame = self.ai.process_frame(frame)
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n"
                   + buf.tobytes() + b"\r\n")

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
camera = VideoStreamer()

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(camera.generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame")

@app.websocket("/ws/qr")
async def ws_qr(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
