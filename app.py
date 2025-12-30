from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        pickup TEXT,
        dropoff TEXT,
        time TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS officers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    db.commit()
    db.close()

init_db()

# ---------- EMAIL ----------
def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = "tigerpatrol.demo@gmail.com"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("tigerpatrol.demo@gmail.com", "APP_PASSWORD_HERE")
            server.send_message(msg)
    except:
        print("Email failed (demo mode)")

# ---------- STUDENT ----------
@app.route("/", methods=["GET", "POST"])
def tiger_patrol_request():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        pickup = request.form["pickup"]
        dropoff = request.form["dropoff"]
        time = request.form["time"]

        db = get_db()
        c = db.cursor()
        c.execute("""
        INSERT INTO rides (name, email, pickup, dropoff, time)
        VALUES (?, ?, ?, ?, ?)
        """, (name, email, pickup, dropoff, time))
        db.commit()
        db.close()

        send_email(email, "Tiger Patrol Request Received",
                   "Your ride request has been received.")

        flash("Request submitted successfully!")
        return redirect(url_for("tiger_patrol_request"))

    return render_template("tiger_patrol.html")

# ---------- OFFICER AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM officers WHERE username=? AND password=?",
                  (username, password))
        officer = c.fetchone()
        db.close()

        if officer:
            return redirect(url_for("officer_dashboard"))
        else:
            flash("Invalid login. Try again.")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            db = get_db()
            c = db.cursor()
            c.execute("INSERT INTO officers (username, password) VALUES (?,?)",
                      (username, password))
            db.commit()
            db.close()
            flash("Account created. Please login.")
            return redirect(url_for("login"))
        except:
            flash("Username already exists")

    return render_template("register.html")

# ---------- OFFICER DASHBOARD ----------
@app.route("/officer")
def officer_dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    db.close()
    return render_template("officer_dashboard.html", rides=rides)

@app.route("/update/<int:ride_id>/<status>")
def update_ride(ride_id, status):
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE rides SET status=? WHERE id=?", (status, ride_id))
    db.commit()
    db.close()
    return redirect(url_for("officer_dashboard"))

# ---------- ADMIN ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

        db = get_db()
        c = db.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?", (user, pw))
        admin = c.fetchone()
        db.close()

        if admin:
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin login")

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    db.close()
    return render_template("admin_dashboard.html", rides=rides)

if __name__ == "__main__":
    app.run(debug=True)
