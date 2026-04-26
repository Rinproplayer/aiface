"""
Đăng ký khuôn mặt sinh viên
==============================
Chụp ảnh khuôn mặt sinh viên qua webcam và lưu vào dataset.
Sử dụng: python register_face.py
"""

import os
import cv2
from config import DATASET_DIR, NUM_PHOTOS_PER_STUDENT, CAMERA_INDEX
from database import add_student, get_student_by_code, update_face_registered

try:
    import face_recognition
    FACE_LIB = True
except ImportError:
    FACE_LIB = False


def register_face():
    """Đăng ký khuôn mặt sinh viên mới qua webcam"""
    print("=" * 50)
    print("📸 ĐĂNG KÝ KHUÔN MẶT SINH VIÊN")
    print("=" * 50)

    # Nhập thông tin sinh viên
    student_code = input("\n📝 Nhập mã sinh viên (VD: SV001): ").strip()
    if not student_code:
        print("❌ Mã sinh viên không được để trống!")
        return

    full_name = input("📝 Nhập họ tên sinh viên: ").strip()
    if not full_name:
        print("❌ Họ tên không được để trống!")
        return

    email = input("📝 Nhập email (bỏ trống nếu không có): ").strip()
    phone = input("📝 Nhập SĐT (bỏ trống nếu không có): ").strip()

    # Kiểm tra sinh viên đã tồn tại chưa
    existing = get_student_by_code(student_code)
    if existing:
        print(f"⚠️ Sinh viên {student_code} đã tồn tại: {existing['full_name']}")
        choice = input("Bạn có muốn đăng ký lại khuôn mặt? (y/n): ").strip().lower()
        if choice != "y":
            return
        student_id = existing["id"]
    else:
        # Thêm sinh viên vào database
        student_id = add_student(student_code, full_name, email, phone)
        if not student_id:
            print("❌ Không thể thêm sinh viên vào database!")
            return

    # Tạo thư mục lưu ảnh
    folder_name = f"{student_code}_{full_name.replace(' ', '_')}"
    student_dir = os.path.join(DATASET_DIR, folder_name)
    os.makedirs(student_dir, exist_ok=True)

    # Mở webcam
    print(f"\n📷 Mở webcam để chụp {NUM_PHOTOS_PER_STUDENT} ảnh...")
    print("   Nhấn SPACE để chụp | Nhấn Q để hủy")
    print("   Hãy quay mặt ở nhiều góc độ khác nhau để tăng độ chính xác!")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ Không thể mở webcam!")
        return

    photo_count = 0

    while photo_count < NUM_PHOTOS_PER_STUDENT:
        ret, frame = cap.read()
        if not ret:
            break

        # Hiển thị hướng dẫn trên frame
        display = frame.copy()
        cv2.putText(display, f"Anh {photo_count + 1}/{NUM_PHOTOS_PER_STUDENT} - SPACE: Chup | Q: Huy",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, f"SV: {student_code} - {full_name}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Phát hiện khuôn mặt và vẽ khung
        if FACE_LIB:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locs = face_recognition.face_locations(rgb)
            for (top, right, bottom, left) in face_locs:
                cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)
            if not face_locs:
                cv2.putText(display, "Khong thay khuon mat!", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("Dang ky khuon mat", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            print("⚠️ Đã hủy đăng ký!")
            break
        elif key == ord(' '):  # SPACE
            # Kiểm tra có khuôn mặt không
            if FACE_LIB:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locs = face_recognition.face_locations(rgb)
                if not face_locs:
                    print("  ❌ Không phát hiện khuôn mặt! Hãy đưa mặt vào camera.")
                    continue

            photo_count += 1
            photo_path = os.path.join(student_dir, f"{photo_count}.jpg")
            cv2.imwrite(photo_path, frame)
            print(f"  ✅ Đã chụp ảnh {photo_count}/{NUM_PHOTOS_PER_STUDENT}")

    cap.release()
    cv2.destroyAllWindows()

    if photo_count >= NUM_PHOTOS_PER_STUDENT:
        # Cập nhật trạng thái đăng ký khuôn mặt
        first_photo = os.path.join(student_dir, "1.jpg")
        update_face_registered(student_id, True, first_photo)
        print(f"\n🎉 Đăng ký khuôn mặt thành công cho {full_name}!")
        print(f"   Đã lưu {photo_count} ảnh vào: {student_dir}")
        print(f"   ➡️  Tiếp theo: chạy 'python train_model.py' để train model")
    else:
        print(f"\n⚠️ Chỉ chụp được {photo_count}/{NUM_PHOTOS_PER_STUDENT} ảnh.")


if __name__ == "__main__":
    register_face()
