#!/usr/bin/env python3
"""
MoneyMom Permit Platform - Burundi Driving License Generator
Authorized Government Use Only
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import sqlite3
import datetime
import os
import secrets
import base64
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Template for Burundi Driving License (based on your real permit)
# Card size: 85.6 x 54 mm at 300 DPI = 1011 x 638 pixels
WIDTH = 1011
HEIGHT = 638

def create_permit_image(data):
    """Generate a Burundi Driving License with custom data"""
    
    # Background color (light cream/off-white from real permit)
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(250, 245, 235))
    draw = ImageDraw.Draw(img)
    
    # Load fonts (simplified - use default if needed)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Border
    draw.rectangle([(5, 5), (WIDTH-5, HEIGHT-5)], outline=(100, 80, 50), width=2)
    
    # Top header: REPUBLIQUE DU BURUNDI
    draw.text((WIDTH//2 - 200, 15), "REPUBLIQUE DU BURUNDI", fill=(0, 0, 0), font=font_title)
    draw.text((WIDTH//2 - 120, 42), "Republika y'Uburundi - Republic of Burundi", fill=(0, 0, 0), font=font_small)
    
    # Title: PERMIS DE CONDUIRE
    draw.text((WIDTH//2 - 150, 70), "PERMIS DE CONDUIRE", fill=(0, 0, 0), font=font_title)
    draw.text((WIDTH//2 - 140, 95), "DRIVING LICENCE - IMPERAMIDONKA", fill=(0, 0, 0), font=font_small)
    
    # Divider line
    draw.line([(20, 115), (WIDTH-20, 115)], fill=(80, 60, 40), width=1)
    
    # Field 1: SURNAME
    draw.text((30, 130), "1. NOM / IZINA - SURNAME", fill=(80, 60, 40), font=font_label)
    draw.text((260, 128), data['surname'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(260, 148), (500, 148)], fill=(0, 0, 0), width=1)
    
    # Field 2: GIVEN NAMES
    draw.text((30, 160), "2. PRENOM / AMANINA - GIVEN NAMES", fill=(80, 60, 40), font=font_label)
    draw.text((260, 158), data['given_names'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(260, 178), (500, 178)], fill=(0, 0, 0), width=1)
    
    # Field 3: DATE AND PLACE OF BIRTH
    draw.text((30, 190), "3. DATE ET LIEU DE NAISSANCE", fill=(80, 60, 40), font=font_label)
    draw.text((260, 188), f"{data['dob']} {data['pob'].upper()}", fill=(0, 0, 0), font=font_value)
    draw.line([(260, 208), (600, 208)], fill=(0, 0, 0), width=1)
    
    # Field 4: RESIDENCE
    draw.text((30, 220), "4. RESIDENCE - ADRESSE - ADDRESS", fill=(80, 60, 40), font=font_label)
    draw.text((260, 218), data['residence'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(260, 238), (600, 238)], fill=(0, 0, 0), width=1)
    
    # Field 5: LICENSE NUMBER
    draw.text((30, 250), "5. N° DU PERMIS DE CONDUIRE", fill=(80, 60, 40), font=font_label)
    draw.text((260, 248), data['license_number'], fill=(0, 0, 0), font=font_value)
    draw.line([(260, 268), (500, 268)], fill=(0, 0, 0), width=1)
    
    # Right side - Photo area
    photo_x = 700
    photo_y = 130
    draw.rectangle([(photo_x, photo_y), (photo_x + 150, photo_y + 180)], outline=(80, 60, 40), width=2)
    draw.text((photo_x + 50, photo_y + 80), "PHOTO", fill=(150, 140, 120), font=font_small)
    
    # If photo provided, paste it
    if data.get('photo_base64'):
        try:
            photo_data = base64.b64decode(data['photo_base64'])
            photo = Image.open(io.BytesIO(photo_data))
            photo = photo.resize((146, 176))
            img.paste(photo, (photo_x + 2, photo_y + 2))
        except:
            pass
    
    # Bottom section - Categories and dates
    draw.line([(20, 300), (WIDTH-20, 300)], fill=(80, 60, 40), width=1)
    
    # Issue Date
    draw.text((30, 315), "Date d'émission / Issue Date:", fill=(80, 60, 40), font=font_small)
    draw.text((230, 313), data['issue_date'], fill=(0, 0, 0), font=font_value)
    
    # Place of Issue
    draw.text((450, 315), "Lieu d'émission / Place of Issue:", fill=(80, 60, 40), font=font_small)
    draw.text((650, 313), data['issue_place'].upper(), fill=(0, 0, 0), font=font_value)
    
    # Categories
    draw.text((30, 345), "Catégories / Categories:", fill=(80, 60, 40), font=font_small)
    draw.text((180, 343), data['categories'].upper(), fill=(0, 0, 0), font=font_value)
    
    # Expiry Date
    draw.text((500, 345), "Expire le / Expires:", fill=(80, 60, 40), font=font_small)
    draw.text((630, 343), data['expiry_date'], fill=(0, 0, 0), font=font_value)
    
    # Card Number
    draw.text((30, 375), "N° de carte / Card N°:", fill=(80, 60, 40), font=font_small)
    draw.text((180, 373), data['card_number'], fill=(0, 0, 0), font=font_value)
    
    # Signature area
    draw.text((30, 410), "Signature du titulaire / Holder's signature:", fill=(80, 60, 40), font=font_small)
    draw.line([(250, 415), (500, 415)], fill=(0, 0, 0), width=1)
    
    # Authority signature
    draw.text((550, 410), "Signature de l'autorité / Authority signature:", fill=(80, 60, 40), font=font_small)
    draw.line([(780, 415), (980, 415)], fill=(0, 0, 0), width=1)
    
    # Footer text
    draw.text((WIDTH//2 - 200, HEIGHT - 30), "S. AUTORITE COMPETENTE (KINNEVE GOURMAND AUTOMOTIVE)", fill=(100, 80, 60), font=font_tiny)
    
    return img

# Flask routes and database setup (same structure as MoneyMom)
def init_db():
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS permits
                 (id INTEGER PRIMARY KEY, user_id INTEGER, data TEXT, image_blob TEXT, created TEXT)''')
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

def log_action(user_id, action, ip):
    conn = sqlite3.connect('moneymom_permit.db')
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

# ============ HTML TEMPLATES ============

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Permit Platform</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
.card{background:#111;padding:40px;border:1px solid #0f0;border-radius:10px;width:350px;}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{width:100%;padding:10px;background:#0f0;color:#000;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="card"><h1 style="text-align:center;">MONEYMOM</h1><h3 style="text-align:center;">Permis de Conduire</h3>
<form method="POST"><input type="text" name="username" placeholder="Username" required><input type="password" name="password" placeholder="Password" required><button type="submit">Login</button></form>
<p style="text-align:center;margin-top:20px;"><a href="/register">Register</a></p>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}</div>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Register</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
.card{background:#111;padding:40px;border:1px solid #0f0;border-radius:10px;width:350px;}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{width:100%;padding:10px;background:#0f0;color:#000;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="card"><h1 style="text-align:center;">REGISTER</h1>
<form method="POST"><input type="text" name="username" placeholder="Username" required><input type="password" name="password" placeholder="Password" required><input type="password" name="confirm" placeholder="Confirm" required><button type="submit">Create Account</button></form>
<p style="text-align:center;margin-top:20px;"><a href="/login">Back to Login</a></p>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}</div>
</body>
</html>
'''

CREATE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Create Permit</title>
<style>
body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
.container{max-width:800px;margin:0 auto;background:#111;padding:30px;border:1px solid #0f0;border-radius:10px;}
input,select{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
.label{color:#0f0;margin-top:15px;display:block;}
h1{text-align:center;}
a{color:#0f0;text-decoration:none;}
</style>
</head>
<body>
<div class="container">
<h1>📄 Create Burundi Driving Permit</h1>
<form method="POST" enctype="multipart/form-data">
<label class="label">1. SURNAME (NOM)</label><input type="text" name="surname" value="SEZERANO" required>
<label class="label">2. GIVEN NAMES (PRENOM)</label><input type="text" name="given_names" value="JEAN" required>
<label class="label">3. DATE OF BIRTH (JJ-MM-AAAA)</label><input type="text" name="dob" value="01-01-1986" required>
<label class="label">3. PLACE OF BIRTH</label><input type="text" name="pob" value="KAMENGE BUJUMBURA" required>
<label class="label">4. RESIDENCE ADDRESS</label><input type="text" name="residence" value="MUTIMBUZI, GAHAHE" required>
<label class="label">5. LICENSE NUMBER</label><input type="text" name="license_number" value="PNC0139839" required>
<label class="label">ISSUE DATE (JJ-MM-AAAA)</label><input type="text" name="issue_date" value="13-09-2016" required>
<label class="label">PLACE OF ISSUE</label><input type="text" name="issue_place" value="BUJUMBURA" required>
<label class="label">CATEGORIES (ex: A, B, C, D)</label><input type="text" name="categories" value="MANUEL DE TRAVAIL" required>
<label class="label">EXPIRY DATE (JJ-MM-AAAA)</label><input type="text" name="expiry_date" value="12-09-2026" required>
<label class="label">CARD NUMBER</label><input type="text" name="card_number" value="DL0006875" required>
<label class="label">PHOTO (upload portrait photo)</label><input type="file" name="photo" accept="image/*">
<button type="submit">🎫 GENERATE PERMIT</button>
</form>
<p style="margin-top:20px;"><a href="/dashboard">← Back to Dashboard</a></p>
</div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Permits</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;}
.container{max-width:1200px;margin:0 auto;}
.permit-card{background:#111;border:1px solid #0f0;border-radius:10px;padding:15px;margin-bottom:15px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>🎫 MONEYMOM PERMITS</h1><div><a href="/create">+ NEW PERMIT</a> | <a href="/logout">EXIT</a></div></div>
<p>Welcome, {{ username }}</p>
<div style="margin:30px 0;"><a href="/create"><button>📄 CREATE NEW DRIVING PERMIT</button></a></div>
<h2>Your Generated Permits</h2>
{% for permit in permits %}
<div class="permit-card">
<p><strong>ID:</strong> {{ permit.0 }} | <strong>Created:</strong> {{ permit.4[:16] }}</p>
<p><a href="/view/{{ permit.0 }}">👁️ View Permit</a> | <a href="/download/{{ permit.0 }}">⬇️ Download PNG</a></p>
</div>
{% else %}
<p>No permits generated yet. Click "CREATE NEW DRIVING PERMIT" above.</p>
{% endfor %}
</div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Admin</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #0f0;padding:8px;text-align:left;}</style>
</head>
<body>
<h1>Admin Panel</h1>
<h2>Users</h2>
<table><tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
{% for u in users %}<tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{{ u.4 }}</td></tr>{% endfor %}</table>
<h2>Permits</h2>
<table><tr><th>ID</th><th>User ID</th><th>Created</th></tr>
{% for p in permits %}<tr><td>{{ p.0 }}</td><td>{{ p.1 }}</td><td>{{ p.4 }}</td></tr>{% endfor %}</table>
<h2>Logs</h2>
<table><tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
{% for l in logs %}<tr><td>{{ l.4 }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>{% endfor %}</table>
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

# ============ ROUTES ============

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('moneymom_permit.db')
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
        confirm = request.form.get('confirm', '')
        if password != confirm:
            return render_template_string(REGISTER_TEMPLATE, error="Passwords do not match")
        conn = sqlite3.connect('moneymom_permit.db')
        c = conn.cursor()
        hashed = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, ip, created, is_admin) VALUES (?, ?, ?, ?, ?)",
                      (username, hashed, request.remote_addr, datetime.datetime.now().isoformat(), 0))
            conn.commit()
            return render_template_string(REGISTER_TEMPLATE, error="Account created! Please login.")
        except:
            return render_template_string(REGISTER_TEMPLATE, error="Username exists")
        finally:
            conn.close()
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    c.execute("SELECT * FROM permits WHERE user_id=? ORDER BY created DESC", (session['user_id'],))
    permits = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], permits=permits)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        # Collect form data
        data = {
            'surname': request.form['surname'],
            'given_names': request.form['given_names'],
            'dob': request.form['dob'],
            'pob': request.form['pob'],
            'residence': request.form['residence'],
            'license_number': request.form['license_number'],
            'issue_date': request.form['issue_date'],
            'issue_place': request.form['issue_place'],
            'categories': request.form['categories'],
            'expiry_date': request.form['expiry_date'],
            'card_number': request.form['card_number'],
            'photo_base64': None
        }
        
        # Handle photo upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                photo_data = photo.read()
                data['photo_base64'] = base64.b64encode(photo_data).decode()
        
        # Generate image
        img = create_permit_image(data)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Save to database
        import json
        conn = sqlite3.connect('moneymom_permit.db')
        c = conn.cursor()
        c.execute("INSERT INTO permits (user_id, data, image_blob, created) VALUES (?, ?, ?, ?)",
                  (session['user_id'], json.dumps(data), img_base64, datetime.datetime.now().isoformat()))
        permit_id = c.lastrowid
        conn.commit()
        conn.close()
        
        log_action(session['user_id'], f"Generated permit: {data['surname']} {data['given_names']}", request.remote_addr)
        return redirect(url_for('dashboard'))
    
    return render_template_string(CREATE_TEMPLATE)

@app.route('/view/<int:permit_id>')
@login_required
def view_permit(permit_id):
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM permits WHERE id=?", (permit_id,))
    permit = c.fetchone()
    conn.close()
    if permit and permit[1] == session['user_id']:
        return f'<img src="data:image/png;base64,{permit[0]}" style="max-width:100%;">'
    return "Not found", 404

@app.route('/download/<int:permit_id>')
@login_required
def download(permit_id):
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    c.execute("SELECT image_blob, user_id FROM permits WHERE id=?", (permit_id,))
    permit = c.fetchone()
    conn.close()
    if permit and permit[1] == session['user_id']:
        img_data = base64.b64decode(permit[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'permit_{permit_id}.png')
    return "Not found", 404

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    users = c.execute("SELECT * FROM users").fetchall()
    permits = c.execute("SELECT * FROM permits ORDER BY created DESC LIMIT 100").fetchall()
    logs = c.execute("SELECT * FROM logs ORDER BY created DESC LIMIT 200").fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, users=users, permits=permits, logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    print("="*60)
    print("🎫 MONEYMOM PERMIT PLATFORM - Burundi Driving License")
    print(f"📍 Running on: http://localhost:{port}")
    print("👑 Admin: Mpc / 08800Mpc+_+")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)
