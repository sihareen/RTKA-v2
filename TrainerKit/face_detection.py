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

# --- FACE FILTER ---
MIN_FACE_RATIO = 0.02   # terlalu kecil = noise
MAX_FACE_RATIO = 0.60   # terlalu besar = bukan wajah normal
CONF_THRESHOLD = 0.75

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-face-detection")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# AI PROCESSOR (FACE DETECTION)
# =========================================================

import cv2
import mediapipe as mp

class AIProcessor:
    def __init__(self):
        self.mode = "face_detection"
        self.face = mp.solutions.face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=CONF_THRESHOLD
        )

    def process_frame(self, frame):
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = self.face.process(rgb)

        best = None
        best_area = 0

        if res.detections:
            for det in res.detections:
                box = det.location_data.relative_bounding_box
                x = int(box.xmin * w)
                y = int(box.ymin * h)
                bw = int(box.width * w)
                bh = int(box.height * h)

                area_ratio = (bw * bh) / (w * h)
                if not (MIN_FACE_RATIO <= area_ratio <= MAX_FACE_RATIO):
                    continue

                if area_ratio > best_area:
                    best_area = area_ratio
                    best = (x, y, bw, bh)

        if best:
            x, y, bw, bh = best
            cv2.rectangle(frame, (x,y), (x+bw,y+bh), (0,255,255), 2)

        # --- SAFEZONE (visual only) ---
        zx = int(w * 0.15)
        zy = int(h * 0.15)
        cv2.rectangle(frame,
                      (cx-zx, cy-zy),
                      (cx+zx, cy+zy),
                      (255,255,0), 1)

        # --- CROSSHAIR ---
        cv2.line(frame, (cx-10,cy),(cx+10,cy),(0,0,255),1)
        cv2.line(frame, (cx,cy-10),(cx,cy+10),(0,0,255),1)

        # --- HUD ---
        cv2.rectangle(frame, (5,5), (280,40), (0,0,0), -1)
        cv2.putText(frame,
            "AI MODE: FACE DETECTION",
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
    logger.info("FACE DETECTION CONNECTED")

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("FACE DETECTION DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
