#!/usr/bin/env python3
"""
Bab 21.2: Realtime Face Attendance
==================================
Melakukan pengenalan wajah dan mencatat check-in 1x per hari.
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
        default=60.0,
        help="Batas confidence LBPH (lebih kecil = lebih ketat)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("Face Attendance - Realtime")
    print("=" * 60)
    print(f"Recognition threshold: {args.threshold:.1f}\n")

    utils.ensure_directories()
    utils.init_database()
    utils.setup_face_cascade()
    detector = utils.load_face_detector()

    try:
        recognizer, labels_map = utils.load_recognizer()
    except Exception as exc:
        print(f"Model load failed: {exc}")
        print("Jalankan 01_enroll_face.py dulu.")
        return

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

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(80, 80),
            )

            for (x, y, w, h) in faces:
                face_roi = gray[y : y + h, x : x + w]
                face_roi = cv2.resize(face_roi, (200, 200))
                pred_label, confidence = recognizer.predict(face_roi)

                label_data = labels_map.get(str(pred_label))
                is_known = label_data is not None and confidence <= args.threshold

                if is_known:
                    person_id = label_data["person_id"]
                    person_name = label_data["person_name"]
                    person_code = label_data["person_code"]
                    text = f"{person_name} ({person_code}) {confidence:.1f}"
                    color = (20, 220, 20)

                    now_ts = time.time()
                    if now_ts - recent_mark.get(person_id, 0) > 3:
                        saved = utils.mark_attendance(label_data, confidence)
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
                    text = f"Unknown {confidence:.1f}"
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
