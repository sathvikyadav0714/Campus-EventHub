import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
cur = conn.cursor()

new_password = generate_password_hash("admin123")

cur.execute("UPDATE admins SET password = ?", (new_password,))
conn.commit()

print("Admin password reset to: admin123")


new_password = generate_password_hash("1234")
cur.execute("UPDATE students SET password = ?", (new_password,))


conn.close()