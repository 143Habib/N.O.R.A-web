import os
import json
import hashlib
import subprocess
import webbrowser
import psutil
import pyautogui
import base64
import iocleart
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from PIL import Image

# Optional: import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "NORA_SECRET_KEY_CHANGE_THIS"

# ========== CONFIG ==========
USERS_FILE = "users.json"
CHAT_FILE_TEMPLATE = "chat_{username}.json"
# We use Llama3 for text, Llava for images
OLLAMA_TEXT_MODEL = "llama3:8b" 
OLLAMA_VISION_MODEL = "llava" 

# ========== Utilities ==========
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def safe_save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def execute_system_command(cmd_lower):
    if "notepad" in cmd_lower:
        subprocess.Popen("notepad")
        return "Opening Notepad.", None
    if "calculator" in cmd_lower or "calc" in cmd_lower:
        subprocess.Popen("calc")
        return "Opening Calculator.", None
    if "camera" in cmd_lower:
        subprocess.run("start microsoft.windows.camera:", shell=True)
        return "Opening Camera.", None
    if "word" in cmd_lower and "open" in cmd_lower:
        subprocess.Popen("start winword", shell=True)
        return "Opening Microsoft Word.", None
    if "excel" in cmd_lower and "open" in cmd_lower:
        subprocess.Popen("start excel", shell=True)
        return "Opening Microsoft Excel.", None
    if "task manager" in cmd_lower:
        subprocess.Popen("taskmgr")
        return "Opening Task Manager.", None
    if "control panel" in cmd_lower:
        subprocess.Popen("control")
        return "Opening Control Panel.", None
    if "youtube" in cmd_lower and "open" in cmd_lower:
        return "Opening YouTube.", {"type": "open_url", "url": "https://www.youtube.com"}
    if "google" in cmd_lower and "open" in cmd_lower:
        return "Opening Google.", {"type": "open_url", "url": "https://www.google.com"}
    if "screenshot" in cmd_lower or "snap" in cmd_lower:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{ts}.png"
        pyautogui.screenshot(filename)
        return f"Screenshot saved as {filename}.", None
    if "battery" in cmd_lower:
        try:
            battery = psutil.sensors_battery()
            if battery:
                plugged = "plugged in" if battery.power_plugged else "on battery"
                return f"Battery is at {battery.percent}% and {plugged}.", None
            return "Battery information not available.", None
        except: return "Could not access battery sensors.", None
    if "time" in cmd_lower:
        return f"The current time is {datetime.now().strftime('%I:%M %p')}.", None
    return None, None

# ========== Routes ==========
@app.route('/')
def index():
    if 'username' in session: return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        users = safe_load_json(USERS_FILE, {})
        user = data.get('username')
        if user in users and users[user]["password"] == hash_password(data.get('password')):
            session['username'] = user
            session['name'] = users[user]['name']
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Invalid credentials"})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        users = safe_load_json(USERS_FILE, {})
        if data.get('username') in users:
            return jsonify({"status": "error", "message": "Username exists"})
        users[data.get('username')] = {
            "name": data.get('name'),
            "email": data.get('email'),
            "phone": data.get('phone'),
            "password": hash_password(data.get('password')),
            "created_at": now_ts()
        }
        safe_save_json(USERS_FILE, users)
        return jsonify({"status": "success"})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'], name=session['name'])

# ========== API Routes ==========
@app.route('/api/get_sessions', methods=['GET'])
def get_sessions():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = safe_load_json(CHAT_FILE_TEMPLATE.format(username=session['username']), {"sessions": []})
    return jsonify(data)

@app.route('/api/new_session', methods=['POST'])
def new_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    new_sess = {
        "session_id": datetime.now().strftime("%Y%m%d%H%M%S"), 
        "start_time": now_ts(), 
        "title": "New Operation", 
        "messages": []
    }
    data["sessions"].append(new_sess)
    safe_save_json(filename, data)
    return jsonify(new_sess)

@app.route('/api/rename_session', methods=['POST'])
def rename_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    sess_id = req.get('session_id')
    new_title = req.get('title')
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    for s in data["sessions"]:
        if s["session_id"] == sess_id:
            s["title"] = new_title
            safe_save_json(filename, data)
            return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/delete_session', methods=['POST'])
def delete_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    sess_id = req.get('session_id')
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    original = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s["session_id"] != sess_id]
    if len(data["sessions"]) < original:
        safe_save_json(filename, data)
        return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/clear_session', methods=['POST'])
def clear_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    sess_id = req.get('session_id')
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    for s in data["sessions"]:
        if s["session_id"] == sess_id:
            s["messages"] = []
            safe_save_json(filename, data)
            return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/process_message', methods=['POST'])
def process_message():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    # Handle Form Data (File + Text)
    user_msg = request.form.get('message', '')
    session_id = request.form.get('session_id')
    uploaded_file = request.files.get('file')
    
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    
    current_sess = next((s for s in data["sessions"] if s["session_id"] == session_id), None)
    if not current_sess: return jsonify({"error": "Session not found"}), 404

    # Save User Msg
    display_content = user_msg
    if uploaded_file:
        display_content += f" [Attached: {uploaded_file.filename}]"
    
    current_sess["messages"].append({"timestamp": now_ts(), "role": "user", "content": display_content})
    
    msg_lower = user_msg.lower()
    response_text = ""
    action = None
    
    # 1. System Commands (Text Only)
    if not uploaded_file:
        sys_resp, sys_action = execute_system_command(msg_lower)
        if sys_resp:
            response_text = sys_resp
            action = sys_action
            
    # 2. AI Processing (Text OR Vision)
    if not response_text:
        if OLLAMA_AVAILABLE:
            try:
                # --- CASE A: IMAGE UPLOAD (VISION) ---
                if uploaded_file and uploaded_file.mimetype.startswith('image/'):
                    # Convert image to bytes for Ollama
                    image_bytes = uploaded_file.read()
                    
                    res = ollama.generate(
                        model=OLLAMA_VISION_MODEL,
                        prompt=user_msg if user_msg else "Describe this image.",
                        images=[image_bytes]
                    )
                    response_text = res['response']
                
                # --- CASE B: TEXT FILE UPLOAD ---
                elif uploaded_file and uploaded_file.mimetype.startswith('text/'):
                    file_content = uploaded_file.read().decode('utf-8')
                    full_prompt = f"User uploaded a file:\n{file_content}\n\nInstruction: {user_msg}"
                    
                    res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=[
                        {"role": "system", "content": "You are NORA. Analyze the provided file content."},
                        {"role": "user", "content": full_prompt}
                    ])
                    response_text = res['message']['content']

                # --- CASE C: NORMAL TEXT CHAT ---
                else:
                    res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=[
                        {"role": "system", "content": "You are NORA. Do not use asterisks. Be concise."},
                        {"role": "user", "content": user_msg}
                    ])
                    response_text = res['message']['content']

            except Exception as e:
                response_text = f"AI Error: {str(e)}"
                if "pull" in str(e) and uploaded_file:
                    response_text += " (Please run 'ollama pull llava' in terminal for image support)"
        else:
            response_text = "System offline. AI module not detected."

    current_sess["messages"].append({"timestamp": now_ts(), "role": "assistant", "content": response_text})
    safe_save_json(filename, data)

    return jsonify({
        "response": response_text,
        "timestamp": now_ts(),
        "action": action
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
