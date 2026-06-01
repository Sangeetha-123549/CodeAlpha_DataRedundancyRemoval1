from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import uuid
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "buspass_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        source TEXT,
        destination TEXT,
        tickets INTEGER,
        price INTEGER,
        ticket_id TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    session.pop('user', None)
    return render_template("register.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        existing = c.fetchone()
        if existing:
            conn.close()
            return "User already exists"
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.pop('user', None)
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = username
            return redirect(url_for('book'))
        else:
            return "Invalid Credentials"
    return render_template("login.html")

@app.route('/book', methods=['GET', 'POST'])
def book():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        tickets = int(request.form['tickets'])
        price = tickets * 50
        ticket_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO bookings 
        (username, source, destination, tickets, price, ticket_id)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (session['user'], source, destination, tickets, price, ticket_id))
        conn.commit()
        conn.close()
        return render_template("success.html", ticket_id=ticket_id, price=price)
    return render_template("book.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/download/<ticket_id>')
def download(ticket_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE ticket_id=?", (ticket_id,))
    data = c.fetchone()
    conn.close()
    if not data:
        return "Ticket not found"
    file_path = os.path.join(BASE_DIR, f"{ticket_id}.pdf")
    pdf = canvas.Canvas(file_path)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(180, 750, "BUS PASS TICKET")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 700, f"Ticket ID: {data[6]}")
    pdf.drawString(100, 680, f"User: {data[1]}")
    pdf.drawString(100, 660, f"Source: {data[2]}")
    pdf.drawString(100, 640, f"Destination: {data[3]}")
    pdf.drawString(100, 620, f"Tickets: {data[4]}")
    pdf.drawString(100, 600, f"Price: ₹{data[5]}")
    pdf.save()
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
