-- ============================================
-- AI FACE RECOGNITION ATTENDANCE SYSTEM
-- Script tạo Database và các bảng
-- ============================================

-- Tạo database
CREATE DATABASE IF NOT EXISTS aiface_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aiface_db;

-- ============================================
-- BẢNG 1: GIẢNG VIÊN (lecturers)
-- ============================================
CREATE TABLE IF NOT EXISTS lecturers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT 'Tên đăng nhập',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Mật khẩu đã mã hóa',
    full_name VARCHAR(100) NOT NULL COMMENT 'Họ và tên',
    email VARCHAR(100) COMMENT 'Email',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) COMMENT = 'Bảng lưu thông tin giảng viên';

-- ============================================
-- BẢNG 2: LỚP HỌC (classes)
-- ============================================
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_code VARCHAR(20) UNIQUE NOT NULL COMMENT 'Mã lớp: CS101, IT202...',
    class_name VARCHAR(100) NOT NULL COMMENT 'Tên lớp học',
    lecturer_id INT COMMENT 'Giảng viên phụ trách',
    schedule VARCHAR(200) COMMENT 'Lịch học: T2-T4 7:30-9:00',
    room VARCHAR(50) COMMENT 'Phòng học',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE SET NULL
) COMMENT = 'Bảng lưu thông tin lớp học';

-- ============================================
-- BẢNG 3: SINH VIÊN (students)
-- ============================================
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_code VARCHAR(20) UNIQUE NOT NULL COMMENT 'Mã sinh viên: SV001',
    full_name VARCHAR(100) NOT NULL COMMENT 'Họ và tên',
    email VARCHAR(100) COMMENT 'Email',
    phone VARCHAR(20) COMMENT 'Số điện thoại',
    photo_path VARCHAR(255) COMMENT 'Đường dẫn ảnh đại diện',
    face_registered BOOLEAN DEFAULT FALSE COMMENT 'Đã đăng ký khuôn mặt chưa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) COMMENT = 'Bảng lưu thông tin sinh viên';

-- ============================================
-- BẢNG 4: SINH VIÊN - LỚP HỌC (student_classes)
-- Quan hệ nhiều-nhiều: 1 SV có thể học nhiều lớp
-- ============================================
CREATE TABLE IF NOT EXISTS student_classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, class_id)
) COMMENT = 'Bảng liên kết sinh viên với lớp học';

-- ============================================
-- BẢNG 5: ĐIỂM DANH (attendance)
-- ============================================
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    date DATE NOT NULL COMMENT 'Ngày điểm danh',
    check_in_time DATETIME NOT NULL COMMENT 'Thời gian điểm danh',
    status ENUM('present', 'late', 'absent') DEFAULT 'present' COMMENT 'Trạng thái',
    confidence FLOAT DEFAULT 0 COMMENT 'Độ tin cậy nhận diện (0-1)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, class_id, date)
) COMMENT = 'Bảng ghi nhận điểm danh';

-- ============================================
-- DỮ LIỆU MẪU
-- ============================================

-- Tạo tài khoản giảng viên mặc định
-- Username: admin | Password: admin123
INSERT IGNORE INTO lecturers (username, password_hash, full_name, email) VALUES 
('admin', '$2b$12$LJ3m4ys3GZwnk3MqFJG8mu8JQoXvJxFqGM1E0x3hGvp6bQ6j1u6K.', 'Quản Trị Viên', 'admin@university.edu'),
('giangvien1', '$2b$12$LJ3m4ys3GZwnk3MqFJG8mu8JQoXvJxFqGM1E0x3hGvp6bQ6j1u6K.', 'Nguyễn Văn A', 'nguyenvana@university.edu');

-- Tạo lớp học mẫu
INSERT IGNORE INTO classes (class_code, class_name, lecturer_id, schedule, room) VALUES
('CS101', 'Nhập môn Lập trình', 1, 'Thứ 2 - Thứ 4, 7:30 - 9:00', 'A101'),
('IT202', 'Cơ sở dữ liệu', 1, 'Thứ 3 - Thứ 5, 9:30 - 11:00', 'B205'),
('AI301', 'Trí tuệ nhân tạo', 2, 'Thứ 2 - Thứ 6, 13:30 - 15:00', 'C301');

SELECT 'Database aiface_db đã được tạo thành công!' AS message;
