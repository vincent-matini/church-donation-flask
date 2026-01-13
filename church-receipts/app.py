from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DB_PATH = "donations.db"

ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get("ADMIN_PASS", "admin123")
)

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- AUTH ----------
def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrap

# ---------- PUBLIC ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        name = request.form.get("name")
        dtype = request.form.get("type")
        amount = request.form.get("amount")

        if not amount:
            flash("Amount is required")
            return redirect(url_for("donate"))

        conn = get_db()
        conn.execute(
            "INSERT INTO donations (name, type, amount, date) VALUES (?, ?, ?, ?)",
            (name, dtype, amount, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

        flash("Donation saved successfully")
        return redirect(url_for("donate"))

    return render_template("donations.html")

# ---------- ADMIN ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME
            and check_password_hash(
                ADMIN_PASSWORD_HASH, request.form.get("password")
            )
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid credentials")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()
    donations = conn.execute(
        "SELECT id, name, type, amount, date FROM donations ORDER BY date DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", donations=donations)

@app.route("/admin/delete/<int:id>", methods=["POST"])
@admin_required
def delete_donation(id):
    conn = get_db()
    conn.execute("DELETE FROM donations WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Donation deleted")
    return redirect(url_for("admin_dashboard"))
