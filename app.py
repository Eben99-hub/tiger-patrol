from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tigerpatrol123'

# ---------------- Database Setup ----------------
def ensure_columns():
    conn = sqlite3.connect('tiger_patrol.db')
    c = conn.cursor()

    # Create rides table if not exists
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
            reason TEXT
        )
    ''')

    # Get existing columns
    c.execute("PRAGMA table_info(rides)")
    existing_columns = [col[1] for col in c.fetchall()]

    # Add missing columns
    if 'status' not in existing_columns:
        c.execute("ALTER TABLE rides ADD COLUMN status TEXT DEFAULT 'Pending'")
    if 'email' not in existing_columns:
        c.execute("ALTER TABLE rides ADD COLUMN email TEXT")

    # Create officers table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Call at startup
ensure_columns()

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

# Student Ride Request
@app.route('/', methods=['GET', 'POST'])
def tiger_patrol_request():
    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        pickup = request.form['pickup']
        dropoff = request.form['dropoff']
        date = request.form['date']
        time = request.form['time']
        phone = request.form['phone']
        reason = request.form.get('reason', 'Not provided')
        email = request.form['email']

        conn = sqlite3.connect('tiger_patrol.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO rides (name, student_id, pickup, dropoff, date, time, phone, reason, status, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, student_id, pickup, dropoff, date, time, phone, reason, 'Pending', email))
        conn.commit()
        conn.close()

        # Send email confirmation
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
        send_email(to_email=email, subject=subject, body=body)
        return redirect(url_for('confirmation'))
    return render_template('tiger_patrol.html')

@app.route('/confirmation')
def confirmation():
    return "<h2>🐯 Your Tiger Patrol ride request has been submitted successfully.</h2>"

# Officer Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('tiger_patrol.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO officers (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return "<h3>Account created successfully! <a href='/login'>Login here</a></h3>"
        except sqlite3.IntegrityError:
            conn.close()
            return "<h3>Username already exists. Try a different one.</h3>"

    return render_template('signup.html')

# Officer Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('tiger_patrol.db')
        c = conn.cursor()
        c.execute('SELECT password FROM officers WHERE username=?', (username,))
        record = c.fetchone()
        conn.close()

        if record and check_password_hash(record[0], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('view_rides'))
        else:
            error_message = "Invalid credentials. Please try again."

    return render_template('login.html', error=error_message)

# Officer Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return "<h3>Logged out successfully. <a href='/login'>Login again</a></h3>"

# Officer Dashboard
@app.route('/rides')
def view_rides():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('tiger_patrol.db')
    c = conn.cursor()
    c.execute('SELECT * FROM rides')
    all_rides = c.fetchall()
    conn.close()
    return render_template('rides.html', rides=all_rides)

# Update ride status
@app.route('/update/<int:ride_id>/<status>')
def update_ride(ride_id, status):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('tiger_patrol.db')
    c = conn.cursor()
    c.execute('UPDATE rides SET status=? WHERE id=?', (status, ride_id))
    c.execute('SELECT name, email FROM rides WHERE id=?', (ride_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()

    # Email notification
    if student:
        student_name = student[0]
        student_email = student[1]
        subject = f"Your Tiger Patrol Ride Status: {status}"
        body = f"Hi {student_name},\n\nYour ride request status has been updated to: {status}.\n\n- Campus Safety Team"
        send_email(to_email=student_email, subject=subject, body=body)

    return redirect(url_for('view_rides'))

if __name__ == '__main__':
    app.run(debug=True)
