#!/usr/bin/env python3
"""
MoneyMom Scan & Edit - Edit text directly on scanned permits
Authorized Government Use Only
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for, jsonify
from PIL import Image, ImageDraw, ImageFont
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

WIDTH = 1011
HEIGHT = 638

# Predefined text areas on the permit (pixel coordinates from your image)
# These are the clickable zones - adjust as needed
TEXT_AREAS = {
    'surname': {
        'label': 'SURNAME (NOM)',
        'x': 210, 'y': 107, 'width': 290, 'height': 20,
        'current': 'SEZERANO'
    },
    'given_names': {
        'label': 'GIVEN NAMES (PRENOM)',
        'x': 210, 'y': 134, 'width': 290, 'height': 20,
        'current': 'JEAN'
    },
    'dob': {
        'label': 'DATE OF BIRTH',
        'x': 210, 'y': 162, 'width': 150, 'height': 20,
        'current': '01-01-1986'
    },
    'pob': {
        'label': 'PLACE OF BIRTH',
        'x': 370, 'y': 162, 'width': 230, 'height': 20,
        'current': 'KAMENGE BUJUMBURA'
    },
    'residence': {
        'label': 'RESIDENCE',
        'x': 210, 'y': 191, 'width': 390, 'height': 20,
        'current': 'MUTIMBUZI, GAHAHE'
    },
    'license_number': {
        'label': 'LICENSE NUMBER',
        'x': 210, 'y': 222, 'width': 290, 'height': 20,
        'current': 'PNC0139839'
    },
    'issue_date': {
        'label': 'ISSUE DATE',
        'x': 200, 'y': 320, 'width': 150, 'height': 20,
        'current': '13-09-2016'
    },
    'issue_place': {
        'label': 'PLACE OF ISSUE',
        'x': 580, 'y': 320, 'width': 200, 'height': 20,
        'current': 'BUJUMBURA'
    },
    'categories': {
        'label': 'CATEGORIES',
        'x': 160, 'y': 348, 'width': 150, 'height': 20,
        'current': 'A, B, C, D'
    },
    'expiry_date': {
        'label': 'EXPIRY DATE',
        'x': 580, 'y': 348, 'width': 150, 'height': 20,
        'current': '12-09-2026'
    },
    'card_number': {
        'label': 'CARD NUMBER',
        'x': 160, 'y': 376, 'width': 200, 'height': 20,
        'current': 'DL0006875'
    }
}

def edit_text_on_image(base64_image, edits):
    """Edit text on the image using PIL"""
    
    # Decode base64 image
    image_data = base64.b64decode(base64_image)
    img = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    # Load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Apply each edit
    for field, new_value in edits.items():
        if field in TEXT_AREAS:
            area = TEXT_AREAS[field]
            # Draw white rectangle to hide old text
            draw.rectangle([(area['x'], area['y']), 
                           (area['x'] + area['width'], area['y'] + area['height'])], 
                          fill=(255, 255, 255))
            # Draw new text
            draw.text((area['x'], area['y']), new_value.upper(), fill=(0, 0, 0), font=font)
    
    # Save to bytes
    output = io.BytesIO()
    img.save(output, format='PNG')
    return base64.b64encode(output.getvalue()).decode()

def init_db():
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS permits
                 (id INTEGER PRIMARY KEY, user_id INTEGER, original_image TEXT, edited_image TEXT, edits TEXT, created TEXT)''')
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
    conn = sqlite3.connect('moneymom_editor.db')
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
<head><title>MoneyMom | Scan & Edit</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
.card{background:#111;padding:40px;border:1px solid #0f0;border-radius:10px;width:350px;}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{width:100%;padding:10px;background:#0f0;color:#000;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="card"><h1 style="text-align:center;">MONEYMOM</h1><h3 style="text-align:center;">Scan & Edit Permit</h3>
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

UPLOAD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Upload Permit</title>
    <style>
        body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
        .container{max-width:800px;margin:0 auto;background:#111;padding:30px;border:1px solid #0f0;border-radius:10px;}
        input,textarea{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
        button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
        .preview{max-width:100%;margin:20px 0;border:1px solid #0f0;}
        a{color:#0f0;text-decoration:none;}
        h1{text-align:center;}
        .field-group{background:#1a1a2e;padding:10px;margin:10px 0;border-radius:5px;}
        .field-label{color:#ff00ff;font-size:12px;display:inline-block;width:150px;}
        .field-input{display:inline-block;width:calc(100% - 160px);}
        .field-input input{width:100%;margin:0;}
    </style>
</head>
<body>
<div class="container">
    <h1>📄 SCAN & EDIT PERMIT</h1>
    <p>Step 1: Upload a scanned image of a real Burundi Driving Permit</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="permit_image" accept="image/*" required>
        <button type="submit">📤 UPLOAD & EDIT</button>
    </form>
    <p style="margin-top:20px;"><a href="/dashboard">← Back to Dashboard</a></p>
</div>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Edit Permit</title>
    <style>
        body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        .row{display:flex;flex-wrap:wrap;}
        .col-image{flex:2;min-width:500px;}
        .col-editor{flex:1;min-width:300px;background:#111;padding:20px;border:1px solid #0f0;border-radius:10px;margin-left:20px;}
        img{max-width:100%;border:1px solid #0f0;cursor:pointer;}
        .field-group{margin-bottom:15px;}
        .field-label{color:#ff00ff;font-size:12px;display:block;margin-bottom:5px;}
        input{width:100%;padding:8px;background:#222;border:1px solid #0f0;color:#0f0;border-radius:5px;}
        button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;margin-top:10px;}
        .click-hint{color:#888;font-size:11px;text-align:center;margin-top:10px;}
        a{color:#0f0;text-decoration:none;}
        h1{text-align:center;}
        .success{background:#00ff4111;border:1px solid #0f0;padding:10px;border-radius:5px;margin-bottom:20px;}
    </style>
</head>
<body>
<div class="container">
    <h1>📄 EDIT PERMIT</h1>
    <div class="row">
        <div class="col-image">
            <img id="permit-image" src="data:image/png;base64,{{ image_base64 }}" alt="Permit">
            <div class="click-hint">💡 Click on any text area on the image to edit it</div>
        </div>
        <div class="col-editor">
            <h3>✏️ Edit Fields</h3>
            <form id="edit-form" method="POST" action="/save_edit/{{ permit_id }}">
                {% for field, area in text_areas.items() %}
                <div class="field-group">
                    <label class="field-label">{{ area.label }}</label>
                    <input type="text" name="{{ field }}" value="{{ area.current }}" id="field-{{ field }}">
                </div>
                {% endfor %}
                <button type="submit">💾 SAVE & DOWNLOAD</button>
            </form>
            <p style="margin-top:20px;"><a href="/dashboard">← Back to Dashboard</a></p>
        </div>
    </div>
</div>
<script>
    // Make image clickable to edit specific fields
    const textAreas = {{ text_areas_json|safe }};
    const img = document.getElementById('permit-image');
    
    function getRelativeCoordinates(event, element) {
        const rect = element.getBoundingClientRect();
        const scaleX = element.naturalWidth / rect.width;
        const scaleY = element.naturalHeight / rect.height;
        const x = (event.clientX - rect.left) * scaleX;
        const y = (event.clientY - rect.top) * scaleY;
        return { x, y };
    }
    
    img.addEventListener('click', function(event) {
        const coords = getRelativeCoordinates(event, img);
        
        // Find which field was clicked
        for (const [field, area] of Object.entries(textAreas)) {
            if (coords.x >= area.x && coords.x <= area.x + area.width &&
                coords.y >= area.y && coords.y <= area.y + area.height) {
                // Highlight and focus the input field
                const input = document.getElementById('field-' + field);
                input.style.border = '2px solid #ff00ff';
                input.focus();
                setTimeout(() => {
                    input.style.border = '';
                }, 1500);
                break;
            }
        }
    });
</script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Dashboard</title>
<style>
body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;}
.permit-card{background:#111;border:1px solid #0f0;border-radius:10px;padding:15px;margin-bottom:15px;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📷 MONEYMOM SCAN & EDIT</h1><div><a href="/upload">+ NEW SCAN</a> | <a href="/logout">EXIT</a></div></div>
<p>Welcome, {{ username }}</p>
<div style="margin:30px 0;"><a href="/upload"><button>📄 SCAN NEW PERMIT</button></a></div>
<h2>Your Edited Permits</h2>
{% for permit in permits %}
<div class="permit-card">
<p><strong>ID:</strong> {{ permit.0 }} | <strong>Created:</strong> {{ permit.4[:16] }}</p>
<p><a href="/view/{{ permit.0 }}">👁️ View</a> | <a href="/download/{{ permit.0 }}">⬇️ Download PNG</a></p>
</div>
{% else %}
<p>No permits yet. Click "SCAN NEW PERMIT" to upload and edit a real permit.</p>
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
<h2>Users</h2></table><tr><th>ID</th><th>Username</th><th>IP</th><th>Created</th></tr>
{% for u in users %}<tr><td>{{ u.0 }}</td><td>{{ u.1 }}</td><td>{{ u.3 }}</td><td>{{ u.4 }}</td></tr>{% endfor %}</table>
<h2>Permits</h2><table><tr><th>ID</th><th>User ID</th><th>Created</th></tr>
{% for p in permits %}<tr><td>{{ p.0 }}</td><td>{{ p.1 }}</td><td>{{ p.4 }}</td></tr>{% endfor %}</table>
<h2>Logs</h2><table><tr><th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
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
        conn = sqlite3.connect('moneymom_editor.db')
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
        conn = sqlite3.connect('moneymom_editor.db')
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
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute("SELECT * FROM permits WHERE user_id=? ORDER BY created DESC", (session['user_id'],))
    permits = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], permits=permits)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['permit_image']
        if file and file.filename:
            # Read and encode image
            image_data = file.read()
            image_base64 = base64.b64encode(image_data).decode()
            
            # Save original with default text areas
            conn = sqlite3.connect('moneymom_editor.db')
            c = conn.cursor()
            c.execute("INSERT INTO permits (user_id, original_image, edited_image, edits, created) VALUES (?, ?, ?, ?, ?)",
                      (session['user_id'], image_base64, image_base64, json.dumps(TEXT_AREAS), datetime.datetime.now().isoformat()))
            permit_id = c.lastrowid
            conn.commit()
            conn.close()
            
            log_action(session['user_id'], "Uploaded permit scan", request.remote_addr)
            return redirect(url_for('edit', permit_id=permit_id))
    
    return render_template_string(UPLOAD_TEMPLATE)

@app.route('/edit/<int:permit_id>')
@login_required
def edit(permit_id):
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute("SELECT original_image, edits FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    conn.close()
    
    if not permit:
        return "Permit not found", 404
    
    # Get current text values from stored edits
    text_areas = json.loads(permit[1])
    
    # Prepare for template
    text_areas_json = json.dumps(text_areas)
    
    return render_template_string(EDIT_TEMPLATE, 
                                  permit_id=permit_id,
                                  image_base64=permit[0],
                                  text_areas=text_areas,
                                  text_areas_json=text_areas_json)

@app.route('/save_edit/<int:permit_id>', methods=['POST'])
@login_required
def save_edit(permit_id):
    # Get edits from form
    edits = {}
    for field in TEXT_AREAS.keys():
        if field in request.form:
            edits[field] = request.form[field]
            # Update stored text areas
            TEXT_AREAS[field]['current'] = request.form[field]
    
    # Get original image
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute("SELECT original_image FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    
    if not permit:
        conn.close()
        return "Permit not found", 404
    
    # Apply edits to image
    edited_image_base64 = edit_text_on_image(permit[0], edits)
    
    # Save edited image and updates
    c.execute("UPDATE permits SET edited_image=?, edits=? WHERE id=?",
              (edited_image_base64, json.dumps(TEXT_AREAS), permit_id))
    conn.commit()
    conn.close()
    
    log_action(session['user_id'], f"Edited permit {permit_id}", request.remote_addr)
    
    return redirect(url_for('download', permit_id=permit_id))

@app.route('/view/<int:permit_id>')
@login_required
def view_permit(permit_id):
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute("SELECT edited_image, user_id FROM permits WHERE id=?", (permit_id,))
    permit = c.fetchone()
    conn.close()
    if permit and permit[1] == session['user_id']:
        return f'<img src="data:image/png;base64,{permit[0]}" style="max-width:100%; border:1px solid #0f0;">'
    return "Not found", 404

@app.route('/download/<int:permit_id>')
@login_required
def download(permit_id):
    conn = sqlite3.connect('moneymom_editor.db')
    c = conn.cursor()
    c.execute("SELECT edited_image, user_id FROM permits WHERE id=?", (permit_id,))
    permit = c.fetchone()
    conn.close()
    if permit and permit[1] == session['user_id']:
        img_data = base64.b64decode(permit[0])
        return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'edited_permit_{permit_id}.png')
    return "Not found", 404

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom_editor.db')
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
    print("📷 MONEYMOM SCAN & EDIT - Edit text on scanned permits")
    print(f"📍 Running on: http://localhost:{port}")
    print("👑 Admin: Mpc / 08800Mpc+_+")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)
