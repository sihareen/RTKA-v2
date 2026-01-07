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

# --- GESTURE FILTER ---
MIN_HAND_RATIO = 0.02      # tangan terlalu kecil = noise
CONFIRM_FRAMES = 4         # harus stabil N frame

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-gesture-count")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# AI PROCESSOR (GESTURE COUNTING)
# =========================================================

import cv2
import mediapipe as mp

class AIProcessor:
    def __init__(self):
        self.mode = "gesture_count"

        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6
        )
        self.draw = mp.solutions.drawing_utils

        self.raw_count = None
        self.stable_count = None
        self.confirm = 0

    def process_frame(self, frame):
        self.raw_count = None

        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

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
                self.confirm = 0
            else:
                fingers = []

                # Thumb (simplified – trainer mode)
                fingers.append(1 if lm.landmark[4].x < lm.landmark[3].x else 0)

                # Other fingers (TIP vs PIP)
                for tip, pip in [(8,6), (12,10), (16,14), (20,18)]:
                    fingers.append(1 if lm.landmark[tip].y < lm.landmark[pip].y else 0)

                self.raw_count = fingers.count(1)

                if self.raw_count == self.stable_count:
                    self.confirm += 1
                else:
                    self.confirm = 1

                if self.confirm >= CONFIRM_FRAMES:
                    self.stable_count = self.raw_count

        else:
            self.confirm = 0

        # --- VISUAL ---
        cv2.rectangle(frame, (5,5), (300,100), (0,0,0), -1)

        cv2.putText(frame,
            "AI MODE: GESTURE COUNT",
            (10,30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,0),
            2
        )

        if self.stable_count is not None:
            cv2.putText(frame,
                f"FINGERS: {self.stable_count}",
                (10,70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0,255,255),
                3
            )
        else:
            cv2.putText(frame,
                "FINGERS: ---",
                (10,70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (100,100,100),
                2
            )

        # Crosshair (trainer consistency)
        cv2.line(frame, (cx-10,cy),(cx+10,cy),(0,0,255),1)
        cv2.line(frame, (cx,cy-10),(cx,cy+10),(0,0,255),1)

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

            ok, buf = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            )
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

camera = VideoStreamer()

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
# WEBSOCKET /ws/objectDetection
# =========================================================

@app.websocket("/ws/objectDetection")
async def ws_object(ws: WebSocket):
    await ws.accept()
    logger.info("GESTURE COUNT CONNECTED")

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("GESTURE COUNT DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
