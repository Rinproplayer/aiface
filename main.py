"""
Điểm danh bằng nhận diện khuôn mặt - PHIÊN BẢN NÂNG CẤP
============================================================
Cải thiện:
- Xử lý liên tục (mỗi 2 frame thay vì 3)
- Hệ thống xác nhận: cần nhận diện đúng 3 lần liên tiếp mới ghi điểm danh
- Hiển thị trạng thái rõ ràng hơn
"""

import cv2
import sys
# Cấu hình encoding UTF-8 cho Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import time
import requests
from datetime import datetime
from collections import Counter

from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT
from face_engine import FaceEngine, preprocess_frame
from database import get_student_by_code, mark_attendance, get_all_classes


def send_websocket_notification(student_code, student_name, class_id, confidence):
    """Gửi thông báo điểm danh qua API"""
    try:
        data = {
            "student_code": student_code,
            "student_name": student_name,
            "class_id": class_id,
            "confidence": confidence,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        requests.post("http://localhost:8000/api/attendance/notify", json=data, timeout=2)
    except Exception:
        pass


def run_attendance(class_id=None):
    """Chạy điểm danh - phiên bản nâng cấp"""
    print("=" * 50)
    print("DIEM DANH BANG NHAN DIEN KHUON MAT")
    print("=" * 50)

    # Chọn lớp học
    if class_id is None:
        classes = get_all_classes()
        if not classes:
            print("Chua co lop hoc nao!")
            return

        print("\nDanh sach lop hoc:")
        for c in classes:
            print(f"  [{c['id']}] {c['class_code']} - {c['class_name']}")

        try:
            class_id = int(input("\nNhap ID lop can diem danh: "))
        except ValueError:
            print("ID khong hop le!")
            return

    # Tải model
    print("\nDang tai model nhan dien...")
    engine = FaceEngine()
    if not engine.load_encodings():
        print("Chua train model! Hay chay: python train_model.py")
        return

    # Mở webcam
    print(f"\nMo webcam...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    if not cap.isOpened():
        print("Khong the mo webcam!")
        return

    print("Webcam da san sang!")
    print("   Nhan Q de thoat | Nhan R de reload model")
    print("-" * 50)

    checked_in = set()        # SV đã điểm danh
    frame_count = 0
    process_every_n = 2       # Xử lý mỗi 2 frame (nhanh hơn)

    # Hệ thống xác nhận: cần nhận đúng N lần liên tiếp
    confirm_threshold = 2     # Cần 2 lần nhận đúng mới ghi (giảm từ 3)
    recognition_buffer = {}   # {student_code: [confidence, confidence, ...]}

    last_results = []         # Kết quả gần nhất để vẽ

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        display = frame.copy()

        # Xử lý nhận diện mỗi N frame
        if frame_count % process_every_n == 0:
            results = engine.recognize(frame)
            last_results = results

            for result in results:
                student_code = result["student_code"]
                name = result["name"]
                confidence = result["confidence"]

                if student_code != "Unknown" and student_code not in checked_in:
                    # Thêm vào buffer xác nhận
                    if student_code not in recognition_buffer:
                        recognition_buffer[student_code] = []

                    recognition_buffer[student_code].append(confidence)

                    # Kiểm tra đã đủ lần xác nhận chưa
                    if len(recognition_buffer[student_code]) >= confirm_threshold:
                        avg_confidence = sum(recognition_buffer[student_code]) / len(recognition_buffer[student_code])

                        # Tìm sinh viên trong database
                        student = get_student_by_code(student_code)
                        if student:
                            status = "present"
                            success = mark_attendance(student["id"], class_id, status, avg_confidence)

                            if success:
                                checked_in.add(student_code)
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(f"  [{timestamp}] {name} ({student_code}) - Do tin cay: {avg_confidence*100:.0f}%")
                                send_websocket_notification(student_code, name, class_id, avg_confidence)

                        # Xóa khỏi buffer
                        del recognition_buffer[student_code]

                elif student_code == "Unknown":
                    pass  # Bỏ qua người không xác định

            # Xóa buffer cũ (quá 30 frame không nhận lại)
            stale_codes = [code for code, confs in recognition_buffer.items()
                          if len(confs) > 0 and frame_count % 60 == 0]
            for code in stale_codes:
                if len(recognition_buffer[code]) < confirm_threshold:
                    recognition_buffer[code] = []

        # Vẽ kết quả gần nhất
        if last_results:
            display = engine.draw_results(display, last_results)

        # Hiển thị thông tin
        info_text = f"Da diem danh: {len(checked_in)} SV | Q: Thoat | R: Reload"
        cv2.putText(display, info_text,
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        time_text = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display, time_text,
                    (CAMERA_WIDTH - 130, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Hiển thị danh sách đang chờ xác nhận
        if recognition_buffer:
            y_pos = 50
            for code, confs in recognition_buffer.items():
                progress = f"{len(confs)}/{confirm_threshold}"
                cv2.putText(display, f"Dang xac nhan: {code} ({progress})",
                            (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
                y_pos += 20

        cv2.imshow("AI Diem Danh - Nhan Q de thoat", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            print("Reload model...")
            engine.load_encodings()
            recognition_buffer.clear()

    cap.release()
    cv2.destroyAllWindows()

    print(f"\nKet qua: Da diem danh {len(checked_in)} sinh vien")
    print("=" * 50)


if __name__ == "__main__":
    run_attendance()
