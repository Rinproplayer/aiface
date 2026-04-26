"""Script cap nhat password admin"""
import mysql.connector
from auth import hash_password

conn = mysql.connector.connect(host="localhost", user="root", password="", database="aiface_db")
cursor = conn.cursor()

new_hash = hash_password("admin123")
cursor.execute("UPDATE lecturers SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
print(f"Updated admin password hash: {new_hash}")
print("Account: admin / admin123")
conn.close()
