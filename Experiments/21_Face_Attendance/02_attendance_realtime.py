#!/usr/bin/env python3
"""
Bab 21.2: Realtime Face Attendance
==================================
Melakukan pengenalan wajah (embedding SFace) dan mencatat check-in 1x per hari.
"""

import argparse
import time
from datetime import datetime

import cv2

import attendance_utils as utils


def parse_args():
    parser = argparse.ArgumentParser(description="Realtime absensi wajah")
    parser.add_argument(
        "--threshold",
        type=float,
        default=utils.DEFAULT_FACE_MATCH_THRESHOLD,
        help="Batas cosine similarity (lebih besar = lebih ketat), contoh 0.36",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("Face Attendance - Realtime")
    print("=" * 60)
    print(f"Cosine threshold: {args.threshold:.3f}\n")

    utils.ensure_directories()
    utils.init_database()

    try:
        detector, recognizer = utils.load_face_analyzers()
        embeddings_index, default_threshold = utils.load_face_embeddings_index()
    except Exception as exc:
        print(f"Model load failed: {exc}")
        print("Jalankan 01_enroll_face.py dulu.")
        return
    threshold = max(0.0, min(1.0, args.threshold or default_threshold))

    camera = None
    camera_type = None
    recent_mark = {}

    try:
        camera, camera_type = utils.open_camera()
        print(f"Camera ready: {camera_type}")
        print("Press 'q' to quit.\n")

        while True:
            ret, frame = utils.read_frame(camera, camera_type)
            if not ret:
                print("Failed to read frame.")
                break

            faces = utils.detect_faces(detector, frame)

            for face_row in faces:
                x, y, w, h = [int(v) for v in face_row[:4]]
                x = max(0, x)
                y = max(0, y)
                w = max(1, min(w, frame.shape[1] - x))
                h = max(1, min(h, frame.shape[0] - y))

                feature = utils.extract_face_feature(frame, face_row, recognizer)
                label_data, similarity = utils.identify_face(
                    feature,
                    embeddings_index,
                    threshold,
                )
                is_known = label_data is not None

                if is_known:
                    person_id = label_data["person_id"]
                    person_name = label_data["person_name"]
                    person_code = label_data["person_code"]
                    text = f"{person_name} ({person_code}) sim:{similarity:.3f}"
                    color = (20, 220, 20)

                    now_ts = time.time()
                    if now_ts - recent_mark.get(person_id, 0) > 3:
                        saved = utils.mark_attendance(label_data, similarity)
                        ts = datetime.now().strftime("%H:%M:%S")
                        if saved:
                            print(f"[{ts}] CHECK-IN: {person_name} ({person_code})")
                        else:
                            print(
                                f"[{ts}] ALREADY CHECKED TODAY: "
                                f"{person_name} ({person_code})"
                            )
                        recent_mark[person_id] = now_ts
                else:
                    text = f"Unknown sim:{similarity:.3f}"
                    color = (20, 20, 230)

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(
                    frame,
                    text,
                    (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

            cv2.putText(
                frame,
                "Press Q to quit",
                (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

            cv2.imshow("Realtime Face Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as exc:
        print(f"Runtime error: {exc}")

    finally:
        if camera is not None:
            utils.close_camera(camera, camera_type)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
