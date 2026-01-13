from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

# -----------------------
# DATABASE SETUP
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
# PUBLIC ROUTES
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/donate", methods=["GET", "POST"])
def donate():
    if request.method == "POST":
        name = request.form["name"]
        amount = request.form["amount"]
        date = request.form["date"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO donations (name, amount, date) VALUES (?, ?, ?)",
            (name, amount, date)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("donations"))

    return render_template("donate.html")

@app.route("/donations")
def donations():
    conn = get_db_connection()
    donations = conn.execute(
        "SELECT name, amount, date FROM donations ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("donations.html", donations=donations)

# -----------------------
# ADMIN AUTH
# -----------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # TEMP credentials (will secure later)
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid credentials", 401

    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    donations = conn.execute(
        "SELECT name, amount, date FROM donations ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin_dashboard.html", donations=donations)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# -----------------------
# RENDER / PORT SUPPORT
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
