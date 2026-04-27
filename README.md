# 🎓 AI Face Recognition Attendance System
## Hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt

### 📋 Mô tả
Hệ thống sử dụng AI nhận diện khuôn mặt để tự động điểm danh sinh viên.
Giảng viên quản lý sinh viên, lớp học và xem báo cáo qua web dashboard.

### ⚙️ Công nghệ
- **AI/CV**: face_recognition, OpenCV, dlib
- **Backend**: FastAPI, WebSocket
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MySQL
- **Auth**: JWT Token + bcrypt

---

## 🚀 Cài đặt & Chạy

### Bước 1: Cài thư viện
```bash
pip install -r requirements.txt
pip install dlib-bin
pip install face-recognition --no-deps
pip install face-recognition-models
pip install setuptools<81
pip install requests
```

### Bước 2: Tạo Database
```bash
python setup_db.py
python fix_password.py
```

### Bước 3: Chạy Server
```bash
python server.py
```
Mở trình duyệt: **http://localhost:8000**
- Tài khoản: `admin` / `admin123`

### Bước 4: Đăng ký khuôn mặt
```bash
python register_face.py
```

### Bước 5: Train model
```bash
python train_model.py
```

### Bước 6: Bắt đầu điểm danh
```bash
python main.py
```

---

## 📁 Cấu trúc dự án
```
AIFace/
├── main.py              # Điểm danh qua webcam
├── register_face.py     # Đăng ký khuôn mặt SV
├── train_model.py       # Train model nhận diện
├── server.py            # FastAPI server + WebSocket
├── config.py            # Cấu hình hệ thống
├── database.py          # Thao tác MySQL
├── auth.py              # JWT authentication
├── face_engine.py       # Engine nhận diện khuôn mặt
├── setup_db.py          # Script tạo database
├── web/                 # Web Dashboard
│   ├── index.html       # Trang đăng nhập
│   ├── dashboard.html   # Tổng quan
│   ├── students.html    # Quản lý sinh viên
│   ├── classes.html     # Quản lý lớp học
│   ├── attendance.html  # Xem điểm danh
│   ├── css/style.css    # Giao diện
│   └── js/app.js        # Logic JavaScript
├── dataset/             # Ảnh khuôn mặt SV
├── encodings/           # Model đã train
└── exports/             # File Excel xuất ra
```

## 🔑 Tính năng
- ✅ Đăng nhập giảng viên (JWT)
- ✅ Quản lý sinh viên (CRUD)
- ✅ Quản lý nhiều lớp học
- ✅ Đăng ký khuôn mặt qua webcam
- ✅ Nhận diện & điểm danh tự động
- ✅ Dashboard realtime (WebSocket)
- ✅ Xuất báo cáo Excel
- ✅ Thống kê điểm danh
