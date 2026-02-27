#!/usr/bin/env python3
"""
Utilities untuk project face attendance.
"""

import json
import os
import sqlite3
import time
import urllib.request
from datetime import datetime

import cv2
import numpy as np

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


def ensure_directories():
    """Create required folders."""
    for path in [DATA_DIR, DATASET_DIR, MODELS_DIR, EXPORT_DIR]:
        os.makedirs(path, exist_ok=True)


def init_database(db_path=DB_PATH):
    """Initialize SQLite schema."""
    conn = sqlite3.connect(db_path)
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
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            person_code TEXT NOT NULL,
            person_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(person_id, event_date),
            FOREIGN KEY(person_id) REFERENCES persons(id)
        )
        """
    )

    conn.commit()
    conn.close()


def setup_face_cascade(cascade_path=CASCADE_PATH):
    """Ensure Haar cascade file exists."""
    if os.path.exists(cascade_path):
        return cascade_path

    print("Downloading Haar Cascade model...")
    urllib.request.urlretrieve(CASCADE_URL, cascade_path)
    return cascade_path


def load_face_detector(cascade_path=CASCADE_PATH):
    """Load OpenCV Haar cascade detector."""
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("Failed to load haarcascade model")
    return detector


def open_camera(width=640, height=480):
    """Open Pi Camera (if available) or USB camera."""
    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_preview_configuration(main={"size": (width, height)})
        camera.configure(config)
        camera.start()
        time.sleep(2)
        return camera, "PiCamera2"
    except Exception:
        pass

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        raise RuntimeError("No camera found")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return camera, "USB Webcam"


def read_frame(camera, camera_type):
    """Read frame from selected camera backend."""
    if camera_type == "PiCamera2":
        frame = camera.capture_array()
        if frame is None:
            return False, None
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        elif len(frame.shape) == 3 and frame.shape[2] == 2:
            # Some PiCamera2 pipelines return YUYV/UYVY frames.
            try:
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUY2)
            except Exception:
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_UYVY)
        return True, frame

    ret, frame = camera.read()
    return ret, frame


def close_camera(camera, camera_type):
    """Release camera resource."""
    if camera_type == "PiCamera2":
        camera.stop()
    else:
        camera.release()


def add_or_update_person(person_code, person_name, db_path=DB_PATH):
    """Insert or update person data."""
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(db_path)
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

    return {
        "person_id": row[0],
        "person_code": row[1],
        "person_name": row[2],
    }


def list_people(db_path=DB_PATH):
    """List all registered people."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id AS person_id, person_code, person_name
        FROM persons
        ORDER BY person_name ASC
        """
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def save_face_sample(person_code, face_gray, sample_index):
    """Save one face crop image to dataset folder."""
    person_dir = os.path.join(DATASET_DIR, person_code)
    os.makedirs(person_dir, exist_ok=True)

    normalized = cv2.equalizeHist(face_gray)
    normalized = cv2.resize(normalized, (200, 200))
    filename = f"face_{sample_index:03d}.png"
    filepath = os.path.join(person_dir, filename)
    cv2.imwrite(filepath, normalized)
    return filepath


def _require_opencv_contrib():
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise RuntimeError(
            "cv2.face (opencv-contrib-python) tidak tersedia. "
            "Install: pip3 install opencv-contrib-python"
        )


def train_lbph_model(db_path=DB_PATH):
    """Train LBPH model using all dataset images."""
    _require_opencv_contrib()

    faces = []
    labels = []
    labels_map = {}
    label_index = 0

    persons = {p["person_code"]: p for p in list_people(db_path=db_path)}
    person_codes = sorted(
        [
            d
            for d in os.listdir(DATASET_DIR)
            if os.path.isdir(os.path.join(DATASET_DIR, d))
        ]
    )

    for person_code in person_codes:
        person = persons.get(person_code)
        if person is None:
            continue

        person_dir = os.path.join(DATASET_DIR, person_code)
        image_files = sorted(
            [
                f
                for f in os.listdir(person_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
        )
        if not image_files:
            continue

        labels_map[str(label_index)] = person
        for image_file in image_files:
            image_path = os.path.join(person_dir, image_file)
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            image = cv2.resize(image, (200, 200))
            faces.append(image)
            labels.append(label_index)

        label_index += 1

    if len(faces) < 2:
        raise RuntimeError("Data training kurang. Minimal 2 sample wajah.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels))
    recognizer.save(MODEL_PATH)

    with open(LABELS_PATH, "w", encoding="utf-8") as file:
        json.dump(labels_map, file, indent=2)

    return len(labels_map), len(faces)


def load_recognizer():
    """Load trained LBPH model and labels mapping."""
    _require_opencv_contrib()

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError("Model belum ada. Jalankan 01_enroll_face.py terlebih dulu.")
    if not os.path.exists(LABELS_PATH):
        raise RuntimeError("labels.json belum ada. Jalankan 01_enroll_face.py terlebih dulu.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    with open(LABELS_PATH, "r", encoding="utf-8") as file:
        labels_map = json.load(file)

    return recognizer, labels_map


def mark_attendance(person_data, confidence, db_path=DB_PATH):
    """Insert attendance once per person per date."""
    now = datetime.now()
    event_date = now.strftime("%Y-%m-%d")
    event_time = now.strftime("%H:%M:%S")
    created_at = now.isoformat(timespec="seconds")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO attendance (
                person_id, person_code, person_name,
                event_date, event_time, confidence, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_data["person_id"],
                person_data["person_code"],
                person_data["person_name"],
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
