#!/usr/bin/env python3
"""
Bab 21.0: Test Camera + Face Detection
======================================
Verifikasi kamera dan deteksi wajah (YuNet) sebelum enroll/absensi.
"""

import time

import cv2

import attendance_utils as utils

print("=" * 60)
print("Face Attendance - Camera Test")
print("=" * 60)

utils.ensure_directories()
utils.init_database()
detector, _ = utils.load_face_analyzers()

camera = None
camera_type = None

try:
    camera, camera_type = utils.open_camera()
    print(f"Camera ready: {camera_type}")
    print("Running test for 10 seconds. Press 'q' to stop.\n")

    start_time = time.time()
    frame_count = 0

    while True:
        ret, frame = utils.read_frame(camera, camera_type)
        if not ret:
            print("Failed to read frame.")
            break

        frame_count += 1
        faces = utils.detect_faces(detector, frame)
        for face_row in faces:
            x, y, w, h = [int(v) for v in face_row[:4]]
            x = max(0, x)
            y = max(0, y)
            w = max(1, min(w, frame.shape[1] - x))
            h = max(1, min(h, frame.shape[0] - y))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 200, 0), 2)

        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0.0
        cv2.putText(
            frame,
            f"Faces: {len(faces)} | FPS: {fps:.1f}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (20, 220, 20),
            2,
        )

        cv2.imshow("Face Attendance Camera Test (press Q)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if elapsed >= 10:
            break

    total_time = time.time() - start_time
    fps = frame_count / total_time if total_time > 0 else 0.0
    print("\nTest finished.")
    print(f"Frames captured: {frame_count}")
    print(f"Average FPS: {fps:.1f}")

except Exception as exc:
    print(f"Error: {exc}")

finally:
    if camera is not None:
        utils.close_camera(camera, camera_type)
    cv2.destroyAllWindows()
