from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add", methods=["POST"])
def add():

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=? OR phone=?",
        (email, phone)
    )

    existing = cursor.fetchone()

    if existing:
        conn.close()

        return render_template(
            "duplicate.html",
            email=email
        )

    cursor.execute(
        "INSERT INTO users(name,email,phone) VALUES(?,?,?)",
        (name, email, phone)
    )

    conn.commit()

    record_id = cursor.lastrowid

    conn.close()

    return render_template(
        "success.html",
        name=name,
        email=email,
        phone=phone,
        record_id=f"RID-2026-{record_id:03d}",
        date=datetime.now().strftime("%d %b %Y %I:%M %p")
    )

if __name__ == "__main__":
    app.run(debug=True)