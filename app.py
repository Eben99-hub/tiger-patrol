from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from email.message import EmailMessage
import smtplib

app = Flask(__name__)
app.secret_key = 'tigerpatrol123'

DATABASE = 'tiger_patrol.db'

# ---------------- Database Setup ----------------
def ensure_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create rides table
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
            email TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Create officers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Create admin table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

ensure_db()

# ---------------- Email Function ----------------
def send_email(to_email, subject, body):
    EMAIL_ADDRESS = 'yourappemail@gmail.com'  # Replace with your app email
    EMAIL_PASSWORD = 'yourapppassword'        # Replace with your app password

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
        print(f"Failed to send email: {e}")

# ---------------- Routes ----------------

# ---------- STUDENT ----------
@app.route("/", methods=["GET", "POST"])
def tiger_patrol_request():
    if request.method == "POST":
        name = request.form['name']
        student_id = request.form['student_id']
        pickup = request.form['pickup']
        dropoff = request.form['dropoff']
        date = request.form['date']
        time = request.form['time']
        phone = request.form['phone']
        reason = request.form.get('reason', 'Not provided')
        email = request.form['email']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO rides (name, student_id, pickup, dropoff, date, time, phone, reason, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, student_id, pickup, dropoff, date, time, phone, reason, email))
        conn.commit()
        conn.close()

        # Send confirmation email
        subject = "Tiger Patrol Ride Request Submitted"
        body = f"""
Hi {name},

Your ride request has been submitted successfully!

Pick-up: {pickup}
Drop-off: {dropoff}
Date: {date}
Time: {time}

- Campus Safety Team
"""
        send_email(email, subject, body)
        flash("Your ride request was submitted successfully!")
        return redirect(url_for("tiger_patrol_request"))

    return render_template("tiger_patrol.html")


# ---------- OFFICER AUTH ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO officers (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            flash("Account created successfully! Please login.")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Username already exists. Try a different one.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT password FROM officers WHERE username=?', (username,))
        record = c.fetchone()
        conn.close()

        if record and check_password_hash(record[0], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('officer_dashboard'))
        else:
            error_message = "Invalid credentials. Try again."

    return render_template('login.html', error=error_message)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash("Logged out successfully.")
    return redirect(url_for('login'))


# ---------- OFFICER DASHBOARD ----------
@app.route("/officer")
def officer_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    conn.close()
    return render_template("officer_dashboard.html", rides=rides)


@app.route("/update/<int:ride_id>/<status>")
def update_ride(ride_id, status):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE rides SET status=? WHERE id=?', (status, ride_id))
    c.execute('SELECT name, email FROM rides WHERE id=?', (ride_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()

    if student:
        student_name = student[0]
        student_email = student[1]
        subject = f"Your Tiger Patrol Ride Status: {status}"
        body = f"Hi {student_name},\n\nYour ride request status has been updated to: {status}.\n\n- Campus Safety Team"
        send_email(student_email, subject, body)

    flash(f"Ride {ride_id} status updated to {status}")
    return redirect(url_for('officer_dashboard'))


# ---------- ADMIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()

        if admin:
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin login")

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    conn.close()
    return render_template("admin_dashboard.html", rides=rides)


if __name__ == "__main__":
    app.run(debug=True)
