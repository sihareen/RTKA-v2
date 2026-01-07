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

# --- GESTURE FILTER ---
MIN_HAND_RATIO = 0.02     # tangan terlalu kecil = noise
CONFIRM_FRAMES = 3        # harus sama berturut-turut
GESTURE_TIMEOUT = 0.6     # detik tanpa gesture → STOP

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-gesture")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

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
# AI PROCESSOR (GESTURE – STABLE)
# =========================================================

import cv2
import mediapipe as mp

class AIProcessor:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        self.draw = mp.solutions.drawing_utils

        self.gesture = None
        self.confirm_count = 0
        self.last_seen = time.time()

    def process_frame(self, frame):
        self.gesture = None
        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)

        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            self.draw.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)

            xs = [p.x for p in lm.landmark]
            ys = [p.y for p in lm.landmark]

            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)

            area_ratio = (maxx - minx) * (maxy - miny)
            if area_ratio < MIN_HAND_RATIO:
                self.confirm_count = 0
                return frame

            fingers = []

            # Jempol (handedness disederhanakan, trainer mode)
            fingers.append(1 if lm.landmark[4].x < lm.landmark[3].x else 0)

            # 4 jari lain
            for tip, pip in [(8,6),(12,10),(16,14),(20,18)]:
                fingers.append(1 if lm.landmark[tip].y < lm.landmark[pip].y else 0)

            count = fingers.count(1)

            self.confirm_count += 1
            if self.confirm_count >= CONFIRM_FRAMES:
                self.gesture = count
                self.last_seen = time.time()
        else:
            self.confirm_count = 0

        # HUD
        cv2.rectangle(frame, (5,5), (280,80), (0,0,0), -1)
        txt = "GESTURE: ---"
        if self.gesture is not None:
            txt = f"GESTURE: {self.gesture}"
        cv2.putText(frame, txt, (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

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
    logger.info("GESTURE COMMAND CONNECTED")

    try:
        while True:
            try:
                msg = await asyncio.wait_for(ws.receive_text(), timeout=0.05)
                data = json.loads(msg)
                if data.get("cmd") == "set_ai_mode":
                    RUNNING = (data.get("mode") == "gesture_cmd")
            except asyncio.TimeoutError:
                pass

            if RUNNING:
                g = camera.ai.gesture
                now = time.time()

                # TIMEOUT SAFETY
                if g is None and (now - camera.ai.last_seen) > GESTURE_TIMEOUT:
                    motor.stop()
                    await asyncio.sleep(0.05)
                    continue

                if g == 1:
                    motor.move(0.3, 0.0)
                elif g == 2:
                    motor.move(-0.3, 0.0)
                elif g == 3:
                    motor.move(0.0, -0.4)
                elif g == 4:
                    motor.move(0.0, 0.4)
                elif g >= 5:
                    motor.stop()
                else:
                    motor.stop()
            else:
                motor.stop()

            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        pass
    finally:
        RUNNING = False
        motor.stop()
        logger.info("GESTURE COMMAND DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
