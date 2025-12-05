import os
import json
import hashlib
import subprocess
import psutil
import pyautogui
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room 
from duckduckgo_search import DDGS 

try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False

app = Flask(__name__)
app.secret_key = "NORA_SECRET_KEY_CHANGE_THIS"
socketio = SocketIO(app, cors_allowed_origins="*")

# ========== CONFIG ==========
USERS_FILE = "users.json"
CHAT_FILE_TEMPLATE = "chat_{username}.json"
OLLAMA_TEXT_MODEL = "llama3:8b" 
OLLAMA_VISION_MODEL = "llava" 

# ========== UTILS ==========
def now_ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def get_current_date(): return datetime.now().strftime("%A, %B %d, %Y")
def safe_load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default
def safe_save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False)
def hash_password(password): return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ========== COMMANDS & SEARCH ==========
# (Keep perform_web_search and execute_system_command exactly as they were in previous code)
# ... [Paste previous perform_web_search and execute_system_command functions here] ...
# For brevity in this snippet, I assume you kept them. 
# Make sure execute_system_command is present!

def execute_system_command(cmd_lower):
    # Minimal example if you need to copy-paste again:
    if "calc" in cmd_lower:
        subprocess.Popen("calc")
        return "Opening Calculator.", None
    # ... Add other commands ...
    return None, None

def perform_web_search(query):
    # ... Paste previous logic ...
    return None

# ========== ROUTES ==========
@app.route('/')
def index():
    if 'username' in session: 
        if session['username'] == 'admin': return redirect(url_for('admin_dashboard'))
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        users = safe_load_json(USERS_FILE, {})
        user = data.get('username')
        passwd = data.get('password')
        
        # Check regular users
        if user in users and users[user]["password"] == hash_password(passwd):
            session['username'] = user
            session['name'] = users[user]['name']
            return jsonify({"status": "success", "role": "user"})
            
        # Check HARDCODED ADMIN (For safety, you should register this properly later)
        if user == "admin" and passwd == "admin123": 
            session['username'] = "admin"
            session['name'] = "SYSTEM OVERLORD"
            return jsonify({"status": "success", "role": "admin"})

        return jsonify({"status": "error", "message": "Invalid credentials"})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        users = safe_load_json(USERS_FILE, {})
        if data.get('username') in users or data.get('username') == 'admin':
            return jsonify({"status": "error", "message": "Username taken"})
        users[data.get('username')] = {
            "name": data.get('name'), "email": data.get('email'),
            "phone": data.get('phone'), "password": hash_password(data.get('password')),
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
    if session['username'] == 'admin': return redirect(url_for('admin_dashboard'))
    return render_template('chat.html', username=session['username'], name=session['name'])

# === NEW ADMIN ROUTE ===
@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    # Get list of all registered users for the sidebar
    users_db = safe_load_json(USERS_FILE, {})
    user_list = [{"username": u, "name": v['name']} for u, v in users_db.items()]
    
    return render_template('admin.html', name=session['name'], users=user_list)


# ========== API ==========
# ... (Keep get_sessions, new_session, rename_session, delete_session, clear_session) ...
# ... (Paste them from previous code) ...

@app.route('/api/get_sessions', methods=['GET'])
def get_sessions():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = safe_load_json(CHAT_FILE_TEMPLATE.format(username=session['username']), {"sessions": []})
    return jsonify(data)

@app.route('/api/new_session', methods=['POST'])
def new_session():
    # Standard logic
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    new_sess = {"session_id": datetime.now().strftime("%Y%m%d%H%M%S"), "start_time": now_ts(), "title": "New Operation", "messages": []}
    data["sessions"].append(new_sess)
    safe_save_json(filename, data)
    socketio.emit('refresh_sessions', room=session['username'])
    return jsonify(new_sess)

# ... (Assume clear/rename/delete are here) ...

@app.route('/api/process_message', methods=['POST'])
def process_message():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    user_msg = request.form.get('message', '')
    session_id = request.form.get('session_id')
    use_web = request.form.get('use_web') == 'true'
    uploaded_file = request.files.get('file')
    tab_id = request.form.get('tab_id', 'unknown')
    current_user = session['username']

    # Log Logic (same as before)
    filename = CHAT_FILE_TEMPLATE.format(username=current_user)
    data = safe_load_json(filename, {"sessions": []})
    current_sess = next((s for s in data["sessions"] if s["session_id"] == session_id), None)
    if not current_sess: return jsonify({"error": "Session not found"}), 404

    display_content = user_msg
    if uploaded_file: display_content += f" [Attached: {uploaded_file.filename}]"
    if use_web: display_content += " [WEB SEARCH]"
    
    # 1. Save & Sync to USER
    current_sess["messages"].append({"timestamp": now_ts(), "role": "user", "content": display_content})
    safe_save_json(filename, data)
    
    socketio.emit('sync_message', {
        'session_id': session_id, 'role': 'user', 'sender': 'You',
        'content': display_content, 'origin_tab': tab_id
    }, room=current_user)

    # 2. BROADCAST TO ADMIN
    socketio.emit('admin_feed_update', {
        'user': current_user,
        'role': 'user',
        'content': display_content,
        'timestamp': now_ts()
    }, room='admin_monitor') # Send to admin room

    # AI Logic
    response_text = ""
    action = None
    msg_lower = user_msg.lower()

    if not uploaded_file:
        sys_resp, sys_action = execute_system_command(msg_lower)
        if sys_resp: response_text, action = sys_resp, sys_action
            
    if not response_text:
        # ... (Ollama logic here, same as before) ...
        response_text = "Processing..." # Placeholder if no AI
        if OLLAMA_AVAILABLE:
            try:
                # Simple example for brevity
                res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=[{'role':'user', 'content': user_msg}])
                response_text = res['message']['content']
            except: response_text = "AI Error."

    # 3. Save AI & Sync to USER
    current_sess["messages"].append({"timestamp": now_ts(), "role": "assistant", "content": response_text})
    safe_save_json(filename, data)
    
    socketio.emit('sync_message', {
        'session_id': session_id, 'role': 'assistant', 'sender': 'NORA',
        'content': response_text, 'origin_tab': 'server', 'action': action
    }, room=current_user)

    # 4. BROADCAST AI RESPONSE TO ADMIN
    socketio.emit('admin_feed_update', {
        'user': current_user,
        'role': 'assistant',
        'content': response_text,
        'timestamp': now_ts()
    }, room='admin_monitor')

    return jsonify({"response": response_text, "timestamp": now_ts(), "action": action})

# ========== SOCKETS ==========
@socketio.on('connect')
def handle_connect():
    if 'username' in session:
        # Admin joins the "God Mode" room
        if session['username'] == 'admin':
            join_room('admin_monitor')
            print("!!! ADMIN CONNECTED TO MONITORING NETWORK !!!")
        else:
            # Regular users join their private room
            join_room(session['username'])
            print(f"User {session['username']} connected.")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
