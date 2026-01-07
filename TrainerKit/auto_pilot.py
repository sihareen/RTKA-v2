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

# --- AUTO PILOT PARAM ---
BASE_SPEED = 0.30
STEER_GAIN = 0.8
MIN_CONTOUR_AREA = 1200

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-autopilot")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"

# =========================================================
# MOTOR DRIVER
# =========================================================

from gpiozero import Motor

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
        return sign * (MIN_PWM + v * (1 - MIN_PWM))

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

# =========================================================
# AI PROCESSOR (VISION AUTO PILOT)
# =========================================================

import cv2
import numpy as np

class AIProcessor:
    def __init__(self):
        self.error_x = 0.0
        self.found = False

    def process_frame(self, frame):
        self.error_x = 0.0
        self.found = False

        h, w, _ = frame.shape
        roi = frame[int(h*0.65):h, 0:w]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > MIN_CONTOUR_AREA:
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    self.error_x = (cx - (w / 2)) / (w / 2)
                    self.found = True

                    cv2.line(
                        frame,
                        (int(w/2), int(h*0.85)),
                        (cx, int(h*0.85)),
                        (0,255,255),
                        2
                    )

        # HUD
        cv2.rectangle(frame, (5,5), (320,40), (0,0,0), -1)
        cv2.putText(frame,
            "AI MODE: AUTO PILOT",
            (10,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,0),
            2
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

motor = MotorDriver()
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
# WEBSOCKET /ws/autoPilot
# =========================================================

@app.websocket("/ws/autoPilot")
async def ws_auto(ws: WebSocket):
    global RUNNING
    await ws.accept()
    logger.info("AUTO PILOT CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                if data.get("cmd") == "set_ai_mode":
                    if data.get("mode") == "start":
                        RUNNING = True
                    elif data.get("mode") == "stop":
                        RUNNING = False
                        motor.stop()
            except asyncio.TimeoutError:
                pass

            if RUNNING and camera.ai.found:
                err = camera.ai.error_x
                throttle = BASE_SPEED - abs(err) * 0.15
                steering = err * STEER_GAIN
                motor.move(throttle, steering)
            else:
                motor.stop()

            await asyncio.sleep(0.02)

    except WebSocketDisconnect:
        pass
    finally:
        RUNNING = False
        motor.stop()
        logger.info("AUTO PILOT DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
