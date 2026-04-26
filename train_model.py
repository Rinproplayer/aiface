"""
Train Model - Mã hóa khuôn mặt
==================================
Đọc ảnh từ dataset, tạo face encoding cho mỗi sinh viên.
Sử dụng: python train_model.py
"""

from face_engine import FaceEngine


def main():
    print("=" * 50)
    print("🧠 TRAIN MODEL NHẬN DIỆN KHUÔN MẶT")
    print("=" * 50)
    print()

    engine = FaceEngine()
    success = engine.train_from_dataset()

    if success:
        print("\n" + "=" * 50)
        print("✅ TRAIN HOÀN TẤT!")
        print("=" * 50)
        print(f"📊 Tổng số encoding: {len(engine.known_encodings)}")
        print(f"👥 Số sinh viên: {len(set(engine.known_student_codes))}")
        print("\n➡️  Tiếp theo: chạy 'python main.py' để bắt đầu điểm danh")
    else:
        print("\n❌ Train thất bại! Kiểm tra lại thư mục dataset/")


if __name__ == "__main__":
    main()
