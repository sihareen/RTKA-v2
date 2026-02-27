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

import attendance_utils as utils


def parse_args():
    parser = argparse.ArgumentParser(description="Enroll wajah untuk attendance")
    parser.add_argument("--code", type=str, help="Kode user, contoh: EMP001")
    parser.add_argument("--name", type=str, help="Nama user")
    parser.add_argument("--samples", type=int, default=30, help="Jumlah sampel wajah")
    return parser.parse_args()


def read_input(prompt):
    value = input(prompt).strip()
    if not value:
        raise ValueError("Input tidak boleh kosong")
    return value


def main():
    args = parse_args()

    print("=" * 60)
    print("Face Attendance - Enroll")
    print("=" * 60)

    person_code = (args.code or read_input("Masukkan kode user   : ")).upper()
    person_name = args.name or read_input("Masukkan nama user   : ")
    samples_target = max(5, args.samples)

    print(f"\nTarget samples: {samples_target}")
    print("Tips: hadap kamera, ubah ekspresi/angle sedikit saat capture.")
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
    last_capture_time = 0.0
    min_capture_interval = 0.15

    try:
        camera, camera_type = utils.open_camera()
        print(f"Camera ready: {camera_type}")

        while captured < samples_target:
            ret, frame = utils.read_frame(camera, camera_type)
            if not ret:
                print("Failed to read frame.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(80, 80),
            )

            if len(faces) > 0:
                # Ambil wajah terbesar agar data training lebih stabil.
                x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (20, 220, 20), 2)
                face_roi = gray[y : y + h, x : x + w]

                now = time.time()
                if now - last_capture_time >= min_capture_interval:
                    sample_index = existing_samples + captured + 1
                    utils.save_face_sample(person_code, face_roi, sample_index)
                    captured += 1
                    last_capture_time = now

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
                "Press Q to stop",
                (10, 55),
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
