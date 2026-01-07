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

# --- SERVO ---
PIN_SERVO_PAN  = 12
PIN_SERVO_TILT = 13

SERVO_MIN = -90
SERVO_MAX = 90

# --- CONTROL PARAM ---
SAFEZONE_X = 0.15
FOV_PAN = 15.0
MIN_STEP = 2.0

TARGET_AREA = 0.12     # target ideal
AREA_TOL = 0.03        # toleransi

# --- COLOR FILTER ---
MIN_COLOR_RATIO = 0.01
MAX_COLOR_RATIO = 0.5
CONFIRM_FRAMES  = 3

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-color-follow")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# MOTOR DRIVER
# =========================================================

from gpiozero import Motor
from rpi_hardware_pwm import HardwarePWM

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

# =========================================================
# SERVO DRIVER
# =========================================================

class ServoDriver:
    def __init__(self):
        self.pan = HardwarePWM(0, hz=50)
        self.pan.start(0)
        self.pan_pos = 0.0

    def _angle_to_duty(self, angle):
        angle = max(SERVO_MIN, min(SERVO_MAX, angle))
        return 7.5 + (angle / 90.0) * 5.0

    def move_pan(self, delta):
        self.pan_pos += delta
        self.pan_pos = max(SERVO_MIN, min(SERVO_MAX, self.pan_pos))
        self.pan.change_duty_cycle(self._angle_to_duty(self.pan_pos))
        time.sleep(0.12)
        self.pan.change_duty_cycle(0)

    def reset(self):
        self.pan_pos = 0
        self.pan.change_duty_cycle(self._angle_to_duty(0))
        time.sleep(0.3)
        self.pan.change_duty_cycle(0)

# =========================================================
# AI PROCESSOR (COLOR FOLLOW)
# =========================================================

import cv2
import numpy as np

class AIProcessor:
    def __init__(self):
        self.target_color = "red"
        self.error_x = 0.0
        self.area_ratio = 0.0
        self.found = False
        self.confirm = 0

        self.COLOR_RANGES = {
            "red": [
                (np.array([0,120,80]), np.array([10,255,255])),
                (np.array([170,120,80]), np.array([180,255,255]))
            ],
            "green": [(np.array([40,80,80]), np.array([80,255,255]))],
            "blue":  [(np.array([100,120,80]), np.array([130,255,255]))],
            "yellow":[(np.array([20,120,100]), np.array([35,255,255]))]
        }

    def set_color(self, color):
        if color in self.COLOR_RANGES:
            self.target_color = color
            self.confirm = 0

    def process_frame(self, frame):
        self.error_x = 0.0
        self.area_ratio = 0.0
        self.found = False

        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = None
        for lo, hi in self.COLOR_RANGES[self.target_color]:
            m = cv2.inRange(hsv, lo, hi)
            mask = m if mask is None else cv2.bitwise_or(mask, m)

        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_area = 0
        for c in contours:
            a = cv2.contourArea(c)
            if a > best_area:
                best_area = a
                best = c

        if best is not None:
            x,y,bw,bh = cv2.boundingRect(best)
            self.area_ratio = (bw * bh) / (w * h)

            if MIN_COLOR_RATIO <= self.area_ratio <= MAX_COLOR_RATIO:
                self.confirm += 1
            else:
                self.confirm = 0

            if self.confirm >= CONFIRM_FRAMES:
                fx = x + bw // 2
                self.error_x = (fx - cx) / cx
                self.found = True
                cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,255,255), 2)
        else:
            self.confirm = 0

        # SAFEZONE
        zx = int(w * SAFEZONE_X)
        cv2.rectangle(frame, (cx-zx, cy-zx), (cx+zx, cy+zx), (255,255,0), 1)

        # HUD
        cv2.rectangle(frame, (5,5), (340,90), (0,0,0), -1)
        cv2.putText(frame,
            f"COLOR FOLLOW: {self.target_color.upper()}",
            (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,255,0), 2)
        cv2.putText(frame,
            f"ERR X:{self.error_x:+.2f} AREA:{self.area_ratio:.2f}",
            (10,65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

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
servo = ServoDriver()
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
# WEBSOCKET /ws/recognitionControl
# =========================================================

@app.websocket("/ws/recognitionControl")
async def ws_recognition(ws: WebSocket):
    global RUNNING
    await ws.accept()
    logger.info("COLOR FOLLOW CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                if data.get("cmd") == "set_ai_mode":
                    if data.get("mode") == "color_follow":
                        RUNNING = True
                        camera.ai.set_color(data.get("color", "red"))
                    else:
                        RUNNING = False
                        motor.stop()
                        servo.reset()
            except asyncio.TimeoutError:
                pass

            if RUNNING and camera.ai.found:
                ex = camera.ai.error_x
                ar = camera.ai.area_ratio

                # SERVO PAN
                if abs(ex) > SAFEZONE_X:
                    dp = -ex * FOV_PAN
                    if abs(dp) >= MIN_STEP:
                        await asyncio.to_thread(servo.move_pan, dp)

                # MOTOR CONTROL
                throttle = 0.0
                if ar < (TARGET_AREA - AREA_TOL):
                    throttle = 0.25
                elif ar > (TARGET_AREA + AREA_TOL):
                    throttle = -0.20

                steering = ex * 0.6
                motor.move(throttle, steering)

            else:
                motor.stop()

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass
    finally:
        RUNNING = False
        motor.stop()
        servo.reset()
        logger.info("COLOR FOLLOW DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
