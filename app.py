from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import uuid
import os
import io
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

# 1. HOME PAGE: First entry point for your application
@app.route('/')
def home():
    return render_template("home.html")

# 2. REGISTER PAGE: Create an account
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        if not username or not password:
            return "Username and Password cannot be empty!"
            
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        existing = c.fetchone()
        
        if existing:
            conn.close()
            return "User already exists! Please try another name or <a href='/login'>Login here</a>."
            
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template("register.html")

# 3. LOGIN PAGE: Verify the user credentials
@app.route('/login', methods=['GET', 'POST'])
def login():
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
            return "Invalid Credentials! <a href='/login'>Try Again</a> or <a href='/register'>Register Here</a>."
    return render_template("login.html")

# 4. BOOKING PAGE: Book a ticket (Multi-booking allowed!)
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

# 5. DOWNLOAD PAGE: Keep PDF processing strictly in-memory
@app.route('/download/<ticket_id>')
def download(ticket_id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE ticket_id=? AND username=?", (ticket_id, session['user']))
    data = c.fetchone()
    conn.close()
    
    if not data:
        return "Ticket not found or unauthorized access", 403
        
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    
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
    
    buffer.seek(0)
    return send_file(
        buffer, 
        as_attachment=True, 
        download_name=f"ticket_{ticket_id}.pdf", 
        mimetype="application/pdf"
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
