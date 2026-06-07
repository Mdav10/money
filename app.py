<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyMom | Click to Edit Permit</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            background: #0a0e1a;
            font-family: 'Segoe UI', 'Courier New', monospace;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #00ff41;
        }
        .logo h1 {
            color: #00ff41;
            font-size: 28px;
        }
        .logout {
            color: #ff6666;
            text-decoration: none;
            padding: 8px 16px;
            border: 1px solid #ff6666;
            border-radius: 5px;
        }
        .main {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .canvas-container {
            flex: 2;
            min-width: 500px;
            background: #111;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #00ff41;
        }
        .canvas-container h3 {
            color: #00ff41;
            margin-bottom: 15px;
        }
        canvas {
            width: 100%;
            height: auto;
            border: 1px solid #333;
            cursor: text;
            background: #fff;
        }
        .instructions {
            flex: 1;
            min-width: 250px;
            background: #111;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #00ff41;
        }
        .instructions h3 {
            color: #ff00ff;
            margin-bottom: 15px;
        }
        .instructions p {
            color: #0f0;
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.6;
        }
        .instructions ul {
            color: #888;
            margin-left: 20px;
            font-size: 13px;
        }
        .instructions li {
            margin: 8px 0;
        }
        button {
            background: #00ff41;
            color: #000;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
        }
        button:hover {
            background: #ff00ff;
            color: #fff;
        }
        .status {
            background: #1a1a2e;
            padding: 10px;
            border-radius: 5px;
            margin-top: 15px;
            font-size: 12px;
            color: #00ff41;
            text-align: center;
        }
        .field-list {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #333;
        }
        .field-list h4 {
            color: #ff00ff;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .field-list p {
            font-size: 11px;
            color: #666;
            margin: 3px 0;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div class="logo"><h1>📷 MONEYMOM | CLICK TO EDIT PERMIT</h1></div>
        <a href="#" class="logout" onclick="alert('Session ended');">🚪 EXIT</a>
    </div>
    
    <div class="main">
        <div class="canvas-container">
            <h3>📄 CLICK ON ANY TEXT TO EDIT</h3>
            <canvas id="permitCanvas" width="1011" height="638" style="width:100%; height:auto; border:1px solid #00ff41;"></canvas>
            <div class="status" id="status">✅ Click on any text field on the permit to edit it directly</div>
        </div>
        
        <div class="instructions">
            <h3>✏️ HOW TO USE</h3>
            <p>1️⃣ <strong>Click directly on any text</strong> in the permit image<br>
            2️⃣ A cursor will appear — <strong>type your new text</strong><br>
            3️⃣ Press <strong>ENTER</strong> to save, or <strong>ESC</strong> to cancel<br>
            4️⃣ Click <strong>SAVE & DOWNLOAD</strong> when done</p>
            
            <div class="field-list">
                <h4>📋 EDITABLE FIELDS</h4>
                <p>• SURNAME (NOM) — top left area</p>
                <p>• GIVEN NAMES (PRENOM) — below surname</p>
                <p>• DATE OF BIRTH — third line</p>
                <p>• PLACE OF BIRTH — next to date</p>
                <p>• RESIDENCE — fourth line</p>
                <p>• LICENSE NUMBER — fifth line</p>
                <p>• ISSUE DATE — bottom left</p>
                <p>• EXPIRY DATE — bottom right</p>
                <p>• CATEGORIES — bottom center</p>
                <p>• CARD NUMBER — bottom left</p>
            </div>
            
            <button id="saveBtn">💾 SAVE & DOWNLOAD AS PNG</button>
        </div>
    </div>
</div>

<script>
    // Load the scanned permit image
    // IMPORTANT: Replace this with your actual scanned permit image
    // You can either put the image file in the same folder and load it,
    // OR paste a base64 image here
    
    // Method 1: Load from file (put your permit.jpg in same folder)
    const imageSrc = prompt("Enter the path to your scanned permit image (or type 'base64' to paste base64):", "permit.jpg");
    
    let img = new Image();
    let canvas = document.getElementById('permitCanvas');
    let ctx = canvas.getContext('2d');
    let currentEditing = null;
    let editInput = null;
    
    // Predefined text areas (pixel coordinates for your specific scan)
    // YOU MUST ADJUST THESE COORDINATES TO MATCH YOUR SCAN
    const textAreas = {
        surname: { x: 210, y: 107, w: 250, h: 22, label: 'SURNAME', default: 'SEZERANO' },
        givenNames: { x: 210, y: 134, w: 250, h: 22, label: 'GIVEN NAMES', default: 'JEAN' },
        dob: { x: 210, y: 162, w: 120, h: 20, label: 'DATE OF BIRTH', default: '01-01-1986' },
        pob: { x: 340, y: 162, w: 220, h: 20, label: 'PLACE OF BIRTH', default: 'KAMENGE BUJUMBURA' },
        residence: { x: 210, y: 191, w: 300, h: 22, label: 'RESIDENCE', default: 'MUTIMBUZI, GAHAHE' },
        licenseNumber: { x: 210, y: 222, w: 250, h: 22, label: 'LICENSE NUMBER', default: 'PNC0139839' },
        issueDate: { x: 200, y: 320, w: 120, h: 20, label: 'ISSUE DATE', default: '13-09-2016' },
        issuePlace: { x: 580, y: 320, w: 180, h: 20, label: 'PLACE OF ISSUE', default: 'BUJUMBURA' },
        categories: { x: 160, y: 348, w: 120, h: 22, label: 'CATEGORIES', default: 'A, B' },
        expiryDate: { x: 580, y: 348, w: 120, h: 20, label: 'EXPIRY DATE', default: '12-09-2026' },
        cardNumber: { x: 160, y: 376, w: 180, h: 20, label: 'CARD NUMBER', default: 'DL0006875' }
    };
    
    // Store current text values
    let currentValues = {};
    for (let key in textAreas) {
        currentValues[key] = textAreas[key].default;
    }
    
    // Function to draw everything on canvas
    function drawCanvas() {
        if (!img.complete || img.naturalWidth === 0) return;
        
        // Draw the image
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Draw text from currentValues
        ctx.font = 'bold 16px "Courier New", monospace';
        ctx.fillStyle = '#000000';
        
        for (let key in textAreas) {
            const area = textAreas[key];
            ctx.fillText(currentValues[key].toUpperCase(), area.x, area.y + 15);
        }
        
        // Draw a subtle highlight box around the currently editing field
        if (currentEditing) {
            const area = textAreas[currentEditing];
            ctx.save();
            ctx.strokeStyle = '#ff00ff';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(area.x - 2, area.y, area.w + 4, area.h);
            ctx.restore();
        }
    }
    
    // Function to check which text area was clicked
    function getTextAreaFromClick(mouseX, mouseY) {
        for (let key in textAreas) {
            const area = textAreas[key];
            if (mouseX >= area.x && mouseX <= area.x + area.w &&
                mouseY >= area.y && mouseY <= area.y + area.h) {
                return key;
            }
        }
        return null;
    }
    
    // Create input overlay for editing
    function startEditing(fieldKey) {
        if (editInput) {
            document.body.removeChild(editInput);
            editInput = null;
        }
        
        currentEditing = fieldKey;
        const area = textAreas[fieldKey];
        
        // Get canvas position on screen
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        const screenX = rect.left + (area.x / scaleX);
        const screenY = rect.top + (area.y / scaleY);
        const screenW = area.w / scaleX;
        const screenH = area.h / scaleY;
        
        // Create input element
        editInput = document.createElement('input');
        editInput.type = 'text';
        editInput.value = currentValues[fieldKey];
        editInput.style.position = 'fixed';
        editInput.style.left = screenX + 'px';
        editInput.style.top = screenY + 'px';
        editInput.style.width = screenW + 'px';
        editInput.style.height = screenH + 'px';
        editInput.style.fontSize = '16px';
        editInput.style.fontWeight = 'bold';
        editInput.style.fontFamily = '"Courier New", monospace';
        editInput.style.backgroundColor = '#fff';
        editInput.style.color = '#000';
        editInput.style.border = '2px solid #ff00ff';
        editInput.style.outline = 'none';
        editInput.style.padding = '2px 4px';
        editInput.style.zIndex = '1000';
        
        editInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                // Save and finish editing
                currentValues[fieldKey] = editInput.value;
                drawCanvas();
                document.body.removeChild(editInput);
                editInput = null;
                currentEditing = null;
                document.getElementById('status').innerHTML = `✅ Saved "${editInput.value}" to ${area.label}`;
            } else if (e.key === 'Escape') {
                // Cancel editing
                document.body.removeChild(editInput);
                editInput = null;
                currentEditing = null;
                document.getElementById('status').innerHTML = `❌ Editing cancelled`;
            }
        });
        
        editInput.addEventListener('blur', function() {
            // Auto-save on blur (optional)
            if (editInput) {
                currentValues[fieldKey] = editInput.value;
                drawCanvas();
                document.body.removeChild(editInput);
                editInput = null;
                currentEditing = null;
            }
        });
        
        document.body.appendChild(editInput);
        editInput.focus();
        editInput.select();
        
        document.getElementById('status').innerHTML = `✏️ Editing ${area.label} — type new text, press ENTER to save`;
    }
    
    // Handle canvas click
    canvas.addEventListener('click', function(e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;
        
        const field = getTextAreaFromClick(mouseX, mouseY);
        if (field) {
            startEditing(field);
        } else {
            document.getElementById('status').innerHTML = '⚠️ Click directly on the text you want to edit (Surname, Name, Date, etc.)';
            setTimeout(() => {
                if (!currentEditing) {
                    document.getElementById('status').innerHTML = '✅ Click on any text field on the permit to edit it directly';
                }
            }, 2000);
        }
    });
    
    // Save and download
    document.getElementById('saveBtn').addEventListener('click', function() {
        // Make sure all text is drawn
        drawCanvas();
        
        // Download as PNG
        const link = document.createElement('a');
        link.download = 'edited_permit.png';
        link.href = canvas.toDataURL();
        link.click();
        
        document.getElementById('status').innerHTML = '💾 Permit saved and downloaded!';
        setTimeout(() => {
            document.getElementById('status').innerHTML = '✅ Click on any text field on the permit to edit it directly';
        }, 3000);
    });
    
    // Load image
    if (imageSrc === 'base64') {
        const b64 = prompt('Paste your base64 image data:');
        img.src = b64;
    } else {
        img.src = imageSrc;
    }
    
    img.onload = function() {
        // Resize canvas to match image dimensions
        canvas.width = img.width;
        canvas.height = img.height;
        
        // Update text area coordinates based on actual image size
        const scaleX = img.width / 1011;  // Original reference width
        const scaleY = img.height / 638;  // Original reference height
        
        for (let key in textAreas) {
            textAreas[key].x = Math.round(textAreas[key].x * scaleX);
            textAreas[key].y = Math.round(textAreas[key].y * scaleY);
            textAreas[key].w = Math.round(textAreas[key].w * scaleX);
            textAreas[key].h = Math.round(textAreas[key].h * scaleY);
        }
        
        drawCanvas();
        document.getElementById('status').innerHTML = '✅ Image loaded. Click on any text to edit it directly.';
    };
    
    img.onerror = function() {
        document.getElementById('status').innerHTML = '❌ Error loading image. Make sure the file path is correct.';
        alert('Error loading image. Please refresh and enter a valid image path.\n\nExample: permit.jpg (place the file in the same folder)');
    };
</script>
</body>
</html>
