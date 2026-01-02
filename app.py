from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib

app = Flask(__name__)
app.secret_key = "tigerpatrol123"

# ---------------- Database ----------------
DATABASE = os.path.join(os.path.dirname(__file__), "tiger_patrol.db")

def get_db():
    return sqlite3.connect(DATABASE)

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Rides table
    c.execute('''
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
    ''')

    # Officers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- Email ----------------
def send_email(to_email, subject, body):
    EMAIL_ADDRESS = "yourappemail@gmail.com"   # Replace with your app email
    EMAIL_PASSWORD = "yourapppassword"         # Replace with your app password

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Email failed: {e}")

# ---------------- Routes ----------------

# Student Ride Request
@app.route("/", methods=["GET", "POST"])
def tiger_patrol_request():
    if request.method == "POST":
        name = request.form['name']
        student_id = request.form['student_id']
        pickup = request.form['pickup']
        dropoff = request.form['dropoff']
        date = request.form['date']
        time_val = request.form['time']
        phone = request.form['phone']
        reason = request.form.get('reason', 'Not provided')
        email = request.form['email']

        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO rides (name, student_id, pickup, dropoff, date, time, phone, reason, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, student_id, pickup, dropoff, date, time_val, phone, reason, email))
        conn.commit()
        conn.close()

        # Email confirmation
        subject = "Tiger Patrol Ride Request Submitted"
        body = f"""
Hi {name},

Your ride request has been submitted successfully!

Pick-up: {pickup}
Drop-off: {dropoff}
Date: {date}
Time: {time_val}

- Campus Safety Team
"""
        send_email(email, subject, body)
        flash("Your ride request has been submitted successfully!", "success")
        return redirect(url_for("tiger_patrol_request"))

    return render_template("tiger_patrol.html")

# ---------------- Officer Auth ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        hashed = generate_password_hash(password)

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO officers (username, password) VALUES (?,?)", (username, hashed))
            conn.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Try a different one.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT password FROM officers WHERE username=?", (username,))
        record = c.fetchone()
        conn.close()

        if record and check_password_hash(record[0], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for("officer_dashboard"))
        else:
            error_message = "Invalid credentials. Please try again."

    return render_template("login.html", error=error_message)

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# ---------------- Officer Dashboard ----------------
@app.route("/officer")
def officer_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    conn.close()
    return render_template("officer_dashboard.html", rides=rides)

@app.route("/update/<int:ride_id>/<status>")
def update_ride(ride_id, status):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE rides SET status=? WHERE id=?", (status, ride_id))
    c.execute("SELECT name, email FROM rides WHERE id=?", (ride_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()

    # Notify student via email
    if student:
        send_email(student[1], f"Ride Status Updated: {status}",
                   f"Hi {student[0]},\n\nYour ride request status has been updated to: {status}.\n\n- Campus Safety Team")

    flash("Ride status updated successfully!", "success")
    return redirect(url_for("officer_dashboard"))

# ---------------- Admin ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()

        if admin:
            session['admin'] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin login", "danger")

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", rides=rides)

# ---------------- Run App ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
