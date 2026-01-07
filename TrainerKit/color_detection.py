#!/usr/bin/env python3
import os
import sys
import json
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

# --- COLOR FILTER ---
MIN_COLOR_RATIO = 0.01     # noise kecil dibuang
MAX_COLOR_RATIO = 0.50     # area aneh dibuang

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-color-detection")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# AI PROCESSOR (COLOR DETECTION)
# =========================================================

import cv2
import numpy as np

class AIProcessor:
    def __init__(self):
        self.mode = "color_detection"

        # HSV ranges (tuned)
        self.COLOR_RANGES = {
            "red": [
                (np.array([0,120,80]), np.array([10,255,255])),
                (np.array([170,120,80]), np.array([180,255,255]))
            ],
            "green": [
                (np.array([40,80,80]), np.array([80,255,255]))
            ],
            "blue": [
                (np.array([100,120,80]), np.array([130,255,255]))
            ],
            "yellow": [
                (np.array([20,120,100]), np.array([35,255,255]))
            ]
        }

    def process_frame(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        detections = []

        for label, ranges in self.COLOR_RANGES.items():
            mask = None
            for lo, hi in ranges:
                m = cv2.inRange(hsv, lo, hi)
                mask = m if mask is None else cv2.bitwise_or(mask, m)

            # Morphology
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
                area_ratio = (bw * bh) / (w * h)

                if MIN_COLOR_RATIO <= area_ratio <= MAX_COLOR_RATIO:
                    detections.append((label, x, y, bw, bh, area_ratio))

        # DRAW DETECTIONS
        for label, x, y, bw, bh, area_ratio in detections:
            cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,255,255), 2)
            cv2.rectangle(frame, (x,y-22), (x+bw,y), (0,0,0), -1)
            cv2.putText(frame,
                        f"{label.upper()} {area_ratio:.2f}",
                        (x+5,y-5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0,255,255),
                        2)

        # SAFEZONE (visual only)
        zx = int(w * 0.15)
        zy = int(h * 0.15)
        cv2.rectangle(frame,
                      (cx-zx, cy-zy),
                      (cx+zx, cy+zy),
                      (255,255,0), 1)

        # CROSSHAIR
        cv2.line(frame, (cx-10,cy),(cx+10,cy),(0,0,255),1)
        cv2.line(frame, (cx,cy-10),(cx,cy+10),(0,0,255),1)

        # HUD
        cv2.rectangle(frame, (5,5), (300,40), (0,0,0), -1)
        cv2.putText(frame,
            "AI MODE: COLOR DETECTION",
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
    logger.info("COLOR DETECTION CONNECTED")

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("COLOR DETECTION DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
