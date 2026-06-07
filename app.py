#!/usr/bin/env python3
"""
MoneyMom Live Edit - Real-time text editing on permit image
"""

from flask import Flask, request, render_template_string, send_file, session, redirect, url_for
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Default text areas with pixel coordinates
TEXT_AREAS = {
    'surname': {'label': 'SURNAME', 'x': 210, 'y': 107, 'width': 300, 'height': 22, 'default': 'SEZERANO'},
    'given_names': {'label': 'GIVEN NAMES', 'x': 210, 'y': 134, 'width': 300, 'height': 22, 'default': 'JEAN'},
    'dob': {'label': 'DATE OF BIRTH', 'x': 210, 'y': 162, 'width': 130, 'height': 20, 'default': '01-01-1986'},
    'pob': {'label': 'PLACE OF BIRTH', 'x': 350, 'y': 162, 'width': 250, 'height': 20, 'default': 'KAMENGE BUJUMBURA'},
    'residence': {'label': 'RESIDENCE', 'x': 210, 'y': 191, 'width': 400, 'height': 22, 'default': 'MUTIMBUZI, GAHAHE'},
    'license_number': {'label': 'LICENSE NUMBER', 'x': 210, 'y': 222, 'width': 300, 'height': 22, 'default': 'PNC0139839'},
    'issue_date': {'label': 'ISSUE DATE', 'x': 200, 'y': 320, 'width': 130, 'height': 20, 'default': '13-09-2016'},
    'issue_place': {'label': 'PLACE OF ISSUE', 'x': 580, 'y': 320, 'width': 200, 'height': 20, 'default': 'BUJUMBURA'},
    'categories': {'label': 'CATEGORIES', 'x': 160, 'y': 348, 'width': 150, 'height': 22, 'default': 'A, B'},
    'expiry_date': {'label': 'EXPIRY DATE', 'x': 580, 'y': 348, 'width': 150, 'height': 20, 'default': '12-09-2026'},
    'card_number': {'label': 'CARD NUMBER', 'x': 160, 'y': 376, 'width': 200, 'height': 20, 'default': 'DL0006875'}
}

def smart_erase_text(img, x, y, width, height):
    """Erase text by sampling background color from edges"""
    region = img.crop((x, y, x + width, y + height))
    w, h = region.size
    
    if w < 5 or h < 5:
        return
    
    # Sample from 4 corners to get background color
    corners = []
    if w > 4 and h > 4:
        corners.append(region.getpixel((2, 2)))
        corners.append(region.getpixel((w - 3, 2)))
        corners.append(region.getpixel((2, h - 3)))
        corners.append(region.getpixel((w - 3, h - 3)))
    
    if corners:
        bg_color = (
            sum(c[0] for c in corners) // len(corners),
            sum(c[1] for c in corners) // len(corners),
            sum(c[2] for c in corners) // len(corners)
        )
    else:
        bg_color = (248, 242, 230)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([(x, y), (x + width, y + height)], fill=bg_color)

def draw_black_text(img, text, x, y, font_size=15):
    """Draw black text on image"""
    draw = ImageDraw.Draw(img)
    
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\Arial.ttf"
    ]
    
    font = None
    for path in font_paths:
        try:
            font = ImageFont.truetype(path, font_size)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    draw.text((x, y), text.upper(), fill=(0, 0, 0), font=font)

def generate_preview_image(image_base64, edits):
    """Generate preview with current edits"""
    image_data = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(image_data))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    for field, new_value in edits.items():
        if field in TEXT_AREAS:
            area = TEXT_AREAS[field]
            smart_erase_text(img, area['x'], area['y'], area['width'], area['height'])
            draw_black_text(img, new_value, area['x'], area['y'], font_size=15)
    
    output = io.BytesIO()
    img.save(output, format='PNG')
    return base64.b64encode(output.getvalue()).decode()

def init_db():
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, ip TEXT, created TEXT, is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS permits
                 (id INTEGER PRIMARY KEY, user_id INTEGER, original_image TEXT, edits TEXT, created TEXT)''')
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
    conn = sqlite3.connect('moneymom_live.db')
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

# ============ SINGLE PAGE HTML - LIVE EDITING ============
MAIN_EDITOR_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MoneyMom | Live Permit Editor</title>
    <meta charset="UTF-8">
    <style>
        * { box-sizing: border-box; }
        body {
            background: #0a0e1a;
            color: #0f0;
            font-family: 'Courier New', monospace;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid #0f0;
            flex-wrap: wrap;
        }
        .logo h1 {
            font-size: 28px;
            background: linear-gradient(135deg, #00ff41, #00cc33);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin: 0;
        }
        .row {
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
        }
        .image-panel {
            flex: 2;
            min-width: 500px;
            background: #0a0a0a;
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #00ff41;
        }
        .image-panel h3 {
            margin-top: 0;
            color: #00ff41;
        }
        .preview-img {
            width: 100%;
            border: 1px solid #333;
            background: #fff;
            border-radius: 5px;
        }
        .editor-panel {
            flex: 1;
            min-width: 280px;
            background: #111;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #00ff41;
        }
        .editor-panel h3 {
            margin-top: 0;
            color: #ff00ff;
        }
        .field-group {
            margin-bottom: 12px;
        }
        .field-label {
            color: #ff00ff;
            font-size: 10px;
            display: block;
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        input {
            width: 100%;
            padding: 8px 10px;
            background: #1a1a2e;
            border: 1px solid #00ff41;
            color: #0f0;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        input:focus {
            outline: none;
            border-color: #ff00ff;
            box-shadow: 0 0 8px #ff00ff;
        }
        button {
            background: #00ff41;
            color: #000;
            padding: 12px 20px;
            border: none;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            border-radius: 5px;
            width: 100%;
            margin-top: 15px;
        }
        button:hover {
            background: #ff00ff;
            color: #fff;
        }
        .logout-btn {
            color: #ff6666;
            text-decoration: none;
            padding: 8px 15px;
            border: 1px solid #ff6666;
            border-radius: 5px;
        }
        .logout-btn:hover {
            background: #ff6666;
            color: #000;
        }
        .click-hint {
            font-size: 11px;
            color: #666;
            text-align: center;
            margin-top: 10px;
        }
        hr {
            border-color: #333;
            margin: 15px 0;
        }
        .status {
            background: #1a1a2e;
            padding: 8px;
            border-radius: 5px;
            font-size: 11px;
            color: #00ff41;
            margin-top: 10px;
            text-align: center;
        }
        a {
            color: #0f0;
            text-decoration: none;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo"><h1>📷 MONEYMOM | LIVE PERMIT EDITOR</h1></div>
        <div><a href="/logout" class="logout-btn">🚪 EXIT</a></div>
    </div>
    
    <div class="row">
        <div class="image-panel">
            <h3>📄 PREVIEW (edits appear instantly)</h3>
            <img id="preview-image" class="preview-img" src="data:image/png;base64,{{ image_base64 }}" alt="Permit Preview">
            <div class="click-hint">💡 Click on any text area on the image to edit it</div>
            <div class="status" id="status-text">✅ Ready — edit any field below or click on the image</div>
        </div>
        
        <div class="editor-panel">
            <h3>✏️ EDIT FIELDS</h3>
            <form id="edit-form">
                {% for field, area in text_areas.items() %}
                <div class="field-group">
                    <label class="field-label">{{ area.label }}</label>
                    <input type="text" 
                           name="{{ field }}" 
                           value="{{ area.default }}" 
                           data-field="{{ field }}"
                           id="input-{{ field }}"
                           autocomplete="off">
                </div>
                {% endfor %}
                <hr>
                <button type="button" id="save-btn">💾 SAVE & DOWNLOAD</button>
            </form>
            <p style="text-align:center; margin-top:15px;"><a href="/dashboard">← My Permits</a></p>
        </div>
    </div>
</div>

<script>
    // Current edits
    let currentEdits = {};
    
    // Get all input fields
    const inputs = document.querySelectorAll('#edit-form input');
    const previewImg = document.getElementById('preview-image');
    const statusDiv = document.getElementById('status-text');
    const saveBtn = document.getElementById('save-btn');
    
    // Text areas coordinates for click detection
    const textAreas = {{ text_areas_json|safe }};
    const permitId = {{ permit_id }};
    
    // Initialize currentEdits
    inputs.forEach(input => {
        const field = input.getAttribute('data-field');
        currentEdits[field] = input.value;
        
        // Add event listener for real-time update
        input.addEventListener('input', function() {
            const fieldName = this.getAttribute('data-field');
            currentEdits[fieldName] = this.value;
            updatePreview();
        });
    });
    
    // Update preview function
    function updatePreview() {
        statusDiv.innerHTML = '⏳ Updating preview...';
        statusDiv.style.color = '#ffaa00';
        
        fetch('/api/preview/{{ permit_id }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentEdits)
        })
        .then(response => response.json())
        .then(data => {
            if (data.image_base64) {
                previewImg.src = 'data:image/png;base64,' + data.image_base64;
                statusDiv.innerHTML = '✅ Preview updated — ' + new Date().toLocaleTimeString();
                statusDiv.style.color = '#00ff41';
            } else {
                statusDiv.innerHTML = '❌ Error updating preview';
                statusDiv.style.color = '#ff4444';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            statusDiv.innerHTML = '❌ Connection error';
            statusDiv.style.color = '#ff4444';
        });
    }
    
    // Save and download
    saveBtn.addEventListener('click', function() {
        statusDiv.innerHTML = '💾 Saving and downloading...';
        statusDiv.style.color = '#ffaa00';
        
        fetch('/api/save/{{ permit_id }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(currentEdits)
        })
        .then(response => response.json())
        .then(data => {
            if (data.download_url) {
                statusDiv.innerHTML = '✅ Saved! Downloading...';
                window.location.href = data.download_url;
                setTimeout(() => {
                    statusDiv.innerHTML = '✅ Ready — edit any field';
                    statusDiv.style.color = '#00ff41';
                }, 2000);
            } else {
                statusDiv.innerHTML = '❌ Save failed';
                statusDiv.style.color = '#ff4444';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            statusDiv.innerHTML = '❌ Save error';
            statusDiv.style.color = '#ff4444';
        });
    });
    
    // Click on image to edit corresponding field
    function getRelativeCoordinates(event, element) {
        const rect = element.getBoundingClientRect();
        const scaleX = element.naturalWidth / rect.width;
        const scaleY = element.naturalHeight / rect.height;
        const x = (event.clientX - rect.left) * scaleX;
        const y = (event.clientY - rect.top) * scaleY;
        return { x, y };
    }
    
    previewImg.addEventListener('click', function(event) {
        const coords = getRelativeCoordinates(event, previewImg);
        
        let foundField = null;
        for (const [field, area] of Object.entries(textAreas)) {
            if (coords.x >= area.x && coords.x <= area.x + area.width &&
                coords.y >= area.y && coords.y <= area.y + area.height) {
                foundField = field;
                break;
            }
        }
        
        if (foundField) {
            const input = document.getElementById('input-' + foundField);
            input.style.border = '2px solid #ff00ff';
            input.style.boxShadow = '0 0 10px #ff00ff';
            input.focus();
            setTimeout(() => {
                input.style.border = '';
                input.style.boxShadow = '';
            }, 1000);
            statusDiv.innerHTML = '✏️ Editing: ' + textAreas[foundField].label;
        } else {
            statusDiv.innerHTML = '⚠️ Click on a text field (Surname, Name, Date, etc.)';
            setTimeout(() => {
                statusDiv.innerHTML = '✅ Ready';
            }, 1500);
        }
    });
    
    // Initial preview update
    setTimeout(() => {
        updatePreview();
    }, 100);
</script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | My Permits</title>
<style>
body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px;flex-wrap:wrap;}
.card{background:#111;border:1px solid #0f0;border-radius:10px;padding:20px;margin-bottom:15px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📷 MONEYMOM PERMITS</h1><div><a href="/new">+ NEW PERMIT</a> | <a href="/logout">EXIT</a></div></div>
<p>Welcome, {{ username }}</p>
<div style="margin:30px 0;"><a href="/new"><button>📄 SCAN NEW PERMIT</button></a></div>
<h2>Your Permits</h2>
{% for permit in permits %}
<div class="card">
<span><strong>ID:</strong> {{ permit.0 }} | <strong>{{ permit.3[:19] }}</strong></span>
<span><a href="/edit/{{ permit.0 }}">✏️ EDIT</a> | <a href="/download/{{ permit.0 }}">⬇️ DOWNLOAD</a></span>
</div>
{% else %}
<p>No permits yet. Click "SCAN NEW PERMIT" to upload.</p>
{% endfor %}
</div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Login</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;}
.card{background:#111;padding:40px;border:1px solid #0f0;border-radius:10px;width:350px;}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{width:100%;padding:10px;background:#0f0;color:#000;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="card"><h1 style="text-align:center;">MONEYMOM</h1><h3 style="text-align:center;">Permit Editor</h3>
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
<h2>Permits</h2><table><tr><th>ID</th><th>User ID</th><th>Created</th></tr>
{% for p in permits %}<tr><td>{{ p.0 }}</td><td>{{ p.1 }}</td><td>{{ p.3 }}</td></tr>{% endfor %}</table>
<h2>Logs</h2></table> hilab<th>Time</th><th>User ID</th><th>Action</th><th>IP</th></tr>
{% for l in logs %}<tr><td>{{ l.4 }}</td><td>{{ l.1 }}</td><td>{{ l.2 }}</td><td>{{ l.3 }}</td></tr>{% endfor %}</table>
<p><a href="/logout">Logout</a></p>
</body>
</html>
'''

UPLOAD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>MoneyMom | Upload Permit</title>
<style>body{background:#0a0e1a;color:#0f0;font-family:monospace;padding:20px;}
.container{max-width:600px;margin:0 auto;background:#111;padding:30px;border:1px solid #0f0;border-radius:10px;}
input{width:100%;padding:10px;margin:10px 0;background:#222;border:1px solid #0f0;color:#0f0;}
button{background:#0f0;color:#000;padding:10px 20px;border:none;cursor:pointer;}
a{color:#0f0;text-decoration:none;}</style>
</head>
<body>
<div class="container"><h1>📄 UPLOAD PERMIT</h1>
<p>Upload a scanned image of a REAL Burundi Driving Permit</p>
<form method="POST" enctype="multipart/form-data"><input type="file" name="permit_image" accept="image/*" required><button type="submit">📤 UPLOAD</button></form>
<p style="margin-top:20px;"><a href="/dashboard">← Back</a></p></div>
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
        conn = sqlite3.connect('moneymom_live.db')
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
        conn = sqlite3.connect('moneymom_live.db')
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
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute("SELECT * FROM permits WHERE user_id=? ORDER BY created DESC", (session['user_id'],))
    permits = c.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_TEMPLATE, username=session['username'], permits=permits)

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_permit():
    if request.method == 'POST':
        file = request.files['permit_image']
        if file and file.filename:
            image_data = file.read()
            image_base64 = base64.b64encode(image_data).decode()
            
            conn = sqlite3.connect('moneymom_live.db')
            c = conn.cursor()
            c.execute("INSERT INTO permits (user_id, original_image, edits, created) VALUES (?, ?, ?, ?)",
                      (session['user_id'], image_base64, json.dumps(TEXT_AREAS), datetime.datetime.now().isoformat()))
            permit_id = c.lastrowid
            conn.commit()
            conn.close()
            
            log_action(session['user_id'], f"Uploaded permit {permit_id}", request.remote_addr)
            return redirect(url_for('edit', permit_id=permit_id))
    
    return render_template_string(UPLOAD_TEMPLATE)

@app.route('/edit/<int:permit_id>')
@login_required
def edit(permit_id):
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute("SELECT original_image, edits FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    conn.close()
    
    if not permit:
        return "Permit not found", 404
    
    text_areas = json.loads(permit[1])
    text_areas_json = json.dumps(text_areas)
    
    return render_template_string(MAIN_EDITOR_TEMPLATE, 
                                  permit_id=permit_id,
                                  image_base64=permit[0],
                                  text_areas=text_areas,
                                  text_areas_json=text_areas_json)

@app.route('/api/preview/<int:permit_id>', methods=['POST'])
@login_required
def api_preview(permit_id):
    data = request.get_json()
    edits = data
    
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute("SELECT original_image FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    conn.close()
    
    if not permit:
        return jsonify({'error': 'Not found'}), 404
    
    preview_base64 = generate_preview_image(permit[0], edits)
    return jsonify({'image_base64': preview_base64})

@app.route('/api/save/<int:permit_id>', methods=['POST'])
@login_required
def api_save(permit_id):
    data = request.get_json()
    edits = data
    
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute("SELECT original_image FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    
    if not permit:
        conn.close()
        return jsonify({'error': 'Not found'}), 404
    
    # Generate final image
    final_base64 = generate_preview_image(permit[0], edits)
    
    # Update stored edits
    for field, value in edits.items():
        if field in TEXT_AREAS:
            TEXT_AREAS[field]['default'] = value
    
    c.execute("UPDATE permits SET edits=? WHERE id=?", (json.dumps(TEXT_AREAS), permit_id))
    conn.commit()
    conn.close()
    
    log_action(session['user_id'], f"Saved permit {permit_id} with edits", request.remote_addr)
    
    return jsonify({'download_url': f'/download/{permit_id}'})

@app.route('/download/<int:permit_id>')
@login_required
def download(permit_id):
    conn = sqlite3.connect('moneymom_live.db')
    c = conn.cursor()
    c.execute("SELECT original_image, edits FROM permits WHERE id=? AND user_id=?", (permit_id, session['user_id']))
    permit = c.fetchone()
    conn.close()
    
    if not permit:
        return "Not found", 404
    
    text_areas = json.loads(permit[1])
    edits = {field: area['default'] for field, area in text_areas.items()}
    
    final_base64 = generate_preview_image(permit[0], edits)
    img_data = base64.b64decode(final_base64)
    
    return send_file(io.BytesIO(img_data), mimetype='image/png', as_attachment=True, download_name=f'permit_{permit_id}.png')

@app.route('/admin')
@login_required
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('moneymom_live.db')
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
    print("📷 MONEYMOM LIVE EDITOR - Real-time preview")
    print(f"📍 Running on: http://localhost:{port}")
    print("👑 Admin: Mpc / 08800Mpc+_+")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=True)
