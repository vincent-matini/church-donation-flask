from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Admin login required")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------
# DATABASE
# -----------------------
def get_db_connection():
    conn = sqlite3.connect("donations.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------
# ADMIN CREDENTIALS
# -----------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

# -----------------------
# PUBLIC ROUTES
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        name = request.form.get("name")
        donation_type = request.form.get("donation_type")
        amount = request.form.get("amount")

        conn = sqlite3.connect("donations.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO donations (name, donation_type, amount) VALUES (?, ?, ?)",
            (name, donation_type, amount)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("donations"))

    return render_template("donate.html")


@app.route("/donations")
def donations():
    conn = sqlite3.connect("donations.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM donations")
    data = cursor.fetchall()
    conn.close()

    return render_template("donations.html", donations=data)


# -----------------------
# ADMIN AUTH
# -----------------------
@app.route("/admin/login", methods=["GET", "POST"])
@admin_required
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["user"] = {
                "username": ADMIN_USERNAME,
                "role": "admin"
            }
            return redirect(url_for("admin_dashboard"))

        return "Invalid credentials", 401

    return render_template("admin_login.html")

@app.route("/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    if not session.get("user") or session["user"]["role"] != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    donations = conn.execute(
        "SELECT id, name, amount, date FROM donations ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", donations=donations)

@app.route("/admin/delete/<int:donation_id>", methods=["POST"])
@admin_required
def delete_donation(donation_id):
    if not session.get("user") or session["user"]["role"] != "admin":
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM donations WHERE id = ?", (donation_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("user", None)
    return redirect(url_for("admin_login"))


# -----------------------
# RENDER PORT BINDING
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
 