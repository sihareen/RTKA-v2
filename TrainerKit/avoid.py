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
# CONFIG INLINE
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

# --- ULTRASONIC ---
PIN_HCSR_TRIG = 26
PIN_HCSR_ECHO = 20

# --- AVOID PARAM ---
SAFE_DIST = 30      # cm
BRAKE_DIST = 20     # cm
TURN_TIME = 0.6

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-avoid")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# HARDWARE
# =========================================================

from gpiozero import Motor, DistanceSensor

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
# AI PROCESSOR (DISPLAY + DISTANCE)
# =========================================================

import cv2

class AIProcessor:
    def __init__(self):
        self.mode = "avoid"
        self.distance = None

    def update_distance(self, d):
        self.distance = d

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

        # DISTANCE HUD
        txt = "DIST: ---"
        col = (0,255,0)
        if self.distance is not None:
            txt = f"DIST: {self.distance:.1f} cm"
            if self.distance < BRAKE_DIST:
                col = (0,0,255)

        cv2.rectangle(frame, (5,5), (220,40), (0,0,0), -1)
        cv2.putText(frame, txt, (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

        cv2.putText(frame, "AI MODE: AVOID", (10,70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

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
sonar = Ultrasonic()
camera = VideoStreamer()

RUNNING = False

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
# WEBSOCKET /ws/avoid
# =========================================================

@app.websocket("/ws/avoid")
async def ws_avoid(ws: WebSocket):
    global RUNNING
    await ws.accept()
    logger.info("AVOID CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                if data.get("cmd") == "set_ai_mode":
                    RUNNING = data.get("mode") != "standby"
            except asyncio.TimeoutError:
                pass

            if RUNNING:
                dist = sonar.read_cm()
                camera.ai.update_distance(dist)

                if dist is None or dist > SAFE_DIST:
                    motor.move(0.25, 0.0)

                elif BRAKE_DIST < dist <= SAFE_DIST:
                    motor.move(0.1, 0.0)

                else:
                    motor.stop()
                    motor.move(0.0, 0.5)
                    await asyncio.sleep(TURN_TIME)
                    motor.stop()

            else:
                motor.stop()

            await asyncio.sleep(0.02)

    except WebSocketDisconnect:
        pass
    finally:
        RUNNING = False
        motor.stop()
        logger.info("AVOID DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
