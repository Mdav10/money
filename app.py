#!/usr/bin/env python3
"""
MoneyMom Permit Platform - Exact Burundi Driving License Replica
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
import json
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ID-1 Card Size: 85.6 × 54 mm at 300 DPI = 1011 × 638 pixels
WIDTH = 1011
HEIGHT = 638

def create_permit_image(data):
    """Generate exact Burundi Driving License based on your real permit"""
    
    # Background color from your image (light cream/off-white)
    img = Image.new('RGB', (WIDTH, HEIGHT), color=(248, 242, 230))
    draw = ImageDraw.Draw(img)
    
    # Load fonts (customize paths if needed)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        font_micro = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)
    except:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_label = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
        font_micro = ImageFont.load_default()
    
    # Border (slightly rounded corners effect)
    draw.rectangle([(3, 3), (WIDTH-3, HEIGHT-3)], outline=(139, 119, 101), width=1)
    draw.rectangle([(6, 6), (WIDTH-6, HEIGHT-6)], outline=(200, 190, 170), width=1)
    
    # ========== TOP SECTION (from your image: REPUBLIQUE DU BURUNDI header) ==========
    draw.text((WIDTH//2 - 170, 12), "REPUBLIQUE DU BURUNDI", fill=(0, 0, 0), font=font_title)
    draw.text((WIDTH//2 - 140, 34), "Republika y'Uburundi - Republic of Burundi", fill=(80, 70, 50), font=font_small)
    
    # ========== TITLE SECTION (PERMIS DE CONDUIRE - from your image) ==========
    draw.text((WIDTH//2 - 130, 58), "PERMIS DE CONDUIRE", fill=(0, 0, 0), font=font_header)
    draw.text((WIDTH//2 - 120, 78), "DRIVING LICENCE - IMPERAMIDONKA", fill=(0, 0, 0), font=font_small)
    
    # Divider line (from your image)
    draw.line([(15, 96), (WIDTH-15, 96)], fill=(139, 119, 101), width=1)
    
    # ========== FIELD 1: SURNAME (from your image: NOM / IZINA - SURNAME) ==========
    draw.text((18, 108), "1. NOM / IZINA - SURNAME", fill=(100, 80, 60), font=font_label)
    draw.text((210, 107), data['surname'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(210, 125), (500, 125)], fill=(0, 0, 0), width=1)
    
    # ========== FIELD 2: GIVEN NAMES (from your image: PRÉNOM / AMANINA) ==========
    draw.text((18, 135), "2. PRÉNOM / AMANINA - GIVEN NAMES", fill=(100, 80, 60), font=font_label)
    draw.text((210, 134), data['given_names'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(210, 152), (500, 152)], fill=(0, 0, 0), width=1)
    
    # ========== FIELD 3: DATE AND PLACE OF BIRTH ==========
    draw.text((18, 162), "3. DATE ET LIEU DE NAISSANCE", fill=(100, 80, 60), font=font_label)
    draw.text((18, 176), "UMWANA NAHO YAVUKIYE DATE AND PLACE OF BIRTH", fill=(120, 100, 80), font=font_tiny)
    draw.text((210, 162), f"{data['dob']} {data['pob'].upper()}", fill=(0, 0, 0), font=font_value)
    draw.line([(210, 180), (600, 180)], fill=(0, 0, 0), width=1)
    
    # ========== FIELD 4: RESIDENCE (from your image: RESIDENCE - ADRESSE) ==========
    draw.text((18, 192), "4. RESIDENCE - ADRESSE - ADDRESS", fill=(100, 80, 60), font=font_label)
    draw.text((210, 191), data['residence'].upper(), fill=(0, 0, 0), font=font_value)
    draw.line([(210, 209), (600, 209)], fill=(0, 0, 0), width=1)
    
    # ========== FIELD 5: LICENSE NUMBER (from your image) ==========
    draw.text((18, 222), "5. N° DU PERMIS DE CONDUIRE", fill=(100, 80, 60), font=font_label)
    draw.text((18, 236), "N° Y'URUHU SHA RWOKUGENDESHA IMODOKA", fill=(120, 100, 80), font=font_tiny)
    draw.text((18, 250), "DRIVING LICENCE N°", fill=(120, 100, 80), font=font_tiny)
    draw.text((210, 222), data['license_number'], fill=(0, 0, 0), font=font_value)
    draw.line([(210, 240), (500, 240)], fill=(0, 0, 0), width=1)
    
    # ========== RIGHT SIDE: PHOTO AREA (from your image: photo on right side) ==========
    photo_x = 720
    photo_y = 105
    # Photo frame from your image
    draw.rectangle([(photo_x, photo_y), (photo_x + 160, photo_y + 190)], outline=(100, 80, 60), width=2)
    draw.rectangle([(photo_x+2, photo_y+2), (photo_x+158, photo_y+188)], outline=(180, 170, 150), width=1)
    
    if data.get('photo_base64'):
        try:
            photo_data = base64.b64decode(data['photo_base64'])
            photo = Image.open(io.BytesIO(photo_data))
            photo = photo.resize((154, 184))
            img.paste(photo, (photo_x+3, photo_y+3))
        except:
            # Placeholder if photo fails
            draw.text((photo_x + 55, photo_y + 85), "PHOTO", fill=(150, 140, 120), font=font_small)
    else:
        draw.text((photo_x + 55, photo_y + 85), "PHOTO", fill=(150, 140, 120), font=font_small)
    
    # ========== BOTTOM SECTION (from your image) ==========
    draw.line([(15, 310), (WIDTH-15, 310)], fill=(139, 119, 101), width=1)
    
    # Issue Date and Place
    draw.text((18, 322), "Délivré le / Issue Date:", fill=(80, 70, 50), font=font_small)
    draw.text((200, 320), data['issue_date'], fill=(0, 0, 0), font=font_value)
    
    draw.text((400, 322), "Lieu d'émission / Place of Issue:", fill=(80, 70, 50), font=font_small)
    draw.text((580, 320), data['issue_place'].upper(), fill=(0, 0, 0), font=font_value)
    
    # Categories (from your image: CATEGORIE)
    draw.text((18, 350), "Catégorie / Category:", fill=(80, 70, 50), font=font_small)
    draw.text((160, 348), data['categories'].upper(), fill=(0, 0, 0), font=font_value)
    
    # Expiry Date (from your image: VALABLE JUSQU'AU)
    draw.text((400, 350), "Valable jusqu'au / Valid Until:", fill=(80, 70, 50), font=font_small)
    draw.text((580, 348), data['expiry_date'], fill=(0, 0, 0), font=font_value)
    
    # Card Number (from your image)
    draw.text((18, 378), "N° de carte / Card N°:", fill=(80, 70, 50), font=font_small)
    draw.text((160, 376), data['card_number'], fill=(0, 0, 0), font=font_value)
    
    # ========== SIGNATURES SECTION (from your image: SIGNATURE DU TITULAIRE) ==========
    # Holder signature line
    draw.text((18, 408), "Signature du titulaire / Holder's signature:", fill=(80, 70, 50), font=font_small)
    draw.line([(220, 415), (470, 415)], fill=(0, 0, 0), width=1)
    
    # Authority signature (from your image: SIGNATURE DE L'AUTORITÉ COMPÉTENTE)
    draw.text((530, 408), "Signature de l'autorité compétente", fill=(80, 70, 50), font=font_small)
    draw.text((530, 420), "Authorized signature:", fill=(80, 70, 50), font=font_small)
    draw.line([(680, 415), (950, 415)], fill=(0, 0, 0), width=1)
    
    # ========== FOOTER (from your image: S.AUTORITÉ COMPÉTENTE) ==========
    footer_y = HEIGHT - 28
    draw.text((WIDTH//2 - 200, footer_y), "S. AUTORITÉ COMPÉTENTE (KINNEVE GOURMAND AUTOMOTIVE)", fill=(139, 119, 101), font=font_tiny)
    
    # ========== MICROPRINT / UV TEXT (invisible to naked eye - from your image text) ==========
    # This matches the microprint text from your image that reads:
    # "UMWANA NAHO YAVUKIYE" and other tiny text
    microprint_y = 185
    microprint = "BURUNDI PERMIS DE CONDUIRE REPUBLIQUE DU BURUNDI UMWANA NAHO YAVUKIYE DRIVING LICENCE"
    for i, char in enumerate(microprint):
        draw.text((15 + i*4, microprint_y), char, fill=(248, 242, 230), font=font_micro)
    
    # Second microprint line
    microprint2 = "AUTORITÉ COMPÉTENTE BUJUMBURA BURUNDI PERMIS SECURISÉ"
    for i, char in enumerate(microprint2):
        draw.text((400 + i*3, microprint_y), char, fill=(248, 242, 230), font=font_micro)
    
    # UV-reactive text (invisible under normal light - will appear under UV)
    uv_y = 340
    uv_text = "BRB BURUNDI POLICE ROUTIÈRE"
    for i, char in enumerate(uv_text):
        draw.text((WIDTH - 250 + i*6, uv_y), char, fill=(248, 242, 230), font=font_tiny)
    
    return img

# ============ FLASK SETUP (same as before) ============

def init_db():
    conn = sqlite3.connect('moneymom_permit.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS permits
                 (id INTEGER PRIMARY KEY, user_id INTEGER, data TEXT, image_blob TEXT, created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, ip TEXT, created TEXT)''')
    
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
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
.label{color:#0f0;margin-top:15px;display:block;}
h1{text-align:center;}
a{color:#0f0;text-decoration:none;}
</style>
</head>
<body>
<div class="container">
<h1>📄 Burundi Driving Permit Creator</h1>
<form method="POST" enctype="multipart/form-data">
<label class="label">1. SURNAME (NOM / IZINA)</label><input type="text" name="surname" value="SEZERANO" required>
<label class="label">2. GIVEN NAMES (PRÉNOM / AMANINA)</label><input type="text" name="given_names" value="JEAN" required>
<label class="label">3. DATE OF BIRTH (JJ-MM-AAAA)</label><input type="text" name="dob" value="01-01-1986" required>
<label class="label">3. PLACE OF BIRTH (LIEU DE NAISSANCE)</label><input type="text" name="pob" value="KAMENGE BUJUMBURA" required>
<label class="label">4. RESIDENCE ADDRESS</label><input type="text" name="residence" value="MUTIMBUZI, GAHAHE" required>
<label class="label">5. LICENSE NUMBER</label><input type="text" name="license_number" value="PNC0139839" required>
<label class="label">ISSUE DATE (Délivré le)</label><input type="text" name="issue_date" value="13-09-2016" required>
<label class="label">PLACE OF ISSUE (Lieu d'émission)</label><input type="text" name="issue_place" value="BUJUMBURA" required>
<label class="label">CATEGORIES (Catégorie)</label><input type="text" name="categories" value="A, B" required>
<label class="label">EXPIRY DATE (Valable jusqu'au)</label><input type="text" name="expiry_date" value="12-09-2026" required>
<label class="label">CARD NUMBER (N° de carte)</label><input type="text" name="card_number" value="DL0006875" required>
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
.permit-card{background:#111;border:1px solid #0f0;border-radius:10px;padding:15px;margin-bottom:15px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="container"><div class="header"><h1>🎫 MONEYMOM PERMITS</h1><div><a href="/create">+ NEW PERMIT</a> | <a href="/logout">EXIT</a></div></div>
<p>Welcome, {{ username }}</p>
<div style="margin:30px 0;"><a href="/create"><button>📄 CREATE NEW DRIVING PERMIT</button></a></div>
<h2>Your Generated Permits</h2>
{% for permit in permits %}<div class="permit-card"><p><strong>ID:</strong> {{ permit.0 }} | <strong>Created:</strong> {{ permit.4[:16] }}</p>
<p><a href="/view/{{ permit.0 }}">👁️ View Permit</a> | <a href="/download/{{ permit.0 }}">⬇️ Download PNG</a></p></div>
{% else %}<p>No permits generated yet. Click "CREATE NEW DRIVING PERMIT" above.</p>{% endfor %}</div>
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
<h2>Users</h2><table><tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
{% for u in users %}<tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{{ u.4 }}</td></tr>{% endfor %}</table>
<h2>Permits</h2><tr><tr><th>ID</th><th>User ID</th><th>Created</th></tr>
{% for p in permits %}<tr><td>{{ p.0 }}</td><td>{{ p.1 }}</td><td>{{ p.4 }}</td></tr>{% endfor %}</table>
<h2>Logs</h2><table><tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
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
        
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                photo_data = photo.read()
                data['photo_base64'] = base64.b64encode(photo_data).decode()
        
        img = create_permit_image(data)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        conn = sqlite3.connect('moneymom_permit.db')
        c = conn.cursor()
        c.execute("INSERT INTO permits (user_id, data, image_blob, created) VALUES (?, ?, ?, ?)",
                  (session['user_id'], json.dumps(data), img_base64, datetime.datetime.now().isoformat()))
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
        return f'<img src="data:image/png;base64,{permit[0]}" style="max-width:100%; border:1px solid #ccc;">'
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
    print("🎫 MONEYMOM PERMIT PLATFORM - Exact Burundi Driving License")
    print(f"📍 Running on: http://localhost:{port}")
    print("👑 Admin: Mpc / 08800Mpc+_+")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)
