#!/usr/bin/env python3
"""
MoneyMom - Realistic BIF 10,000 Note Generator
Authorized Government Use Only - Burundi Movement
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import sqlite3
import datetime
import os
import secrets
import base64
import time
import random
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Database setup
def init_db():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id INTEGER PRIMARY KEY, user_id INTEGER, serial_number TEXT UNIQUE, image_blob TEXT, created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, ip TEXT, created TEXT)''')
    
    # Create admin user
    admin_pass = generate_password_hash("08800Mpc+_+")
    c.execute("SELECT * FROM users WHERE username=?", ("Mpc",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                  ("Mpc", admin_pass, "0.0.0.0", datetime.datetime.now().isoformat(), 1))
    
    conn.commit()
    conn.close()

def generate_serial():
    # Format: EJ + 7 digits + year
    digits = ''.join([str(random.randint(0,9)) for _ in range(7)])
    return f"EJ{digits}2023"

def create_front_image(serial):
    # Dimensions: ~1500x700 pixels (proportional to real note)
    width = 1500
    height = 700
    
    # Background color (light green/yellow from real note)
    bg_color = (245, 235, 190)
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        font_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Border
    draw.rectangle([(20, 20), (width-20, height-20)], outline=(80, 60, 30), width=2)
    
    # Top text: IBANKI YA REPUBLIKA Y'UBURUNDI
    draw.text((width//2 - 300, 50), "IBANKI YA REPUBLIKA Y'UBURUNDI", 
              fill=(0, 0, 0), font=font_large)
    
    # Left vertical serial number
    draw.text((60, 300), serial, fill=(100, 50, 20), font=font_medium)
    
    # Center: Large 10000
    draw.text((width//2 - 100, 250), "10000", fill=(0, 0, 0), font=font_huge)
    
    # Center text: AMAFARANGA CUMI
    draw.text((width//2 - 140, 330), "AMAFARANGA CUMI", fill=(0, 0, 0), font=font_medium)
    
    # Right: 10000
    draw.text((width - 180, 280), "10000", fill=(0, 0, 0), font=font_huge)
    
    # Bottom: IBIHUMBI CUMI
    draw.text((width//2 - 100, height - 80), "IBIHUMBI CUMI", fill=(0, 0, 0), font=font_medium)
    
    # Bottom horizontal serial number
    draw.text((width//2 - 150, height - 120), serial, fill=(100, 50, 20), font=font_small)
    
    # Decorative pattern - circles like real note
    for i in range(5):
        draw.ellipse([(50 + i*80, 550), (100 + i*80, 600)], outline=(180, 160, 100), width=1)
    
    # Security thread area (vertical stripe)
    draw.rectangle([(width//2 - 15, 100), (width//2 + 15, height-100)], fill=(200, 180, 120), outline=(100, 80, 40))
    
    return img

def create_back_image(serial):
    width = 1500
    height = 700
    
    bg_color = (245, 235, 190)
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_huge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_huge = ImageFont.load_default()
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Border
    draw.rectangle([(20, 20), (width-20, height-20)], outline=(80, 60, 30), width=2)
    
    # Top: BANQUE DE LA REPUBLIQUE DU BURUNDI
    draw.text((width//2 - 350, 40), "BANQUE DE LA REPUBLIQUE DU BURUNDI", 
              fill=(0, 0, 0), font=font_large)
    
    # Large 10000 center
    draw.text((width//2 - 120, 200), "10000", fill=(0, 0, 0), font=font_huge)
    
    # DIX MILLE FRANCS
    draw.text((width//2 - 180, 290), "DIX MILLE FRANCS", fill=(0, 0, 0), font=font_large)
    
    # LE GOUVERNEUR (left)
    draw.text((150, 450), "LE GOUVERNEUR", fill=(0, 0, 0), font=font_small)
    draw.line([(150, 480), (400, 480)], fill=(0, 0, 0), width=1)
    
    # LE VICE-GOUVERNEUR (right)
    draw.text((width - 400, 450), "LE VICE-GOUVERNEUR", fill=(0, 0, 0), font=font_small)
    draw.line([(width - 400, 480), (width - 150, 480)], fill=(0, 0, 0), width=1)
    
    # Bottom warning text
    draw.text((width//2 - 300, height - 80), "LE CONTREFACTEUR EST PUNI DE SERVITUDE PENALE", 
              fill=(100, 50, 20), font=font_tiny)
    
    # Date
    draw.text((width - 200, height - 50), "07-11-2022", fill=(80, 60, 30), font=font_tiny)
    
    # BRB Logo in center
    draw.text((width//2 - 30, height//2 + 50), "BRB", fill=(80, 60, 30), font=font_large)
    
    return img

def create_note_pair(serial):
    front = create_front_image(serial)
    back = create_back_image(serial)
    return front, back

# Logging function
def log_action(user_id, action, ip):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs (user_id, action, ip, created) VALUES (?, ?, ?, ?)",
              (user_id, action, ip, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# HTML Templates (same as before, simplified for length)
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom</title>
<style>
body{background:#0a0a0a;color:#0f0;font-family:monospace;text-align:center;padding:50px;}
input{background:#222;color:#0f0;border:1px solid #0f0;padding:10px;margin:10px;width:200px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
</style>
</head>
<body>
<h1>MONEYMOM</h1>
<h2>Premium Bills Supply - BIF 10,000</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Login</button>
</form>
<a href="/register" style="color:#0f0;">Register</a>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom - Register</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;text-align:center;padding:50px;}
input{background:#222;color:#0f0;border:1px solid #0f0;padding:10px;margin:10px;width:200px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}</style>
</head>
<body>
<h1>Register</h1>
<form method="POST">
<input type="text" name="username" placeholder="Username" required><br>
<input type="password" name="password" placeholder="Password" required><br>
<button type="submit">Create Account</button>
</form>
<a href="/login">Back to Login</a>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
{% if success %}<p style="color:#0f0;">{{ success }}</p>{% endif %}
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px;}
.note{border:1px solid #0f0;margin:20px 0;padding:10px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;}</style>
</head>
<body>
<h1>MoneyMom</h1>
<p>Welcome, {{ username }}</p>
<form method="POST" action="/generate"><button type="submit">Generate BIF 10,000 Note (Front & Back)</button></form>
<h2>Your Notes</h2>
{% for note in notes %}
<div class="note">
<p>Serial: {{ note.2 }}</p>
<p>Created: {{ note.4 }}</p>
<a href="/view_front/{{ note.0 }}">View Front</a> | 
<a href="/view_back/{{ note.0 }}">View Back</a> | 
<a href="/download/{{ note.0 }}">Download Both</a>
</div>
{% endfor %}
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom Admin</title>
<style>body{background:#0a0a0a;color:#0f0;font-family:monospace;padding:20px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #0f0;padding:8px;}</style>
</head>
<body>
<h1>Admin Panel</h1>
<h2>Users</h2>
<table><tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
{% for u in users %}<tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{{ u.4 }}</td></tr>{% endfor %}</table>
<h2>Notes</h2>
<table><tr><th>ID</th><th>User ID</th><th>Serial</th><th>Created</th></tr>
{% for n in notes %}<tr><td>{{ n.0 }}</td><td>{{ n.1 }}</td><td>{{ n.2 }}</td><td>{{ n.4 }}</td></tr>{% endfor %}</table>
<h2>Logs</h2>
<table><tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
{% for l in logs %}<tr><td>{{ l.4 }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>{% endfor %}</table>
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        c.execute("SELECT id, username, password, is_admin FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            log_action(user[0], "Login", request.remote_addr)
            if user[3] == 1:
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        error = "Invalid credentials"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('moneymom.db')
        c = conn.cursor()
        hashed = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                      (username, hashed, request.remote_addr, datetime.datetime.now().isoformat(), 0))
            conn.commit()
            return render_template_string(REGISTER_TEMPLATE, success="Account created! Please login.")
        except:
            return render_template_string(REGISTER_TEMPLATE, error="Username exists")
        finally:
            conn.close()
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created DESC", (session['user_id'],))
    notes = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], notes=notes)

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    user_id = session['user_id']
    serial = generate_serial()
    front_img, back_img = create_note_pair(serial)
    
    # Combine front and back into one image (side by side)
    total_width = front_img.width * 2
    combined = Image.new('RGB', (total_width, front_img.height), color=(245, 235, 190))
    combined.paste(front_img, (0, 0))
    combined.paste(back_img, (front_img.width, 0))
    
    buffered = io.BytesIO()
    combined.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, serial_number, image_blob, created) VALUES (?, ?, ?, ?)",
              (user_id, serial, img_base64, datetime.datetime.now().isoformat()))
    note_id = c.lastrowid
    conn.commit()
    conn.close()
    
    log_action(user_id, f"Generated note: {serial}", request.remote_addr)
    return redirect(url_for('dashboard'))

@app.route('/download/<int:note_id>')
@login_required
def download(note_id):
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM notes WHERE id=?", (note_id,))
    note = c.fetchone()
    conn.close()
    if note and note[1] == session['user_id']:
        img_data = base64.b64decode(note[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'BIF_10000_{note_id}.png')
    return "Not found", 404

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom.db')
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    notes = c.execute("SELECT * FROM notes ORDER BY created DESC LIMIT 100").fetchall()
    logs = c.execute("SELECT * FROM logs ORDER BY created DESC LIMIT 200").fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, users=users, notes=notes, logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
