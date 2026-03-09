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
EMBEDDINGS_PATH = os.path.join(MODELS_DIR, "face_embeddings.json")
YUNET_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

CASCADE_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/master/"
    "data/haarcascades/haarcascade_frontalface_default.xml"
)
YUNET_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
    "face_detection_yunet_2023mar.onnx"
)
SFACE_MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/"
    "face_recognition_sface_2021dec.onnx"
)
DEFAULT_FACE_MATCH_THRESHOLD = 0.363


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


def _download_if_missing(path, url, label):
    if os.path.exists(path):
        return path
    print(f"Downloading {label}...")
    urllib.request.urlretrieve(url, path)
    return path


def setup_face_models():
    """Ensure YuNet and SFace ONNX files exist."""
    _download_if_missing(YUNET_MODEL_PATH, YUNET_MODEL_URL, "YuNet model")
    _download_if_missing(SFACE_MODEL_PATH, SFACE_MODEL_URL, "SFace model")


def load_face_detector(cascade_path=CASCADE_PATH):
    """Load OpenCV Haar cascade detector."""
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("Failed to load haarcascade model")
    return detector


def _require_face_modules():
    if not hasattr(cv2, "FaceDetectorYN_create"):
        raise RuntimeError(
            "FaceDetectorYN tidak tersedia. Gunakan OpenCV terbaru "
            "(disarankan opencv-contrib-python)."
        )
    if not hasattr(cv2, "FaceRecognizerSF_create"):
        raise RuntimeError(
            "FaceRecognizerSF tidak tersedia. Gunakan OpenCV terbaru "
            "(disarankan opencv-contrib-python)."
        )


def load_face_analyzers(input_size=(640, 480)):
    """Load YuNet detector and SFace recognizer."""
    _require_face_modules()
    setup_face_models()
    detector = cv2.FaceDetectorYN_create(
        YUNET_MODEL_PATH,
        "",
        input_size,
        score_threshold=0.9,
        nms_threshold=0.3,
        top_k=5000,
    )
    recognizer = cv2.FaceRecognizerSF_create(SFACE_MODEL_PATH, "")
    return detector, recognizer


def open_camera(width=640, height=480):
    """Open USB webcam via OpenCV/V4L2 only."""
    backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
    for backend in backends:
        camera = cv2.VideoCapture(0, backend)
        if not camera.isOpened():
            continue

        camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        # Warm up webcam buffers; avoids stale first frame on some UVC devices.
        ok = False
        for _ in range(8):
            ok, _ = camera.read()
            if ok:
                break
            time.sleep(0.03)
        if ok:
            return camera, "USB Webcam"
        camera.release()

    raise RuntimeError("Webcam tidak tersedia di /dev/video0")


def read_frame(camera, camera_type):
    """Read frame from selected camera backend."""
    _ = camera_type
    ret, frame = camera.read()
    return ret, frame


def close_camera(camera, camera_type):
    """Release camera resource."""
    _ = camera_type
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


def _normalize_feature(feature):
    vec = np.asarray(feature, dtype=np.float32).flatten()
    norm = np.linalg.norm(vec)
    if norm <= 1e-10:
        return None
    return vec / norm


def detect_faces(detector, frame):
    """Detect faces using YuNet."""
    height, width = frame.shape[:2]
    detector.setInputSize((width, height))
    _, faces = detector.detect(frame)
    if faces is None:
        return []
    return faces


def extract_face_feature(frame, face_row, recognizer):
    """Extract normalized SFace embedding from one detected face row."""
    aligned = recognizer.alignCrop(frame, face_row)
    feature = recognizer.feature(aligned)
    return _normalize_feature(feature)


def _largest_face(faces):
    if not faces:
        return None
    return max(faces, key=lambda row: float(row[2] * row[3]))


def train_face_embeddings_model(db_path=DB_PATH):
    """
    Build face embedding index from dataset images.
    Returns (total_people, total_images_used).
    """
    detector, recognizer = load_face_analyzers()
    people = {p["person_code"]: p for p in list_people(db_path=db_path)}
    person_codes = sorted(
        [
            d
            for d in os.listdir(DATASET_DIR)
            if os.path.isdir(os.path.join(DATASET_DIR, d))
        ]
    )

    records = []
    total_images_used = 0
    for person_code in person_codes:
        person = people.get(person_code)
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

        features = []
        for image_file in image_files:
            image_path = os.path.join(person_dir, image_file)
            frame = cv2.imread(image_path)
            if frame is None:
                continue
            faces = detect_faces(detector, frame)
            face_row = _largest_face(faces)
            if face_row is None:
                continue
            feature = extract_face_feature(frame, face_row, recognizer)
            if feature is None:
                continue
            features.append(feature)
            total_images_used += 1

        if not features:
            continue

        mean_feature = _normalize_feature(np.mean(np.vstack(features), axis=0))
        if mean_feature is None:
            continue
        records.append(
            {
                "person_id": person["person_id"],
                "person_code": person["person_code"],
                "person_name": person["person_name"],
                "embedding": mean_feature.tolist(),
                "samples_used": len(features),
            }
        )

    if not records:
        raise RuntimeError("Gagal membuat embedding. Pastikan dataset wajah valid.")

    with open(EMBEDDINGS_PATH, "w", encoding="utf-8") as file:
        json.dump(
            {
                "model": "SFace",
                "metric": "cosine_similarity",
                "threshold": DEFAULT_FACE_MATCH_THRESHOLD,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "people": records,
            },
            file,
            indent=2,
        )
    return len(records), total_images_used


def load_face_embeddings_index():
    """Load embedding index and return dict keyed by person_code."""
    if not os.path.exists(EMBEDDINGS_PATH):
        raise RuntimeError("Model embedding belum ada. Jalankan 01_enroll_face.py dulu.")
    with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    people = {}
    for row in data.get("people", []):
        embedding = _normalize_feature(row.get("embedding"))
        if embedding is None:
            continue
        people[row["person_code"]] = {
            "person_id": row["person_id"],
            "person_code": row["person_code"],
            "person_name": row["person_name"],
            "embedding": embedding,
            "samples_used": row.get("samples_used", 0),
        }

    if not people:
        raise RuntimeError("Embedding index kosong/tidak valid.")
    threshold = float(data.get("threshold", DEFAULT_FACE_MATCH_THRESHOLD))
    return people, threshold


def identify_face(feature, embeddings_index, threshold):
    """Return (person_data_or_none, similarity)."""
    query = _normalize_feature(feature)
    if query is None:
        return None, -1.0

    best_person = None
    best_score = -1.0
    for row in embeddings_index.values():
        score = float(np.dot(query, row["embedding"]))
        if score > best_score:
            best_score = score
            best_person = row

    if best_person is None or best_score < threshold:
        return None, best_score
    return {
        "person_id": best_person["person_id"],
        "person_code": best_person["person_code"],
        "person_name": best_person["person_name"],
    }, best_score


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
