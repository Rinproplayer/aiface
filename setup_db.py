"""Script tạo database và dữ liệu mẫu"""
import sys
# Cấu hình encoding UTF-8 cho Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import mysql.connector

print("=" * 50)
print("🗄️  SETUP DATABASE")
print("=" * 50)

# Step 1: Create database
conn = mysql.connector.connect(host="localhost", user="root", password="")
cursor = conn.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS aiface_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
conn.commit()
print("✅ 1. Database 'aiface_db' created")
conn.close()

# Step 2: Create tables
conn = mysql.connector.connect(host="localhost", user="root", password="", database="aiface_db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS lecturers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'lecturer') DEFAULT 'lecturer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

# Thêm cột role nếu bảng đã tồn tại nhưng chưa có cột role
try:
    cursor.execute("ALTER TABLE lecturers ADD COLUMN role ENUM('admin', 'lecturer') DEFAULT 'lecturer'")
    print("  ✅ Added 'role' column to lecturers")
except:
    pass  # Cột đã tồn tại

cursor.execute("""CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_code VARCHAR(20) UNIQUE NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    lecturer_id INT,
    schedule VARCHAR(200),
    room VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecturer_id) REFERENCES lecturers(id) ON DELETE SET NULL
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_code VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    photo_path VARCHAR(255),
    face_registered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS student_classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, class_id)
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    class_id INT NOT NULL,
    date DATE NOT NULL,
    check_in_time DATETIME NOT NULL,
    status ENUM('present', 'late', 'absent') DEFAULT 'present',
    confidence FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, class_id, date)
)""")

print("✅ 2. All tables created")

# Step 3: Insert sample data - admin account with password "admin123"
hash_pw = "$2b$12$LJ3m4ys3GZwnk3MqFJG8mu8JQoXvJxFqGM1E0x3hGvp6bQ6j1u6K."
try:
    cursor.execute(
        "INSERT IGNORE INTO lecturers (username, password_hash, full_name, email, role) VALUES (%s, %s, %s, %s, %s)",
        ("admin", hash_pw, "Admin", "admin@university.edu", "admin")
    )
    # Cập nhật role cho admin nếu đã tồn tại
    cursor.execute("UPDATE lecturers SET role='admin' WHERE username='admin'")
except Exception as e:
    print(f"  Note: {e}")

try:
    cursor.execute(
        "INSERT IGNORE INTO classes (class_code, class_name, lecturer_id, schedule, room) VALUES (%s, %s, %s, %s, %s)",
        ("CS101", "Nhap mon Lap trinh", 1, "Thu 2 - Thu 4, 7:30 - 9:00", "A101")
    )
    cursor.execute(
        "INSERT IGNORE INTO classes (class_code, class_name, lecturer_id, schedule, room) VALUES (%s, %s, %s, %s, %s)",
        ("IT202", "Co so du lieu", 1, "Thu 3 - Thu 5, 9:30 - 11:00", "B205")
    )
except Exception as e:
    print(f"  Note: {e}")

conn.commit()
print("✅ 3. Sample data inserted")
print()
print("🎉 Database setup complete!")
print("   Account: admin / admin123")
conn.close()
