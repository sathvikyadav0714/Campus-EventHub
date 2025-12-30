from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import uuid
from utils.certificate import generate_certificate
import os




app = Flask(__name__)
app.secret_key = "campus_eventhub_secret"
DB_NAME = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()


    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll_no TEXT UNIQUE,
            email TEXT UNIQUE,
            department TEXT,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            department TEXT,
            date TEXT,
            venue TEXT,
            is_paid INTEGER,
            fee INTEGER,
            status TEXT DEFAULT 'upcoming'
        )
    """)


    cur.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event_id INTEGER,
            payment_status TEXT,
            payment_method TEXT,
            transaction_id TEXT,
            UNIQUE(student_id, event_id)
        )
    """)



    conn.commit()
    conn.close()

def create_admin():
    conn = get_db_connection()
    cur = conn.cursor()

    hashed_password = generate_password_hash("admin123")

    try:
        cur.execute("""
            INSERT INTO admins (username, password)
            VALUES (?, ?)
        """, ("admin", hashed_password))

        conn.commit()
    except sqlite3.IntegrityError:
        pass  # admin already exists

    conn.close()

def migrate_registrations_table():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE registrations ADD COLUMN payment_method TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    try:
        cur.execute("ALTER TABLE registrations ADD COLUMN transaction_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()

def migrate_events_status():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE events ADD COLUMN status TEXT DEFAULT 'upcoming'")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.commit()
    conn.close()





# ✅ HOME ROUTE (THIS IS "/" ROUTE)
@app.route("/")
def home():
    return "Campus EventHub – Database connected!"


# ✅ ADD THIS ROUTE **HERE**
@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        name = request.form["name"]
        roll_no = request.form["roll_no"]
        email = request.form["email"]
        department = request.form["department"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO students (name, roll_no, email, department, password)
                VALUES (?, ?, ?, ?, ?)
            """, (name, roll_no, email, department, hashed_password))

            conn.commit()
            conn.close()

            return "Student registered successfully!"

        except sqlite3.IntegrityError:
            return "Roll number or Email already exists!"

    return render_template("student/register.html")


# Student login route
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM students WHERE email = ?", (email,))
        student = cur.fetchone()
        conn.close()

        if student and check_password_hash(student["password"], password):
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            return redirect(url_for("student_dashboard"))
        else:
            return "Invalid email or password!"

    return render_template("student/login.html")


# Student dashboard route
@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    return render_template("student/dashboard.html")


# Student events route
@app.route("/student/events")
def student_events():
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # fetch student department
    cur.execute("SELECT department FROM students WHERE id = ?", (session["student_id"],))
    student = cur.fetchone()

    cur.execute("""
        SELECT * FROM events
        WHERE department = ? OR department = 'ALL'
    """, (student["department"],))

    events = cur.fetchall()
    conn.close()

    return render_template("student/events.html", events=events)


# Student event registration route
@app.route("/student/register-event/<int:event_id>")
def register_event(event_id):
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()

    if not event:
        conn.close()
        return "Event not found!"

    # ✅ FREE EVENT
    if event["is_paid"] == 0:
        try:
            cur.execute("""
                INSERT INTO registrations (student_id, event_id, payment_status)
                VALUES (?, ?, ?)
            """, (session["student_id"], event_id, "free"))

            conn.commit()
            conn.close()
            return "Successfully registered for the free event!"

        except sqlite3.IntegrityError:
            conn.close()
            return "You have already registered for this event."

    # 💳 PAID EVENT
    else:
        conn.close()
        return redirect(url_for("pay_for_event", event_id=event_id))


# Student payment route for paid events
@app.route("/student/pay/<int:event_id>", methods=["GET", "POST"])
def pay_for_event(event_id):
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()

    if not event:
        conn.close()
        return "Event not found!"

    if request.method == "POST":
        method = request.form["method"]
        transaction_id = "TXN_" + uuid.uuid4().hex[:10].upper()

        try:
            cur.execute("""
                INSERT INTO registrations 
                (student_id, event_id, payment_status, payment_method, transaction_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["student_id"],
                event_id,
                "paid",
                method,
                transaction_id
            ))

            conn.commit()
            conn.close()
            return f"Payment successful! Transaction ID: {transaction_id}"

        except sqlite3.IntegrityError:
            conn.close()
            return "You have already registered for this event."

    conn.close()
    return render_template("student/mock_payment.html", event=event)

    

# Student my events route
@app.route("/student/my-events")
def my_events():
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.*
        FROM events e
        JOIN registrations r ON e.id = r.event_id
        WHERE r.student_id = ?
    """, (session["student_id"],))

    events = cur.fetchall()
    conn.close()

    return render_template("student/my_events.html", events=events)



# Student certificates route
@app.route("/student/certificates")
def student_certificates():
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.title, r.event_id
        FROM events e
        JOIN registrations r ON e.id = r.event_id
        WHERE r.student_id = ? AND e.status = 'completed'
    """, (session["student_id"],))

    rows = cur.fetchall()
    conn.close()

    certificates = []
    for row in rows:
        filename = f"certificate_event{row['event_id']}_student{session['student_id']}.pdf"
        certificates.append({
            "title": row["title"],
            "filename": filename
        })

    return render_template("student/certificates.html", certificates=certificates)






# Student logout route
@app.route("/student/logout")
def student_logout():
    session.clear()
    return redirect(url_for("student_login"))


# Admin login route
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = cur.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid admin credentials!"

    return render_template("admin/login.html")



# Admin dashboard route
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    return render_template("admin/dashboard.html")

# Admin logout route
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


#✅ create event route
@app.route("/admin/create-event", methods=["GET", "POST"])
def create_event():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        department = request.form["department"]
        date = request.form["date"]
        venue = request.form["venue"]
        is_paid = 1 if request.form["is_paid"] == "yes" else 0
        fee = request.form["fee"] if is_paid else 0

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO events (title, description, department, date, venue, is_paid, fee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (title, description, department, date, venue, is_paid, fee))

        conn.commit()
        conn.close()

        return "Event created successfully!"

    return render_template("admin/create_event.html")


#✅ admin events management route
@app.route("/admin/events")
def admin_events():
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    conn.close()

    return render_template("admin/events.html", events=events)



#✅ admin complete event route
@app.route("/admin/complete-event/<int:event_id>")
def complete_event(event_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE events
        SET status = 'completed'
        WHERE id = ?
    """, (event_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin_events"))




#✅ admin delete event route
@app.route("/admin/delete-event/<int:event_id>")
def delete_event(event_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_events"))




#✅ admin edit event route
@app.route("/admin/edit-event/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            UPDATE events
            SET title = ?, description = ?, department = ?, date = ?, venue = ?, fee = ?
            WHERE id = ?
        """, (
            request.form["title"],
            request.form["description"],
            request.form["department"],
            request.form["date"],
            request.form["venue"],
            request.form["fee"],
            event_id
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("admin_events"))

    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()
    conn.close()

    return render_template("admin/edit_event.html", event=event)





#✅ admin generate certificates route
@app.route("/admin/generate-certificates/<int:event_id>")
def generate_certificates(event_id):
    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # get event
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cur.fetchone()

    if event["status"] != "completed":
        conn.close()
        return "Event is not completed yet!"

    # get registered students
    cur.execute("""
        SELECT s.name, s.id
        FROM students s
        JOIN registrations r ON s.id = r.student_id
        WHERE r.event_id = ?
    """, (event_id,))

    students = cur.fetchall()

    os.makedirs("static/certificates", exist_ok=True)

    for student in students:
        filename = f"certificate_event{event_id}_student{student['id']}.pdf"
        path = os.path.join("static/certificates", filename)

        generate_certificate(
            student_name=student["name"],
            event_title=event["title"],
            output_path=path
        )

    conn.close()
    return "Certificates generated successfully!"






# ⚠️ KEEP THIS ALWAYS AT THE END
if __name__ == "__main__":
    app.run(debug=True)




