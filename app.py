import sqlite3
import random
import smtplib

from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "super_secret_key_123"
app.permanent_session_lifetime = timedelta(days=7)

# EMAIL (simple version)
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"


# 🗄️ DATABASE
def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:

        # 👤 USERS TABLE (UPGRADED)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            xp INTEGER DEFAULT 0
        )
        """)
# OTP
def send_otp_email(to_email, otp):
    try:
        msg = MIMEText(f"Your OTP is {otp}")
        msg["Subject"] = "OTP"
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
    except:
        print("Email error")


# HOME
@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return render_template("home.html")


# SIGNUP
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        otp = str(random.randint(100000, 999999))

        session["otp"] = otp
        session["temp_user"] = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password)
        }

        send_otp_email(email, otp)
        return redirect("/verify")

    return render_template("signup.html")


# VERIFY
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        if request.form["otp"] == session.get("otp"):
            u = session["temp_user"]

            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (name,email,password) VALUES (?,?,?)",
                    (u["name"], u["email"], u["password"])
                )

            session.pop("otp", None)
            session.pop("temp_user", None)

            return redirect("/login")

        flash("Wrong OTP")

    return render_template("verify.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

     user = conn.execute(
    "SELECT * FROM users WHERE email=?",
    (email,)
       ).fetchone()

        if user and check_password_hash(user["password"], password):
            session["user"] = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
            return redirect("/dashboard")

        flash("Invalid login")

    return render_template("login.html")

@app.route("/users")
def users():
    with get_db() as conn:
        all_users = conn.execute(
            "SELECT id, name, email, xp FROM users"
        ).fetchall()

    return render_template("users.html", users=all_users)
    
# DASHBOARD (COURSES)
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html", user=session["user"])


# LESSON ROUTES
@app.route("/html")
def html():
    return render_template("html.html")

@app.route("/python")
def python():
    return render_template("python.html")

@app.route("/js")
def js():
    return render_template("js.html")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)