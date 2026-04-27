"""
Đăng ký khuôn mặt sinh viên - PHIÊN BẢN NÂNG CẤP
=====================================================
Cải thiện:
- Dùng Haar Cascade (nhanh, ổn định) để phát hiện mặt khi chụp
- Tiền xử lý CLAHE cho điều kiện ngược sáng
- Tự động chụp khi phát hiện khuôn mặt ổn định
- Hướng dẫn quay nhiều góc
"""

import os
import cv2
import time
from config import DATASET_DIR, NUM_PHOTOS_PER_STUDENT, CAMERA_INDEX
from database import add_student, get_student_by_code, update_face_registered
from face_engine import preprocess_frame, detect_faces_haar

# Haar cascade cho phát hiện nhanh
HAAR_FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def detect_face_for_register(frame):
    """Phát hiện khuôn mặt bằng Haar Cascade (nhanh hơn face_recognition)"""
    # Tiền xử lý
    enhanced = preprocess_frame(frame)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = HAAR_FACE.detectMultiScale(
        gray,
        scaleFactor=1.05,      # Giảm scale factor = phát hiện tốt hơn
        minNeighbors=3,        # Giảm = dễ phát hiện hơn
        minSize=(80, 80),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return faces


def register_face():
    """Đăng ký khuôn mặt sinh viên mới qua webcam"""
    print("=" * 50)
    print("DANG KY KHUON MAT SINH VIEN")
    print("=" * 50)

    # Nhập thông tin sinh viên
    student_code = input("\nNhap ma sinh vien (VD: SV001): ").strip()
    if not student_code:
        print("Ma sinh vien khong duoc de trong!")
        return

    full_name = input("Nhap ho ten sinh vien: ").strip()
    if not full_name:
        print("Ho ten khong duoc de trong!")
        return

    email = input("Nhap email (bo trong neu khong co): ").strip()
    phone = input("Nhap SDT (bo trong neu khong co): ").strip()

    # Kiểm tra sinh viên đã tồn tại chưa
    existing = get_student_by_code(student_code)
    if existing:
        print(f"Sinh vien {student_code} da ton tai: {existing['full_name']}")
        choice = input("Ban co muon dang ky lai khuon mat? (y/n): ").strip().lower()
        if choice != "y":
            return
        student_id = existing["id"]
    else:
        student_id = add_student(student_code, full_name, email, phone)
        if not student_id:
            print("Khong the them sinh vien vao database!")
            return

    # Tạo thư mục lưu ảnh
    folder_name = f"{student_code}_{full_name.replace(' ', '_')}"
    student_dir = os.path.join(DATASET_DIR, folder_name)
    os.makedirs(student_dir, exist_ok=True)

    # Mở webcam
    num_photos = NUM_PHOTOS_PER_STUDENT
    print(f"\nMo webcam de chup {num_photos} anh...")
    print("   Nhan SPACE de chup | Nhan Q de huy")
    print("   Hay quay mat o nhieu goc do khac nhau!")
    print("   Goc doc: Thang, nghieng trai, nghieng phai")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Khong the mo webcam!")
        return

    # Tăng độ phân giải camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    photo_count = 0
    no_face_count = 0
    last_capture_time = 0

    # Hướng dẫn cho từng ảnh
    guides = [
        "Nhin thang vao camera",
        "Nghieng dau sang TRAI",
        "Nghieng dau sang PHAI",
        "Nhin LEN tren",
        "Nhin XUONG duoi",
        "Cuoi",
        "Mat binh thuong",
        "Quay nhe sang trai",
        "Quay nhe sang phai",
        "Nhin thang - binh thuong",
    ]

    while photo_count < num_photos:
        ret, frame = cap.read()
        if not ret:
            break

        # Phát hiện khuôn mặt
        faces = detect_face_for_register(frame)
        has_face = len(faces) > 0

        # Hiển thị
        display = frame.copy()

        # Vẽ khung khuôn mặt
        if has_face:
            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            no_face_count = 0
        else:
            no_face_count += 1

        # Hiển thị hướng dẫn
        guide_text = guides[photo_count] if photo_count < len(guides) else "Nhin thang"
        cv2.putText(display, f"Anh {photo_count+1}/{num_photos} - SPACE: Chup | Q: Huy",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(display, f"SV: {student_code} - {full_name}",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        cv2.putText(display, f"Huong dan: {guide_text}",
                    (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)

        if has_face:
            cv2.putText(display, "DA PHAT HIEN KHUON MAT - Nhan SPACE",
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            cv2.putText(display, "Dang tim khuon mat...",
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        cv2.imshow("Dang ky khuon mat", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("Da huy dang ky!")
            break
        elif key == ord(' '):  # SPACE
            if not has_face:
                print("  Khong phat hien khuon mat! Dua mat vao camera.")
                continue

            # Đợi ít nhất 0.3s giữa các lần chụp
            now = time.time()
            if now - last_capture_time < 0.3:
                continue

            photo_count += 1
            photo_path = os.path.join(student_dir, f"{photo_count}.jpg")

            # Lưu ảnh gốc (không có khung vẽ)
            cv2.imwrite(photo_path, frame)

            # Lưu thêm ảnh đã enhance (tăng dữ liệu train)
            enhanced = preprocess_frame(frame)
            enhanced_path = os.path.join(student_dir, f"{photo_count}_enhanced.jpg")
            cv2.imwrite(enhanced_path, enhanced)

            last_capture_time = now
            print(f"  Da chup anh {photo_count}/{num_photos} ({guide_text})")

    cap.release()
    cv2.destroyAllWindows()

    if photo_count >= num_photos:
        first_photo = os.path.join(student_dir, "1.jpg")
        update_face_registered(student_id, True, first_photo)
        print(f"\nDang ky khuon mat thanh cong cho {full_name}!")
        print(f"   Da luu {photo_count * 2} anh vao: {student_dir}")
        print(f"   Tiep theo: chay 'python train_model.py'")
    else:
        print(f"\nChi chup duoc {photo_count}/{num_photos} anh.")
        if photo_count > 0:
            first_photo = os.path.join(student_dir, "1.jpg")
            update_face_registered(student_id, True, first_photo)
            print("Van co the train voi so anh hien tai.")
            print("Chay: python train_model.py")


if __name__ == "__main__":
    register_face()
