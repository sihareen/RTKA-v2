#!/usr/bin/env python3
import os
import sys
import json
import time
import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# =========================================================
# CONFIG INLINE (TRAINER KIT)
# =========================================================

HOST = "0.0.0.0"
PORT = 8000

# --- CAMERA ---
VIDEO_SOURCE = -1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- MOTOR PIN ---
PIN_FL_FWD = 17
PIN_FL_BWD = 27
PIN_RL_FWD = 22
PIN_RL_BWD = 23
PIN_FR_FWD = 24
PIN_FR_BWD = 25
PIN_RR_FWD = 5
PIN_RR_BWD = 6
MIN_PWM = 0.40

# --- BFD1000 (LL L M R RR) ---
PIN_LINE_LL = 4
PIN_LINE_L  = 14
PIN_LINE_M  = 15
PIN_LINE_R  = 18
PIN_LINE_RR = 21

# --- ULTRASONIC ---
PIN_HCSR_TRIG = 26
PIN_HCSR_ECHO = 20

# --- HYBRID PARAM ---
SAFE_DIST  = 30     # cm
BRAKE_DIST = 20     # cm

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-line-hybrid")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# HARDWARE
# =========================================================

from gpiozero import Motor, DigitalInputDevice, DistanceSensor

class MotorDriver:
    def __init__(self):
        self.FL = Motor(PIN_FL_FWD, PIN_FL_BWD)
        self.RL = Motor(PIN_RL_FWD, PIN_RL_BWD)
        self.FR = Motor(PIN_FR_FWD, PIN_FR_BWD)
        self.RR = Motor(PIN_RR_FWD, PIN_RR_BWD)

    def _map(self, v):
        if abs(v) < 0.05:
            return 0.0
        sign = 1 if v > 0 else -1
        v = abs(v)
        return sign * (MIN_PWM + v * (1.0 - MIN_PWM))

    def move(self, throttle, steering):
        l = self._map(throttle + steering)
        r = self._map(throttle - steering)
        self.FL.value = l
        self.RL.value = l
        self.FR.value = r
        self.RR.value = r

    def stop(self):
        for m in (self.FL, self.RL, self.FR, self.RR):
            m.stop()


class BFD1000:
    """
    Output:
    1 = garis hitam
    0 = putih
    """
    def __init__(self):
        self.ll = DigitalInputDevice(PIN_LINE_LL, pull_up=False)
        self.l  = DigitalInputDevice(PIN_LINE_L,  pull_up=False)
        self.m  = DigitalInputDevice(PIN_LINE_M,  pull_up=False)
        self.r  = DigitalInputDevice(PIN_LINE_R,  pull_up=False)
        self.rr = DigitalInputDevice(PIN_LINE_RR, pull_up=False)

    def read(self):
        return [
            self.ll.value,
            self.l.value,
            self.m.value,
            self.r.value,
            self.rr.value
        ]


class Ultrasonic:
    def __init__(self):
        self.sensor = DistanceSensor(
            trigger=PIN_HCSR_TRIG,
            echo=PIN_HCSR_ECHO,
            max_distance=4.0
        )

    def read_cm(self):
        try:
            return round(self.sensor.distance * 100, 1)
        except:
            return None

# =========================================================
# AI PROCESSOR (DISPLAY HYBRID)
# =========================================================

import cv2

class AIProcessor:
    def __init__(self):
        self.mode = "line_hybrid"
        self.distance = None
        self.lines = [0,0,0,0,0]
        self.mask  = [1,1,1,1,1]

    def update(self, dist, lines, mask):
        self.distance = dist
        self.lines = lines
        self.mask = mask

    def process_frame(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        # SAFEZONE
        zx = int(w * 0.15)
        zy = int(h * 0.15)
        cv2.rectangle(frame, (cx-zx, cy-zy), (cx+zx, cy+zy), (255,255,0), 1)

        # CROSSHAIR
        cv2.line(frame, (cx-10, cy), (cx+10, cy), (0,0,255), 1)
        cv2.line(frame, (cx, cy-10), (cx, cy+10), (0,0,255), 1)

        # HUD BACKGROUND
        cv2.rectangle(frame, (5,5), (300,140), (0,0,0), -1)

        # DISTANCE
        d_txt = "DIST: ---"
        d_col = (0,255,0)
        if self.distance is not None:
            d_txt = f"DIST: {self.distance:.1f} cm"
            if self.distance < BRAKE_DIST:
                d_col = (0,0,255)

        cv2.putText(frame, d_txt, (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, d_col, 2)

        # LINE STATUS
        cv2.putText(
            frame,
            f"LINE RAW : {self.lines}",
            (10,60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0,255,255),
            1
        )

        # MASK STATUS
        cv2.putText(
            frame,
            f"LINE MASK: {self.mask}",
            (10,85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255,255,0),
            1
        )

        # MODE
        cv2.putText(
            frame,
            "AI MODE: LINE + AVOID (HYBRID)",
            (10,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0,255,0),
            1
        )

        return frame

# =========================================================
# CAMERA
# =========================================================

class VideoStreamer:
    def __init__(self):
        self.cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.ai = AIProcessor()

    def generate_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            frame = self.ai.process_frame(frame)

            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buf.tobytes()
                + b"\r\n"
            )

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

motor = MotorDriver()
line  = BFD1000()
sonar = Ultrasonic()
camera = VideoStreamer()

RUNNING = False
active_mask = [1,1,1,1,1]   # LL L M R RR

# =========================================================
# VIDEO FEED
# =========================================================

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        camera.generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

# =========================================================
# WEBSOCKET /ws/avoid  (HYBRID MODE)
# =========================================================

@app.websocket("/ws/avoid")
async def ws_avoid(ws: WebSocket):
    global RUNNING, active_mask
    await ws.accept()
    logger.info("LINE HYBRID CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)

                if data.get("cmd") == "set_ai_mode":
                    if data.get("mode") == "avoid_hybrid":
                        RUNNING = True
                        cfg = data.get("config", {})
                        active_mask = [
                            1 if cfg.get("ll", True) else 0,
                            1 if cfg.get("l",  True) else 0,
                            1 if cfg.get("m",  True) else 0,
                            1 if cfg.get("r",  True) else 0,
                            1 if cfg.get("rr", True) else 0,
                        ]
                    else:
                        RUNNING = False

            except asyncio.TimeoutError:
                pass

            if RUNNING:
                dist = sonar.read_cm()
                raw_lines = line.read()
                masked_lines = [r & m for r, m in zip(raw_lines, active_mask)]

                camera.ai.update(dist, raw_lines, active_mask)

                # ---------- PRIORITY 1: OBSTACLE ----------
                if dist is not None and dist < BRAKE_DIST:
                    motor.stop()
                    motor.move(0.0, 0.5)
                    await asyncio.sleep(0.4)
                    motor.stop()

                # ---------- PRIORITY 2: LINE ----------
                else:
                    if sum(masked_lines) == 0:
                        motor.stop()

                    elif masked_lines[2]:
                        motor.move(0.22, 0.0)
                    elif masked_lines[1]:
                        motor.move(0.18, -0.3)
                    elif masked_lines[3]:
                        motor.move(0.18, 0.3)
                    elif masked_lines[0]:
                        motor.move(0.14, -0.5)
                    elif masked_lines[4]:
                        motor.move(0.14, 0.5)

            else:
                motor.stop()

            await asyncio.sleep(0.02)

    except WebSocketDisconnect:
        pass
    finally:
        RUNNING = False
        motor.stop()
        logger.info("LINE HYBRID DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
