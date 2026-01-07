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

# --- MODEL ---
MODEL_PATH = "assets/ssd_mobilenet_v2.tflite"
CONF_THRESHOLD = 0.55

# --- AREA FILTER ---
MIN_AREA_RATIO = 0.02
MAX_AREA_RATIO = 0.80

# --- TARGET OBJECT (WHITELIST) ---
TARGET_OBJECTS = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    44: "bottle",
    46: "cup",
    67: "cell phone"
}

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("trainer-object-detection")

os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# =========================================================
# AI PROCESSOR (SSD OBJECT DETECTION)
# =========================================================

import cv2
import numpy as np

# --- TFLITE IMPORT (PI FRIENDLY) ---
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite


class AIProcessor:
    def __init__(self):
        self.mode = "object_detection"

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        self.interpreter = tflite.Interpreter(model_path=MODEL_PATH)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def process_frame(self, frame):
        h, w, _ = frame.shape

        # --- PREPROCESS ---
        img = cv2.resize(frame, (300, 300))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(img_rgb, axis=0)

        self.interpreter.set_tensor(
            self.input_details[0]['index'],
            input_data
        )
        self.interpreter.invoke()

        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]

        # --- FIND BEST OBJECT ---
        best = None
        best_score = 0

        for i, score in enumerate(scores):
            if score < CONF_THRESHOLD:
                continue

            cls = int(classes[i])
            if cls not in TARGET_OBJECTS:
                continue

            ymin, xmin, ymax, xmax = boxes[i]
            bw = int((xmax - xmin) * w)
            bh = int((ymax - ymin) * h)
            area_ratio = (bw * bh) / (w * h)

            if not (MIN_AREA_RATIO <= area_ratio <= MAX_AREA_RATIO):
                continue

            if score > best_score:
                best_score = score
                best = (i, cls, score)

        # --- DRAW ---
        if best:
            i, cls, score = best
            ymin, xmin, ymax, xmax = boxes[i]

            x1 = int(xmin * w)
            y1 = int(ymin * h)
            x2 = int(xmax * w)
            y2 = int(ymax * h)

            label = TARGET_OBJECTS[cls]
            text = f"{label} {int(score*100)}%"

            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.rectangle(frame, (x1,y1-25), (x1+200,y1), (0,0,0), -1)
            cv2.putText(frame, text, (x1+5,y1-7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # --- HUD ---
        cv2.rectangle(frame, (5,5), (260,40), (0,0,0), -1)
        cv2.putText(frame,
            "AI MODE: OBJECT DETECTION",
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
    logger.info("OBJECT DETECTION CONNECTED")

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        logger.info("OBJECT DETECTION DISCONNECTED")

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
