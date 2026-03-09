#!/usr/bin/env python3
"""
Bab 21.4: One-File Web Face Attendance
======================================
Satu script untuk:
- Live camera stream di browser
- Enroll wajah user
- Realtime attendance (check-in 1x per hari)
- Export CSV

Jalankan:
  python3 04_face_attendance_web.py --host 0.0.0.0 --port 5000

Buka:
  http://<IP_RASPBERRY_PI>:5000
"""

import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import threading
import time
import urllib.request
from datetime import datetime

import cv2
import numpy as np
from flask import Flask, Response, jsonify, render_template_string, request, send_file

import attendance_utils as common

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATASET_DIR = os.path.join(DATA_DIR, "dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

DB_PATH = os.path.join(DATA_DIR, "attendance.db")
MODEL_PATH = os.path.join(MODELS_DIR, "lbph_trainer.yml")
LABELS_PATH = os.path.join(MODELS_DIR, "labels.json")
CASCADE_PATH = os.path.join(MODELS_DIR, "haarcascade_frontalface_default.xml")

CASCADE_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/master/"
    "data/haarcascades/haarcascade_frontalface_default.xml"
)

RECOGNITION_THRESHOLD = common.DEFAULT_FACE_MATCH_THRESHOLD
ENROLL_INTERVAL_SEC = 0.15
ENROLL_ANGLE_DELAY_SEC = 3.0
DEFAULT_ENROLL_SAMPLES = 70
ENROLL_ANGLES = [
    ("front", "Depan"),
    ("left", "Menoleh Kiri"),
    ("right", "Menoleh Kanan"),
    ("up", "Tengadah"),
    ("down", "Menunduk"),
    ("tilt_left", "Miring Kiri"),
    ("tilt_right", "Miring Kanan"),
]
DETECT_ROTATION_ANGLES = [0, -15, 15, -30, 30]
DEFAULT_ADMIN_PIN = "123456"
DEFAULT_ATTENDANCE_CONFIG = {
    "arrival_start": "06:00",
    "arrival_end": "10:00",
    "departure_start": "16:00",
    "departure_end": "21:00",
}


# ---------------------------------------------------------------------------
# Storage and ML utilities
# ---------------------------------------------------------------------------

def normalize_enroll_target(samples_target):
    _ = samples_target  # Kompatibilitas request lama.
    return DEFAULT_ENROLL_SAMPLES


def _clip_box(x, y, w, h, width, height):
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(1, min(w, width - x))
    h = max(1, min(h, height - y))
    return x, y, w, h


def _to_original_box(rot_box, inverse_matrix, width, height):
    x, y, w, h = rot_box
    points = np.array(
        [
            [[x, y]],
            [[x + w, y]],
            [[x + w, y + h]],
            [[x, y + h]],
        ],
        dtype=np.float32,
    )
    points = cv2.transform(points, inverse_matrix)
    x2, y2, w2, h2 = cv2.boundingRect(points)
    return _clip_box(x2, y2, w2, h2, width, height)


def detect_largest_face_with_rotation(detector, gray):
    height, width = gray.shape[:2]
    center = (width / 2.0, height / 2.0)

    for angle in DETECT_ROTATION_ANGLES:
        if angle == 0:
            rotated = gray
            inverse = None
        else:
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(gray, matrix, (width, height))
            inverse = cv2.invertAffineTransform(matrix)

        faces = detector.detectMultiScale(
            rotated,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(80, 80),
        )
        if len(faces) == 0:
            continue

        rx, ry, rw, rh = max(faces, key=lambda box: box[2] * box[3])
        face_roi = rotated[ry : ry + rh, rx : rx + rw]
        if angle == 0:
            box = _clip_box(rx, ry, rw, rh, width, height)
        else:
            box = _to_original_box((rx, ry, rw, rh), inverse, width, height)
        return box, face_roi

    return None, None


def ensure_directories():
    for path in [DATA_DIR, DATASET_DIR, MODELS_DIR, EXPORT_DIR]:
        os.makedirs(path, exist_ok=True)


def hash_pin(pin):
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


def validate_hhmm(value):
    return datetime.strptime(value, "%H:%M").strftime("%H:%M")


def _create_attendance_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            person_code TEXT NOT NULL,
            person_name TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(person_id, event_date, event_type),
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
        """
    )


def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_code TEXT NOT NULL UNIQUE,
            person_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'"
    )
    attendance_exists = cursor.fetchone() is not None

    if not attendance_exists:
        _create_attendance_table(cursor)
    else:
        cursor.execute("PRAGMA table_info(attendance)")
        columns = {row[1] for row in cursor.fetchall()}
        if "event_type" not in columns:
            cursor.execute("ALTER TABLE attendance RENAME TO attendance_old")
            _create_attendance_table(cursor)
            cursor.execute(
                """
                INSERT INTO attendance (
                    person_id, person_code, person_name, event_type,
                    event_date, event_time, confidence, created_at
                )
                SELECT
                    person_id, person_code, person_name, 'arrival',
                    event_date, event_time, confidence, created_at
                FROM attendance_old
                """
            )
            cursor.execute("DROP TABLE attendance_old")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
        ("admin_pin_hash", hash_pin(DEFAULT_ADMIN_PIN)),
    )
    for key, value in DEFAULT_ATTENDANCE_CONFIG.items():
        cursor.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    conn.commit()
    conn.close()


def get_setting(key, default_value=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return default_value
    return row[0]


def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def verify_admin_pin(pin):
    if pin is None:
        return False
    pin = str(pin).strip()
    if not pin:
        return False
    saved = get_setting("admin_pin_hash", hash_pin(DEFAULT_ADMIN_PIN))
    return hash_pin(pin) == saved


def get_attendance_config():
    config = {}
    for key, default_value in DEFAULT_ATTENDANCE_CONFIG.items():
        config[key] = get_setting(key, default_value)
    return config


def save_attendance_config(arrival_start, arrival_end, departure_start, departure_end):
    config = {
        "arrival_start": validate_hhmm(arrival_start),
        "arrival_end": validate_hhmm(arrival_end),
        "departure_start": validate_hhmm(departure_start),
        "departure_end": validate_hhmm(departure_end),
    }
    for key, value in config.items():
        set_setting(key, value)
    return config


def _time_to_minutes(text):
    hh, mm = text.split(":")
    return int(hh) * 60 + int(mm)


def _is_time_in_range(now_minute, start_minute, end_minute):
    if start_minute <= end_minute:
        return start_minute <= now_minute <= end_minute
    return now_minute >= start_minute or now_minute <= end_minute


def get_current_event_type(config):
    now = datetime.now()
    now_minute = now.hour * 60 + now.minute

    a_start = _time_to_minutes(config["arrival_start"])
    a_end = _time_to_minutes(config["arrival_end"])
    d_start = _time_to_minutes(config["departure_start"])
    d_end = _time_to_minutes(config["departure_end"])

    if _is_time_in_range(now_minute, a_start, a_end):
        return "arrival"
    if _is_time_in_range(now_minute, d_start, d_end):
        return "departure"
    return None


def event_type_label(event_type):
    if event_type == "arrival":
        return "Kedatangan"
    if event_type == "departure":
        return "Kepulangan"
    return "Di luar jadwal"


def setup_face_cascade():
    common.setup_face_models()


def load_face_detector():
    detector, _ = common.load_face_analyzers()
    return detector


def _require_opencv_contrib():
    common._require_face_modules()


def load_face_analyzers():
    return common.load_face_analyzers()


def add_or_update_person(person_code, person_name):
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO persons (person_code, person_name, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(person_code) DO UPDATE SET
            person_name = excluded.person_name,
            updated_at = excluded.updated_at
        """,
        (person_code, person_name, now, now),
    )

    cursor.execute(
        "SELECT id, person_code, person_name FROM persons WHERE person_code = ?",
        (person_code,),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return {"person_id": row[0], "person_code": row[1], "person_name": row[2]}


def list_people_map():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, person_code, person_name FROM persons")
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for row in rows:
        result[row["person_code"]] = {
            "person_id": row["id"],
            "person_code": row["person_code"],
            "person_name": row["person_name"],
        }
    return result


def save_face_sample(person_code, face_gray, sample_index):
    person_dir = os.path.join(DATASET_DIR, person_code)
    os.makedirs(person_dir, exist_ok=True)

    normalized = cv2.equalizeHist(face_gray)
    normalized = cv2.resize(normalized, (200, 200))
    filepath = os.path.join(person_dir, f"face_{sample_index:03d}.png")
    cv2.imwrite(filepath, normalized)
    return filepath


def train_lbph_model():
    return common.train_face_embeddings_model(db_path=DB_PATH)


def load_recognizer():
    embeddings, threshold = common.load_face_embeddings_index()
    return embeddings, threshold


def mark_attendance(person_data, confidence, event_type):
    now = datetime.now()
    event_date = now.strftime("%Y-%m-%d")
    event_time = now.strftime("%H:%M:%S")
    created_at = now.isoformat(timespec="seconds")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO attendance (
                person_id, person_code, person_name,
                event_type, event_date, event_time, confidence, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_data["person_id"],
                person_data["person_code"],
                person_data["person_name"],
                event_type,
                event_date,
                event_time,
                float(confidence),
                created_at,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def fetch_today_attendance():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT person_code, person_name, event_type, event_date, event_time, confidence
        FROM attendance
        WHERE event_date = ?
        ORDER BY event_time DESC, event_type ASC
        """,
        (today,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def export_attendance_csv(date_str):
    datetime.strptime(date_str, "%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT person_code, person_name, event_type, event_date, event_time, confidence
        FROM attendance
        WHERE event_date = ?
        ORDER BY event_time ASC, event_type ASC
        """,
        (date_str,),
    )
    rows = cursor.fetchall()
    conn.close()

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(
        ["person_code", "person_name", "event_type", "event_date", "event_time", "confidence"]
    )
    for row in rows:
        writer.writerow(
            [
                row["person_code"],
                row["person_name"],
                row["event_type"],
                row["event_date"],
                row["event_time"],
                f"{row['confidence']:.2f}",
            ]
        )

    return csv_buffer.getvalue().encode("utf-8")


# ---------------------------------------------------------------------------
# Camera backend
# ---------------------------------------------------------------------------

def open_camera(width=640, height=480):
    camera = cv2.VideoCapture(0)
    if camera.isOpened():
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return camera, "USB Webcam"

    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_preview_configuration(main={"size": (width, height)})
        camera.configure(config)
        camera.start()
        time.sleep(2)
        return camera, "PiCamera2"
    except Exception:
        raise RuntimeError("No camera found")


def read_frame(camera, camera_type):
    if camera_type == "PiCamera2":
        frame = camera.capture_array()
        if frame is None:
            return False, None
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 2:
            try:
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
            except Exception:
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)
        return True, frame

    ret, frame = camera.read()
    return ret, frame


def close_camera(camera, camera_type):
    if camera_type == "PiCamera2":
        camera.stop()
    else:
        camera.release()


# ---------------------------------------------------------------------------
# Processing engine
# ---------------------------------------------------------------------------

class FaceAttendanceEngine:
    def __init__(self):
        ensure_directories()
        init_database()
        setup_face_cascade()

        self.detector, self.feature_extractor = load_face_analyzers()
        self.camera, self.camera_type = open_camera()

        self.mode = "idle"  # idle | enroll | attendance | training
        self.message = "System ready"
        self.mode_lock = threading.Lock()

        self.current_frame_jpeg = None
        self.frame_lock = threading.Lock()

        self.stop_event = threading.Event()
        self.thread = None
        self.training_thread = None

        self.enroll_job = None
        self.embeddings_index = {}
        self.match_threshold = RECOGNITION_THRESHOLD
        self.last_mark = {}
        self.attendance_config = get_attendance_config()

        self._load_model_if_exists(initial=True)

    def _load_model_if_exists(self, initial=False):
        try:
            self.embeddings_index, self.match_threshold = load_recognizer()
            if initial:
                self.message = "System ready (model loaded)"
            return True
        except Exception:
            self.embeddings_index = {}
            self.match_threshold = RECOGNITION_THRESHOLD
            if initial:
                self.message = "System ready (no model, please enroll first)"
            return False

    def start(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=3)
        if self.training_thread is not None and self.training_thread.is_alive():
            self.training_thread.join(timeout=3)
        close_camera(self.camera, self.camera_type)

    def set_idle(self):
        with self.mode_lock:
            self.mode = "idle"
            self.enroll_job = None
            self.message = "Idle"

    def start_enroll(self, person_code, person_name, samples_target, admin_pin):
        person_code = person_code.strip().upper()
        person_name = person_name.strip()

        if not person_code or not person_name:
            raise ValueError("person_code dan person_name wajib diisi")
        if not verify_admin_pin(admin_pin):
            raise ValueError("PIN admin salah")
        if self.mode == "training":
            raise ValueError("Model sedang diproses, tunggu hingga selesai")

        total_target = normalize_enroll_target(samples_target)
        samples_per_angle = total_target // len(ENROLL_ANGLES)
        person_data = add_or_update_person(person_code, person_name)
        person_dir = os.path.join(DATASET_DIR, person_code)
        os.makedirs(person_dir, exist_ok=True)
        existing = len(
            [
                f
                for f in os.listdir(person_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
        )

        with self.mode_lock:
            self.enroll_job = {
                "person": person_data,
                "target": total_target,
                "captured": 0,
                "existing": existing,
                "per_angle": samples_per_angle,
                "angle_index": 0,
                "angle_captured": 0,
                "angle_started_ts": time.time(),
                "last_capture_ts": 0.0,
            }
            self.mode = "enroll"
            self.message = (
                f"Enroll started for {person_data['person_name']} ({person_data['person_code']})"
            )

    def save_config(self, arrival_start, arrival_end, departure_start, departure_end, admin_pin):
        if not verify_admin_pin(admin_pin):
            raise ValueError("PIN admin salah")
        config = save_attendance_config(
            arrival_start=arrival_start,
            arrival_end=arrival_end,
            departure_start=departure_start,
            departure_end=departure_end,
        )
        with self.mode_lock:
            self.attendance_config = config
            self.message = "Config jadwal absensi disimpan"
        return config

    def start_attendance(self):
        with self.mode_lock:
            if self.mode == "training":
                raise RuntimeError("Model sedang diproses, tunggu hingga selesai.")
            if not self.embeddings_index:
                if not self._load_model_if_exists():
                    raise RuntimeError("Model belum tersedia. Lakukan enroll terlebih dulu.")
            self.mode = "attendance"
            self.message = "Attendance mode started"

    def get_status(self):
        with self.mode_lock:
            status = {
                "mode": self.mode,
                "message": self.message,
                "camera_type": self.camera_type,
                "model_ready": bool(self.embeddings_index),
                "threshold": self.match_threshold,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "attendance_config": dict(self.attendance_config),
                "enroll": None,
            }

            if self.enroll_job is not None:
                _, angle_label = ENROLL_ANGLES[self.enroll_job["angle_index"]]
                status["enroll"] = {
                    "person_code": self.enroll_job["person"]["person_code"],
                    "person_name": self.enroll_job["person"]["person_name"],
                    "captured": self.enroll_job["captured"],
                    "target": self.enroll_job["target"],
                    "angle_label": angle_label,
                    "angle_index": self.enroll_job["angle_index"] + 1,
                    "angle_total": len(ENROLL_ANGLES),
                    "angle_captured": self.enroll_job["angle_captured"],
                    "per_angle": self.enroll_job["per_angle"],
                }

            return status

    def get_jpeg(self):
        with self.frame_lock:
            return self.current_frame_jpeg

    def _update_jpeg(self, frame):
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            return
        with self.frame_lock:
            self.current_frame_jpeg = encoded.tobytes()

    def _loop(self):
        while not self.stop_event.is_set():
            ret, frame = read_frame(self.camera, self.camera_type)
            if not ret or frame is None:
                with self.mode_lock:
                    self.message = "Camera read failed"
                time.sleep(0.05)
                continue

            with self.mode_lock:
                mode_now = self.mode

            if mode_now == "enroll":
                self._process_enroll(frame)
            elif mode_now == "attendance":
                self._process_attendance(frame)
            elif mode_now == "training":
                self._draw_training_overlay(frame)
            else:
                self._draw_idle_overlay(frame)

            self._update_jpeg(frame)
            time.sleep(0.01)

    def _draw_idle_overlay(self, frame):
        cv2.putText(
            frame,
            "Mode: IDLE",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 220, 40),
            2,
        )
        cv2.putText(
            frame,
            "Use web controls to start enroll/attendance",
            (10, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 220, 220),
            2,
        )

    def _draw_training_overlay(self, frame):
        cv2.putText(
            frame,
            "Mode: TRAINING MODEL",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 180, 255),
            2,
        )
        cv2.putText(
            frame,
            "Please wait, rebuilding embeddings...",
            (10, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 220, 220),
            2,
        )

    def _process_enroll(self, frame):
        faces = common.detect_faces(self.detector, frame)
        face_row = max(faces, key=lambda row: float(row[2] * row[3])) if faces else None

        with self.mode_lock:
            job = self.enroll_job

        if job is None:
            self.set_idle()
            return

        now_ts = time.time()
        _, angle_label = ENROLL_ANGLES[job["angle_index"]]
        wait_remaining = max(0.0, ENROLL_ANGLE_DELAY_SEC - (now_ts - job["angle_started_ts"]))

        if face_row is not None:
            x, y, w, h = [int(v) for v in face_row[:4]]
            x = max(0, x)
            y = max(0, y)
            w = max(1, min(w, frame.shape[1] - x))
            h = max(1, min(h, frame.shape[0] - y))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (20, 220, 20), 2)
            face_roi = frame[y : y + h, x : x + w]

            if (
                face_roi.size > 0
                and wait_remaining <= 0
                and now_ts - job["last_capture_ts"] >= ENROLL_INTERVAL_SEC
            ):
                sample_index = job["existing"] + job["captured"] + 1
                face_gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                save_face_sample(job["person"]["person_code"], face_gray, sample_index)

                with self.mode_lock:
                    if self.enroll_job is not None:
                        self.enroll_job["captured"] += 1
                        self.enroll_job["angle_captured"] += 1
                        self.enroll_job["last_capture_ts"] = now_ts
                        if (
                            self.enroll_job["angle_captured"] >= self.enroll_job["per_angle"]
                            and self.enroll_job["captured"] < self.enroll_job["target"]
                        ):
                            self.enroll_job["angle_index"] += 1
                            self.enroll_job["angle_captured"] = 0
                            self.enroll_job["angle_started_ts"] = now_ts
                            self.enroll_job["last_capture_ts"] = 0.0
                            _, next_angle = ENROLL_ANGLES[self.enroll_job["angle_index"]]
                            self.message = (
                                f"Ganti sudut ke {next_angle}. "
                                f"Capture dimulai {ENROLL_ANGLE_DELAY_SEC:.0f} detik lagi."
                            )
                        job = self.enroll_job

        _, angle_label = ENROLL_ANGLES[job["angle_index"]]
        wait_remaining = max(
            0.0, ENROLL_ANGLE_DELAY_SEC - (time.time() - job["angle_started_ts"])
        )
        progress_text = (
            f"ENROLL {job['person']['person_code']} | "
            f"{job['captured']}/{job['target']}"
        )
        cv2.putText(
            frame,
            progress_text,
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 220, 20),
            2,
        )
        cv2.putText(
            frame,
            f"Sudut: {job['angle_index'] + 1}/{len(ENROLL_ANGLES)} - {angle_label}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 220, 40),
            2,
        )
        if wait_remaining > 0:
            cv2.putText(
                frame,
                f"Capture starts in: {wait_remaining:.1f}s",
                (10, 74),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 180, 255),
                2,
            )

        if job["captured"] >= job["target"]:
            with self.mode_lock:
                if self.mode != "training":
                    self.mode = "training"
                    self.message = "Enroll selesai. Rebuild model embedding..."
            if self.training_thread is None or not self.training_thread.is_alive():
                self.training_thread = threading.Thread(
                    target=self._rebuild_model_async, daemon=True
                )
                self.training_thread.start()

    def _rebuild_model_async(self):
        try:
            total_people, total_images = train_lbph_model()
            self._load_model_if_exists()
            with self.mode_lock:
                self.message = (
                    "Enroll done. "
                    f"Model updated ({total_people} people, {total_images} images)."
                )
        except Exception as exc:
            with self.mode_lock:
                self.message = f"Training failed: {exc}"
        finally:
            with self.mode_lock:
                self.mode = "idle"
                self.enroll_job = None

    def _process_attendance(self, frame):
        if not self.embeddings_index:
            cv2.putText(
                frame,
                "No model. Please enroll first.",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            return

        faces = common.detect_faces(self.detector, frame)

        cv2.putText(
            frame,
            "Mode: ATTENDANCE",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 220, 20),
            2,
        )

        event_type = get_current_event_type(self.attendance_config)
        event_label = event_type_label(event_type)
        schedule_text = (
            f"In: {self.attendance_config['arrival_start']}-{self.attendance_config['arrival_end']} "
            f"| Out: {self.attendance_config['departure_start']}-{self.attendance_config['departure_end']}"
        )
        cv2.putText(
            frame,
            f"Window: {event_label}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 220, 40) if event_type else (0, 180, 255),
            2,
        )
        cv2.putText(
            frame,
            schedule_text,
            (10, 74),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
        )

        for face_row in faces:
            x, y, w, h = [int(v) for v in face_row[:4]]
            x = max(0, x)
            y = max(0, y)
            w = max(1, min(w, frame.shape[1] - x))
            h = max(1, min(h, frame.shape[0] - y))
            feature = common.extract_face_feature(frame, face_row, self.feature_extractor)
            label_data, similarity = common.identify_face(
                feature,
                self.embeddings_index,
                self.match_threshold,
            )
            known = label_data is not None

            if known:
                person_id = label_data["person_id"]
                person_name = label_data["person_name"]
                person_code = label_data["person_code"]
                color = (20, 220, 20)
                text = f"{person_name} ({person_code}) sim:{similarity:.3f} [{event_label}]"

                now_ts = time.time()
                if event_type is None:
                    color = (0, 180, 255)
                    text = f"{person_name} ({person_code}) luar jadwal"
                else:
                    mark_key = f"{person_id}:{event_type}"
                    if now_ts - self.last_mark.get(mark_key, 0) > 3:
                        saved = mark_attendance(label_data, similarity, event_type)
                        with self.mode_lock:
                            if saved:
                                self.message = (
                                    f"{event_type_label(event_type)} tersimpan: "
                                    f"{person_name} ({person_code})"
                                )
                            else:
                                self.message = (
                                    f"{event_type_label(event_type)} sudah tercatat hari ini: "
                                    f"{person_name} ({person_code})"
                                )
                        self.last_mark[mark_key] = now_ts
            else:
                color = (20, 20, 230)
                text = f"Unknown sim:{similarity:.3f}"

            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(
                frame,
                text,
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RTKAv2 Face Attendance</title>
  <style>
    :root {
      --bg: #f1ece2;
      --ink: #2a251e;
      --muted: #6d6354;
      --panel: #fffdfa;
      --line: #dacdb6;
      --line-soft: #ebe1d0;
      --brand: #186f5b;
      --brand-dark: #0f4f41;
      --alert: #ba3d30;
      --accent: #df8b22;
      --soft-blue: #2d6aa4;
      --shadow: 0 14px 40px rgba(36, 26, 10, 0.11);
    }

    * {
      box-sizing: border-box;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }

    body {
      margin: 0;
      font-family: "Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 4% 8%, rgba(223, 139, 34, 0.16), transparent 34%),
        radial-gradient(circle at 96% 12%, rgba(24, 111, 91, 0.17), transparent 28%),
        radial-gradient(circle at 84% 94%, rgba(45, 106, 164, 0.12), transparent 30%),
        var(--bg);
      min-height: 100vh;
    }

    .page {
      width: 100%;
      min-height: 100vh;
    }

    .wrap {
      max-width: 1260px;
      margin: 0 auto;
      padding: 22px;
      display: grid;
      gap: 18px;
      grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr);
      grid-template-areas:
        "header header"
        "video sidebar";
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
    }

    .topbar {
      grid-area: header;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      background:
        linear-gradient(130deg, rgba(24, 111, 91, 0.95), rgba(34, 59, 95, 0.92)),
        var(--panel);
      color: #fffdf8;
      border: none;
    }

    .title-stack h1 {
      margin: 0;
      font-size: 1.45rem;
      letter-spacing: 0.4px;
      font-weight: 800;
    }

    .subtitle {
      margin-top: 4px;
      font-size: 0.92rem;
      opacity: 0.9;
      color: #efe8db;
    }

    .tag {
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.35px;
      background: rgba(255, 255, 255, 0.14);
      border: 1px solid rgba(255, 255, 255, 0.25);
      white-space: nowrap;
    }

    .video-panel {
      grid-area: video;
      padding: 14px;
      display: grid;
      gap: 12px;
      align-content: start;
    }

    .camera-shell {
      border-radius: 14px;
      overflow: hidden;
      border: 2px solid #1a1a1a;
      background: #0f0f0f;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
    }

    .video-box {
      width: 100%;
      aspect-ratio: 16 / 10;
      background: #111;
    }

    .video-box img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }

    .caption {
      padding: 9px 12px;
      border: 1px dashed var(--line);
      border-radius: 10px;
      color: var(--muted);
      font-size: 0.86rem;
      background: #fffaf1;
    }

    .sidebar {
      grid-area: sidebar;
      padding: 14px;
      display: grid;
      gap: 12px;
      align-content: start;
    }

    .status {
      font-size: 0.89rem;
      line-height: 1.45;
      padding: 12px;
      border-radius: 12px;
      background: #fff;
      border: 1px solid var(--line-soft);
      min-height: 116px;
    }

    .block {
      border: 1px solid var(--line-soft);
      border-radius: 14px;
      padding: 11px;
      background: #fffdfa;
      display: grid;
      gap: 9px;
    }

    .section-title {
      margin: 0;
      font-size: 0.96rem;
      letter-spacing: 0.2px;
      color: #3c3327;
      text-transform: uppercase;
      font-weight: 800;
    }

    .pin-note {
      font-size: 0.8rem;
      color: #7a3f00;
      background: #fff1dc;
      border: 1px dashed #e5bc89;
      border-radius: 8px;
      padding: 7px 9px;
    }

    .muted {
      color: var(--muted);
      font-size: 0.82rem;
      margin-top: 2px;
    }

    .controls {
      display: grid;
      gap: 8px;
      grid-template-columns: 1fr 1fr;
    }

    .time-grid {
      display: grid;
      gap: 8px;
      grid-template-columns: 1fr 1fr;
    }

    input, button {
      width: 100%;
      padding: 10px 11px;
      border-radius: 10px;
      border: 1px solid var(--line-soft);
      font-size: 0.9rem;
      font-family: inherit;
      background: #fff;
      color: var(--ink);
    }

    input:focus {
      outline: none;
      border-color: rgba(24, 111, 91, 0.7);
      box-shadow: 0 0 0 3px rgba(24, 111, 91, 0.12);
    }

    button {
      cursor: pointer;
      border: none;
      font-weight: 800;
      letter-spacing: 0.2px;
      transition: transform 0.08s ease, filter 0.18s ease;
    }

    button:active { transform: scale(0.98); }
    button:hover { filter: brightness(0.97); }

    .btn-brand { background: var(--brand); color: #fff; }
    .btn-accent { background: var(--accent); color: #241b12; }
    .btn-stop { background: var(--alert); color: #fff; }
    .btn-soft { background: var(--soft-blue); color: #fff; }

    .table-inline {
      border: 1px solid var(--line-soft);
      border-radius: 14px;
      padding: 10px;
      background: #fffcf6;
    }

    .table-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }

    .table-title {
      margin: 0;
      font-size: 1.02rem;
      letter-spacing: 0.2px;
    }

    .table-wrap {
      border: 1px solid var(--line-soft);
      border-radius: 12px;
      overflow: auto;
      max-height: 360px;
      background: #fff;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 680px;
      font-size: 0.88rem;
    }

    th, td {
      border-bottom: 1px solid #efe4d0;
      padding: 9px 10px;
      text-align: left;
    }

    th {
      background: #faf3e7;
      position: sticky;
      top: 0;
      z-index: 1;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      color: #5a4f40;
    }

    tbody tr:nth-child(even) { background: #fffdf8; }

    .type-pill {
      display: inline-block;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 700;
      border: 1px solid transparent;
    }

    .type-arrival {
      background: rgba(24, 111, 91, 0.12);
      color: #145949;
      border-color: rgba(24, 111, 91, 0.25);
    }

    .type-departure {
      background: rgba(45, 106, 164, 0.11);
      color: #1f568a;
      border-color: rgba(45, 106, 164, 0.24);
    }

    @media (max-width: 980px) {
      .wrap {
        grid-template-columns: 1fr;
        grid-template-areas:
          "header"
          "video"
          "sidebar";
        padding: 14px;
      }

      .topbar {
        flex-direction: column;
        align-items: flex-start;
      }

      .controls,
      .time-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="page">
    <div class="wrap">
      <header class="panel topbar">
        <div class="title-stack">
          <h1>RTKAv2 Face Attendance</h1>
          <div class="subtitle">Compact web control panel for camera, enroll, schedule, and export</div>
        </div>
        <div class="tag">ADMIN PIN MODE ENABLED</div>
      </header>

      <section class="panel video-panel">
        <div class="camera-shell">
          <div class="video-box">
            <img src="/video_feed" alt="Live Camera">
          </div>
        </div>
        <div class="caption">Live stream from Raspberry Pi camera. Attendance runs continuously when mode is active.</div>

        <div class="table-inline">
          <div class="table-head">
            <h2 class="table-title">Today Attendance</h2>
            <div class="muted">Auto refresh every 4 seconds</div>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody id="tbody"></tbody>
            </table>
          </div>
        </div>
      </section>

      <aside class="panel sidebar">
        <div class="status" id="statusBox">Loading status...</div>

        <div class="block">
          <h3 class="section-title">Mode Attendance</h3>
          <div class="controls">
            <button class="btn-brand" onclick="startAttendance()">Start Attendance</button>
            <button class="btn-stop" onclick="stopMode()">Stop</button>
          </div>
        </div>

        <div class="block">
          <h3 class="section-title">Enroll (Admin)</h3>
          <div class="pin-note">Save Enroll akan meminta PIN admin.</div>
          <div class="muted">Fixed 70 foto: 7 sudut (Depan, Menoleh Kiri, Menoleh Kanan, Tengadah, Menunduk, Miring Kiri, Miring Kanan), delay 3 detik per sudut.</div>
          <input id="code" placeholder="Person Code (EMP001)">
          <input id="name" placeholder="Person Name">
          <button class="btn-accent" onclick="startEnroll()">Save Enroll</button>
        </div>

        <div class="block">
          <h3 class="section-title">Export</h3>
          <input id="exportDate" type="date">
          <button class="btn-soft" onclick="exportCsv()">Export CSV</button>
        </div>

        <div class="block">
          <h3 class="section-title">Config Jam Absensi (Admin)</h3>
          <div class="pin-note">Save Config akan meminta PIN admin.</div>
          <div class="time-grid">
            <div>
              <label class="muted" for="arrivalStart">Kedatangan Start</label>
              <input id="arrivalStart" type="time">
            </div>
            <div>
              <label class="muted" for="arrivalEnd">Kedatangan End</label>
              <input id="arrivalEnd" type="time">
            </div>
            <div>
              <label class="muted" for="departureStart">Kepulangan Start</label>
              <input id="departureStart" type="time">
            </div>
            <div>
              <label class="muted" for="departureEnd">Kepulangan End</label>
              <input id="departureEnd" type="time">
            </div>
          </div>
          <button class="btn-soft" onclick="saveConfig()">Save Config</button>
        </div>
      </aside>

    </div>
  </div>

  <script>
    function todayStr() {
      const d = new Date();
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }

    async function apiPost(url, payload = {}) {
      const r = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      return r.json();
    }

    async function startAttendance() {
      const res = await apiPost('/api/start_attendance');
      alert(res.message || JSON.stringify(res));
      refreshStatus();
      refreshToday();
    }

    async function stopMode() {
      const res = await apiPost('/api/stop');
      alert(res.message || JSON.stringify(res));
      refreshStatus();
    }

    async function startEnroll() {
      const pin = prompt('Masukkan PIN admin untuk enroll:');
      if (!pin) return;
      const payload = {
        person_code: document.getElementById('code').value,
        person_name: document.getElementById('name').value,
        samples: 70,
        admin_pin: pin
      };
      const res = await apiPost('/api/start_enroll', payload);
      alert(res.message || JSON.stringify(res));
      refreshStatus();
    }

    function exportCsv() {
      const date = document.getElementById('exportDate').value || todayStr();
      window.location.href = `/api/export?date=${encodeURIComponent(date)}`;
    }

    async function loadConfig() {
      try {
        const r = await fetch('/api/config');
        const data = await r.json();
        const c = data.config || {};
        document.getElementById('arrivalStart').value = c.arrival_start || '06:00';
        document.getElementById('arrivalEnd').value = c.arrival_end || '10:00';
        document.getElementById('departureStart').value = c.departure_start || '16:00';
        document.getElementById('departureEnd').value = c.departure_end || '21:00';
      } catch (e) {
        console.log('config load fail', e);
      }
    }

    async function saveConfig() {
      const pin = prompt('Masukkan PIN admin untuk save config:');
      if (!pin) return;
      const payload = {
        arrival_start: document.getElementById('arrivalStart').value,
        arrival_end: document.getElementById('arrivalEnd').value,
        departure_start: document.getElementById('departureStart').value,
        departure_end: document.getElementById('departureEnd').value,
        admin_pin: pin
      };
      const res = await apiPost('/api/config', payload);
      alert(res.message || JSON.stringify(res));
      refreshStatus();
      loadConfig();
    }

    function prettyType(eventType) {
      if (eventType === 'arrival') return 'Kedatangan';
      if (eventType === 'departure') return 'Kepulangan';
      return eventType || '-';
    }

    function typeClass(eventType) {
      if (eventType === 'arrival') return 'type-pill type-arrival';
      if (eventType === 'departure') return 'type-pill type-departure';
      return 'type-pill';
    }

    async function refreshStatus() {
      try {
        const r = await fetch('/api/status');
        const s = await r.json();
        const e = s.enroll;
        let enrollTxt = '-';
        if (e) {
          enrollTxt =
            `${e.person_code} ${e.person_name} (${e.captured}/${e.target}) | ` +
            `Sudut ${e.angle_index}/${e.angle_total} ${e.angle_label} (${e.angle_captured}/${e.per_angle})`;
        }
        const c = s.attendance_config || {};
        document.getElementById('statusBox').innerHTML =
          `<b>Mode:</b> ${s.mode}<br>` +
          `<b>Message:</b> ${s.message}<br>` +
          `<b>Camera:</b> ${s.camera_type}<br>` +
          `<b>Model ready:</b> ${s.model_ready}<br>` +
          `<b>Arrival:</b> ${c.arrival_start || '-'} - ${c.arrival_end || '-'}<br>` +
          `<b>Departure:</b> ${c.departure_start || '-'} - ${c.departure_end || '-'}<br>` +
          `<b>Enroll:</b> ${enrollTxt}<br>` +
          `<b>Time:</b> ${s.timestamp}`;
      } catch (e) {
        document.getElementById('statusBox').innerText = 'Failed to load status';
      }
    }

    async function refreshToday() {
      const body = document.getElementById('tbody');
      body.innerHTML = '';
      try {
        const r = await fetch('/api/today');
        const data = await r.json();
        for (const row of data.rows) {
          const tr = document.createElement('tr');
          tr.innerHTML =
            `<td>${row.person_code}</td>` +
            `<td>${row.person_name}</td>` +
            `<td><span class="${typeClass(row.event_type)}">${prettyType(row.event_type)}</span></td>` +
            `<td>${row.event_date}</td>` +
            `<td>${row.event_time}</td>` +
            `<td>${Number(row.confidence).toFixed(2)}</td>`;
          body.appendChild(tr);
        }
      } catch (e) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="6">Failed to load data</td>';
        body.appendChild(tr);
      }
    }

    document.getElementById('exportDate').value = todayStr();
    loadConfig();
    refreshStatus();
    refreshToday();
    setInterval(refreshStatus, 1200);
    setInterval(refreshToday, 4000);
  </script>
</body>
</html>
"""


def make_app(engine):
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route("/video_feed")
    def video_feed():
        def generate():
            while True:
                frame = engine.get_jpeg()
                if frame is None:
                    time.sleep(0.05)
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
                time.sleep(0.03)

        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/api/status")
    def api_status():
        return jsonify(engine.get_status())

    @app.route("/api/today")
    def api_today():
        rows = fetch_today_attendance()
        return jsonify({"rows": rows})

    @app.route("/api/start_enroll", methods=["POST"])
    def api_start_enroll():
        payload = request.get_json(silent=True) or {}
        person_code = (payload.get("person_code") or "").strip()
        person_name = (payload.get("person_name") or "").strip()
        samples = payload.get("samples") or DEFAULT_ENROLL_SAMPLES
        admin_pin = payload.get("admin_pin")

        try:
            engine.start_enroll(person_code, person_name, int(samples), admin_pin)
            return jsonify({"ok": True, "message": "Enroll started"})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.route("/api/start_attendance", methods=["POST"])
    def api_start_attendance():
        try:
            engine.start_attendance()
            return jsonify({"ok": True, "message": "Attendance mode started"})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.route("/api/stop", methods=["POST"])
    def api_stop():
        engine.set_idle()
        return jsonify({"ok": True, "message": "Mode set to idle"})

    @app.route("/api/config", methods=["GET", "POST"])
    def api_config():
        if request.method == "GET":
            return jsonify({"ok": True, "config": engine.attendance_config})

        payload = request.get_json(silent=True) or {}
        arrival_start = payload.get("arrival_start")
        arrival_end = payload.get("arrival_end")
        departure_start = payload.get("departure_start")
        departure_end = payload.get("departure_end")
        admin_pin = payload.get("admin_pin")

        try:
            config = engine.save_config(
                arrival_start=arrival_start,
                arrival_end=arrival_end,
                departure_start=departure_start,
                departure_end=departure_end,
                admin_pin=admin_pin,
            )
            return jsonify({"ok": True, "message": "Config saved", "config": config})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.route("/api/export")
    def api_export():
        date_str = request.args.get("date") or datetime.now().strftime("%Y-%m-%d")
        try:
            csv_bytes = export_attendance_csv(date_str)
            filename = f"attendance_{date_str}.csv"
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype="text/csv",
                as_attachment=True,
                download_name=filename,
            )
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

    @app.route("/api/health")
    def api_health():
        return jsonify({"ok": True, "message": "running"})

    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="One-file web face attendance")
    parser.add_argument("--host", default="0.0.0.0", help="Flask host")
    parser.add_argument("--port", type=int, default=5000, help="Flask port")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (not for production)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 70)
    print("RTKAv2 Face Attendance Web (One Script)")
    print("=" * 70)

    engine = FaceAttendanceEngine()
    engine.start()

    app = make_app(engine)

    print(f"Server URL: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
