#!/usr/bin/env python3
"""
Bab 21.1: Enroll Wajah untuk Absensi
====================================
Mendaftarkan wajah user dan melatih model LBPH.
"""

import argparse
import os
import time

import cv2
import numpy as np

import attendance_utils as utils

ENROLL_ANGLE_DELAY_SEC = 3.0
DEFAULT_TOTAL_SAMPLES = 70
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


def parse_args():
    parser = argparse.ArgumentParser(description="Enroll wajah untuk attendance")
    parser.add_argument("--code", type=str, help="Kode user, contoh: EMP001")
    parser.add_argument("--name", type=str, help="Nama user")
    parser.add_argument(
        "--samples",
        type=int,
        default=70,
        help="Kompatibilitas lama (diabaikan, enroll selalu 70 foto)",
    )
    return parser.parse_args()


def read_input(prompt):
    value = input(prompt).strip()
    if not value:
        raise ValueError("Input tidak boleh kosong")
    return value


def normalize_target_samples(samples_target):
    _ = samples_target  # Kompatibilitas argumen lama.
    return DEFAULT_TOTAL_SAMPLES


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


def main():
    args = parse_args()

    print("=" * 60)
    print("Face Attendance - Enroll")
    print("=" * 60)

    person_code = (args.code or read_input("Masukkan kode user   : ")).upper()
    person_name = args.name or read_input("Masukkan nama user   : ")
    samples_target = normalize_target_samples(args.samples)
    samples_per_angle = samples_target // len(ENROLL_ANGLES)
    if args.samples != DEFAULT_TOTAL_SAMPLES:
        print(f"Catatan: --samples diabaikan, enroll dikunci {DEFAULT_TOTAL_SAMPLES} foto.")

    print(f"\nTarget samples: {samples_target}")
    print(
        f"Mode {len(ENROLL_ANGLES)} sudut aktif: {samples_per_angle} foto per sudut, "
        f"delay {ENROLL_ANGLE_DELAY_SEC:.0f} detik tiap sudut."
    )
    print(
        "Urutan sudut: Depan -> Menoleh Kiri -> Menoleh Kanan -> "
        "Tengadah -> Menunduk -> Miring Kiri -> Miring Kanan"
    )
    print("Tekan 'q' untuk batal.\n")

    utils.ensure_directories()
    utils.init_database()
    utils.setup_face_cascade()
    detector = utils.load_face_detector()

    person_data = utils.add_or_update_person(person_code, person_name)
    print(
        f"Registered person: {person_data['person_name']} "
        f"({person_data['person_code']})"
    )

    person_dir = os.path.join(utils.DATASET_DIR, person_code)
    os.makedirs(person_dir, exist_ok=True)
    existing_samples = len(
        [
            f
            for f in os.listdir(person_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]
    )
    print(f"Existing samples: {existing_samples}")

    camera = None
    camera_type = None
    captured = 0
    captured_in_angle = 0
    current_angle_index = 0
    angle_started_ts = 0.0
    last_capture_time = 0.0
    min_capture_interval = 0.15

    try:
        camera, camera_type = utils.open_camera()
        print(f"Camera ready: {camera_type}")
        angle_started_ts = time.time()
        print(
            f"Sudut 1/{len(ENROLL_ANGLES)}: Depan. "
            f"Tahan posisi, capture dimulai dalam {ENROLL_ANGLE_DELAY_SEC:.0f} detik."
        )

        while captured < samples_target:
            ret, frame = utils.read_frame(camera, camera_type)
            if not ret:
                print("Failed to read frame.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_box, face_roi = detect_largest_face_with_rotation(detector, gray)

            now = time.time()
            angle_label = ENROLL_ANGLES[current_angle_index][1]
            wait_remaining = max(0.0, ENROLL_ANGLE_DELAY_SEC - (now - angle_started_ts))

            if face_box is not None and face_roi is not None:
                x, y, w, h = face_box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (20, 220, 20), 2)

                if wait_remaining <= 0 and now - last_capture_time >= min_capture_interval:
                    sample_index = existing_samples + captured + 1
                    utils.save_face_sample(person_code, face_roi, sample_index)
                    captured += 1
                    captured_in_angle += 1
                    last_capture_time = now

                    if captured_in_angle >= samples_per_angle and captured < samples_target:
                        current_angle_index += 1
                        captured_in_angle = 0
                        angle_started_ts = now
                        last_capture_time = 0.0
                        _, next_label = ENROLL_ANGLES[current_angle_index]
                        print(
                            f"Sudut {current_angle_index + 1}/{len(ENROLL_ANGLES)}: "
                            f"{next_label}. "
                            f"Tunggu {ENROLL_ANGLE_DELAY_SEC:.0f} detik."
                        )

            cv2.putText(
                frame,
                f"Capturing: {captured}/{samples_target}",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (10, 220, 10),
                2,
            )
            cv2.putText(
                frame,
                f"Angle: {current_angle_index + 1}/{len(ENROLL_ANGLES)} - {angle_label}",
                (10, 55),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 220, 40),
                2,
            )
            if wait_remaining > 0:
                cv2.putText(
                    frame,
                    f"Capture starts in: {wait_remaining:.1f}s",
                    (10, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 180, 255),
                    2,
                )
            cv2.putText(
                frame,
                "Press Q to stop",
                (10, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

            cv2.imshow("Enroll Face", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\nEnroll dihentikan user.")
                break

    except Exception as exc:
        print(f"Error during enroll: {exc}")

    finally:
        if camera is not None:
            utils.close_camera(camera, camera_type)
        cv2.destroyAllWindows()

    print(f"\nCaptured new samples: {captured}")
    if captured == 0:
        print("Tidak ada sample baru. Training dibatalkan.")
        return

    try:
        total_people, total_images = utils.train_lbph_model()
        print("Training selesai.")
        print(f"Total people in model : {total_people}")
        print(f"Total face samples    : {total_images}")
        print(f"Model path            : {utils.MODEL_PATH}")
    except Exception as exc:
        print(f"Training failed: {exc}")


if __name__ == "__main__":
    main()
