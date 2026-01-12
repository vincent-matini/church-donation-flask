import sqlite3
import csv
from flask import Flask, render_template, request, redirect, url_for, Response

app = Flask(__name__)
DB_NAME = "donations.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            donation_type TEXT,
            amount REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        donation_type = request.form.get("type")
        amount = request.form.get("amount")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO donations (name, donation_type, amount) VALUES (?, ?, ?)",
            (name, donation_type, amount)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("donations"))

    return render_template("index.html")


@app.route("/donations")
def donations():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, donation_type, amount, date FROM donations ORDER BY date DESC"
    )
    records = cursor.fetchall()
    conn.close()

    return render_template("donations.html", records=records)


@app.route("/export")
def export():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, donation_type, amount, date FROM donations")
    records = cursor.fetchall()
    conn.close()

    def generate():
        yield "Name,Type,Amount,Date\n"
        for r in records:
            name = r[0] if r[0] else "Anonymous"
            yield f"{name},{r[1]},{r[2]},{r[3]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=donations.csv"}
    )


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


