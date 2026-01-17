from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os
from datetime import datetime

# --------------------------------------------------
# APP CONFIG
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "donations.db")

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

with app.app_context():
    init_db()

# --------------------------------------------------
# ADMIN CONFIG
# --------------------------------------------------
ADMIN_USERNAME = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(
    os.environ.get("ADMIN_PASS", "admin123")
)

# --------------------------------------------------
# AUTH DECORATOR
# --------------------------------------------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

# --------------------------------------------------
# PUBLIC ROUTES
# --------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")
    

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            dtype = request.form.get("type", "").strip()
            amount = float(request.form.get("amount", 0))

            if amount <= 0:
                flash("Invalid donation amount", "error")
                return redirect(url_for("donate"))

            conn = get_db()
            conn.execute(
                "INSERT INTO donations (name, type, amount, date) VALUES (?, ?, ?, ?)",
                (name, dtype, amount, datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()

            flash("Thank you for your donation 🙏", "success")
            return redirect(url_for("thank_you"))

        except Exception as e:
            print("DONATE ERROR:", e)
            flash("Unable to process donation", "error")
            return redirect(url_for("donate"))

    return render_template("donate.html")

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")

# --------------------------------------------------
# ADMIN AUTH
# --------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password", "error")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("admin_login"))

# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()
    donations = conn.execute(
        """
        SELECT id, name, type, amount, date
        FROM donations
        ORDER BY date DESC
        """
    ).fetchall()
    conn.close()

    # DEBUG SAFETY: ensure donations is always iterable
    if donations is None:
        donations = []

    return render_template(
        "admin_dashboard.html",
        donations=donations
    )


@app.route("/admin/delete/<int:donation_id>", methods=["POST"])
@admin_required
def delete_donation(donation_id):
    conn = get_db()
    conn.execute("DELETE FROM donations WHERE id = ?", (donation_id,))
    conn.commit()
    conn.close()

    flash("Donation deleted", "success")
    return redirect(url_for("admin_dashboard"))

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}
