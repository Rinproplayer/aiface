"""
Train Model - Ma hoa khuon mat (NANG CAP)
============================================
Doc anh tu dataset, tien xu ly, tao face encoding.
Su dung: python train_model.py
"""

import sys
# Cấu hình encoding UTF-8 cho Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from face_engine import FaceEngine


def main():
    print("=" * 50)
    print("TRAIN MODEL NHAN DIEN KHUON MAT")
    print("=" * 50)
    print()
    print("Cai thien:")
    print("  - Tien xu ly anh (CLAHE can bang sang)")
    print("  - Upsample x2 de phat hien mat nho")
    print("  - Num_jitters=3 de encode chinh xac hon")
    print()

    engine = FaceEngine()
    success = engine.train_from_dataset()

    if success:
        print("\n" + "=" * 50)
        print("TRAIN HOAN TAT!")
        print("=" * 50)
        print(f"Tong so encoding: {len(engine.known_encodings)}")
        print(f"So sinh vien: {len(set(engine.known_student_codes))}")
        print("\nTiep theo: chay 'python main.py' de bat dau diem danh")
    else:
        print("\nTrain that bai! Kiem tra lai thu muc dataset/")


if __name__ == "__main__":
    main()
