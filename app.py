from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "tigerpatrol123"

DATABASE = "tiger_patrol.db"

# ---------------- Database Setup ----------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Rides table
    c.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            student_id TEXT,
            pickup TEXT,
            dropoff TEXT,
            date TEXT,
            time TEXT,
            phone TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            email TEXT
        )
    """)

    # Officers table
    c.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Admin table
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- Email Placeholder ----------------
def send_email(to_email, subject, body):
    # Placeholder: replace with real credentials if needed
    print(f"[EMAIL] To: {to_email} | Subject: {subject} | Body:\n{body}\n")
    # Uncomment below for real email sending
    """
    EMAIL_ADDRESS = "yourappemail@gmail.com"
    EMAIL_PASSWORD = "yourapppassword"
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    """

# ---------------- Routes ----------------

# Student Ride Request
@app.route("/", methods=["GET", "POST"])
def tiger_patrol_request():
    if request.method == "POST":
        name = request.form["name"]
        student_id = request.form["student_id"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        date = request.form["date"]
        time_ = request.form["time"]
        phone = request.form["phone"]
        reason = request.form.get("reason", "Not provided")
        email = request.form["email"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO rides (name, student_id, pickup, dropoff, date, time, phone, reason, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, student_id, pickup, dropoff, date, time_, phone, reason, email))
        conn.commit()
        conn.close()

        # Flash confirmation
        flash("🐯 Your ride request has been submitted successfully!", "success")

        # Email notification placeholder
        subject = "Tiger Patrol Ride Request Submitted"
        body = f"""
Hi {name},

Your ride request has been submitted successfully!

Pick-up: {pickup}
Drop-off: {dropoff}
Date: {date}
Time: {time_}

- Campus Safety Team
"""
        send_email(email, subject, body)

        return redirect(url_for("tiger_patrol_request"))

    return render_template("tiger_patrol.html")

# ---------------- Officer Signup ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO officers (username, password) VALUES (?, ?)", (username, hashed))
            conn.commit()
            flash("✅ Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("⚠️ Username already exists. Try a different one.", "danger")
        finally:
            conn.close()

    return render_template("signup.html")

# ---------------- Officer Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT password FROM officers WHERE username=?", (username,))
        record = c.fetchone()
        conn.close()

        if record and check_password_hash(record[0], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("officer_dashboard"))
        else:
            error_message = "⚠️ Invalid credentials. Please try again."

    return render_template("login.html", error=error_message)

# ---------------- Officer Logout ----------------
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ---------------- Officer Dashboard ----------------
@app.route("/officer")
def officer_dashboard():
    if not session.get("logged_in"):
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    conn.close()

    return render_template("officer_dashboard.html", rides=rides)

# ---------------- Update Ride Status ----------------
@app.route("/update/<int:ride_id>/<status>")
def update_ride(ride_id, status):
    if not session.get("logged_in"):
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE rides SET status=? WHERE id=?", (status, ride_id))
    c.execute("SELECT name, email FROM rides WHERE id=?", (ride_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()

    if student:
        student_name, student_email = student
        subject = f"Your Tiger Patrol Ride Status: {status}"
        body = f"Hi {student_name},\n\nYour ride request status has been updated to: {status}.\n\n- Campus Safety Team"
        send_email(student_email, subject, body)

    flash(f"Ride status updated to '{status}'.", "success")
    return redirect(url_for("officer_dashboard"))

# ---------------- Admin Login ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (user, pw))
        admin = c.fetchone()
        conn.close()

        if admin:
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin login.", "danger")

    return render_template("a_
