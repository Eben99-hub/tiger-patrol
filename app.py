from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "tigerpatrol_secret"

DB_NAME = "tiger_patrol.db"

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect(DB_NAME)

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

    db.commit()
    db.close()

init_db()

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

        flash("Ride request submitted!")
        return redirect(url_for("tiger_patrol_request"))

    return render_template("tiger_patrol.html")

# ---------- OFFICER AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        c = db.cursor()
        c.execute("SELECT password FROM officers WHERE username=?", (username,))
        record = c.fetchone()
        db.close()

        if record and check_password_hash(record[0], password):
            session["officer"] = username
            return redirect(url_for("officer_dashboard"))
        else:
            error = "Invalid login. Try again."

    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            db = get_db()
            c = db.cursor()
            c.execute("INSERT INTO officers (username, password) VALUES (?, ?)",
                      (username, password))
            db.commit()
            db.close()
            flash("Account created. Please login.")
            return redirect(url_for("login"))
        except:
            flash("Username already exists")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- OFFICER DASHBOARD ----------
@app.route("/officer")
def officer_dashboard():
    if "officer" not in session:
        return redirect(url_for("login"))

    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM rides")
    rides = c.fetchall()
    db.close()

    return render_template("officer_dashboard.html", rides=rides)

@app.route("/update/<int:ride_id>/<status>")
def update_ride(ride_id, status):
    if "officer" not in session:
        return redirect(url_for("login"))

    db = get_db()
    c = db.cursor()
    c.execute("UPDATE rides SET status=? WHERE id=?", (status, ride_id))
    db.commit()
    db.close()

    return redirect(url_for("officer_dashboard"))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run()
