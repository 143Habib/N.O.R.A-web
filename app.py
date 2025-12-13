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

# Optional: import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False
    print("WARNING: Ollama library not found. AI features will be limited.")

app = Flask(__name__)
app.secret_key = "NORA_SECRET_KEY_CHANGE_THIS"

# Standard SocketIO setup (Increased buffer for video frames)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, max_http_buffer_size=10000000)

# ========== CONFIGURATION ==========
USERS_FILE = "users.json"
CHAT_FILE_TEMPLATE = "chat_{username}.json"
OLLAMA_TEXT_MODEL = "llama3:8b" 
OLLAMA_VISION_MODEL = "llava" 

# ========== UTILITIES ==========
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_date():
    return datetime.now().strftime("%A, %B %d, %Y")

def safe_load_json(path, default):
    if not os.path.exists(path): return default
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def safe_save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False)

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ========== WEB SEARCH LOGIC ==========
def perform_web_search(query):
    print(f"DEBUG: Searching Web for: {query}") 
    try:
        results = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        
        if not results: return None
        
        context_str = f"--- REAL-TIME SEARCH RESULTS ({get_current_date()}) ---\n"
        for i, r in enumerate(results):
            context_str += f"Source {i+1}: {r.get('title', 'No Title')}\n"
            context_str += f"Content: {r.get('body', 'No Content')}\n"
            context_str += f"Link: {r.get('href', '#')}\n\n"
        context_str += "--- END OF SEARCH RESULTS ---\n"
        return context_str

    except Exception as e:
        print(f"DEBUG: Search FAILED with error: {e}")
        return None

# ========== SYSTEM COMMAND LOGIC ==========
def execute_system_command(cmd_lower):
    # These commands run on the HOST machine (Server/PC)
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
        try:
            pyautogui.screenshot(filename)
            return f"Screenshot saved as {filename}.", None
        except Exception:
            return "Failed to take screenshot (display missing?).", None
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

# ========== ROUTES: AUTHENTICATION ==========
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
        hashed_pw = hash_password(passwd)

        if user == "admin":
            if "admin" in users:
                if users["admin"]["password"] == hashed_pw:
                    session['username'] = "admin"
                    session['name'] = users["admin"]["name"]
                    return jsonify({"status": "success", "role": "admin"})
            elif passwd == "admin123":
                session['username'] = "admin"
                session['name'] = "SYSTEM OVERLORD"
                return jsonify({"status": "success", "role": "admin"})
        
        if user in users and users[user]["password"] == hashed_pw:
            session['username'] = user
            session['name'] = users[user]['name']
            return jsonify({"status": "success", "role": "user"})
            
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

# ========== ROUTES: PROFILE ==========
@app.route('/profile')
def profile():
    if 'username' not in session: return redirect(url_for('login'))
    users = safe_load_json(USERS_FILE, {})
    current_user = session['username']
    user_data = users.get(current_user, {"name": session.get('name', 'Admin'), "email": "", "phone": ""})
    return render_template('profile.html', user=current_user, data=user_data, is_admin=(current_user=='admin'))

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session: return jsonify({"status": "error", "message": "Unauthorized"}), 401
    data = request.get_json()
    users = safe_load_json(USERS_FILE, {})
    current_user = session['username']
    new_password = data.get('password')
    
    if current_user == 'admin':
        if 'admin' not in users: users['admin'] = {"name": "SYSTEM OVERLORD", "email": "", "phone": "", "created_at": now_ts()}
        if new_password:
            users['admin']['password'] = hash_password(new_password)
            safe_save_json(USERS_FILE, users)
            return jsonify({"status": "success", "message": "Admin password updated."})
        else: return jsonify({"status": "error", "message": "Admin can only update password."})

    if current_user in users:
        users[current_user]['name'] = data.get('name', users[current_user]['name'])
        users[current_user]['email'] = data.get('email', users[current_user]['email'])
        users[current_user]['phone'] = data.get('phone', users[current_user]['phone'])
        session['name'] = users[current_user]['name']
        if new_password: users[current_user]['password'] = hash_password(new_password)
        safe_save_json(USERS_FILE, users)
        return jsonify({"status": "success", "message": "Profile updated successfully."})
    return jsonify({"status": "error", "message": "User not found."})

# ========== ROUTES: VIEWS ==========
@app.route('/chat')
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    if session['username'] == 'admin': return redirect(url_for('admin_dashboard'))
    return render_template('chat.html', username=session['username'], name=session['name'])

@app.route('/admin')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin': return redirect(url_for('login'))
    users_db = safe_load_json(USERS_FILE, {})
    user_list = [{"username": u, "name": v['name']} for u, v in users_db.items() if u != 'admin']
    return render_template('admin.html', name=session['name'], users=user_list)

# ========== ROUTES: SESSION API ==========
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
    new_sess = {"session_id": datetime.now().strftime("%Y%m%d%H%M%S"), "start_time": now_ts(), "title": "New Operation", "messages": []}
    data["sessions"].append(new_sess)
    safe_save_json(filename, data)
    socketio.emit('refresh_sessions', room=session['username'])
    return jsonify(new_sess)

@app.route('/api/rename_session', methods=['POST'])
def rename_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    for s in data["sessions"]:
        if s["session_id"] == req.get('session_id'):
            s["title"] = req.get('title')
            safe_save_json(filename, data)
            socketio.emit('refresh_sessions', room=session['username'])
            return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/delete_session', methods=['POST'])
def delete_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    original = len(data["sessions"])
    data["sessions"] = [s for s in data["sessions"] if s["session_id"] != req.get('session_id')]
    if len(data["sessions"]) < original:
        safe_save_json(filename, data)
        socketio.emit('refresh_sessions', room=session['username'])
        return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/clear_session', methods=['POST'])
def clear_session():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    req = request.get_json()
    filename = CHAT_FILE_TEMPLATE.format(username=session['username'])
    data = safe_load_json(filename, {"sessions": []})
    for s in data["sessions"]:
        if s["session_id"] == req.get('session_id'):
            s["messages"] = []
            safe_save_json(filename, data)
            socketio.emit('sync_clear', {'session_id': req.get('session_id')}, room=session['username'])
            return jsonify({"status": "success"})
    return jsonify({"error": "Session not found"}), 404

# ========== CORE: MESSAGE PROCESSING ==========
@app.route('/api/process_message', methods=['POST'])
def process_message():
    if 'username' not in session: return jsonify({"error": "Unauthorized"}), 401
    
    user_msg = request.form.get('message', '')
    session_id = request.form.get('session_id')
    use_web = request.form.get('use_web') == 'true' 
    uploaded_file = request.files.get('file')
    tab_id = request.form.get('tab_id', 'unknown')
    current_user = session['username']
    
    filename = CHAT_FILE_TEMPLATE.format(username=current_user)
    data = safe_load_json(filename, {"sessions": []})
    
    current_sess = next((s for s in data["sessions"] if s["session_id"] == session_id), None)
    if not current_sess: return jsonify({"error": "Session not found"}), 404

    display_content = user_msg
    if uploaded_file: display_content += f" [Attached: {uploaded_file.filename}]"
    if use_web: display_content += " [WEB SEARCH]"
    
    current_sess["messages"].append({"timestamp": now_ts(), "role": "user", "content": display_content})
    safe_save_json(filename, data)

    socketio.emit('sync_message', {
        'session_id': session_id, 'role': 'user', 'sender': 'You', 'content': display_content, 'origin_tab': tab_id 
    }, room=current_user)
    
    socketio.emit('admin_feed_update', {
        'user': current_user, 'role': 'user', 'content': display_content, 'timestamp': now_ts()
    }, room='admin_monitor')
    
    msg_lower = user_msg.lower()
    response_text = ""
    action = None
    
    if not uploaded_file:
        sys_resp, sys_action = execute_system_command(msg_lower)
        if sys_resp:
            response_text = sys_resp
            action = sys_action
            
    if not response_text:
        if OLLAMA_AVAILABLE:
            try:
                if uploaded_file and uploaded_file.mimetype.startswith('image/'):
                    res = ollama.generate(model=OLLAMA_VISION_MODEL, prompt=user_msg if user_msg else "Describe this image.", images=[uploaded_file.read()])
                    response_text = res['response']
                elif uploaded_file and uploaded_file.mimetype.startswith('text/'):
                    res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=[
                        {"role": "system", "content": "Analyze the file provided."},
                        {"role": "user", "content": f"File:\n{uploaded_file.read().decode('utf-8')}\n\nTask: {user_msg}"}
                    ])
                    response_text = res['message']['content']
                elif use_web:
                    search_context = perform_web_search(user_msg)
                    current_date = get_current_date()
                    if search_context:
                        system_prompt = f"You are NORA. Date: {current_date}. Use these SEARCH RESULTS:\n{search_context}"
                    else:
                        system_prompt = f"You are NORA. Date: {current_date}. Search failed."
                    context_messages = [{"role": "system", "content": system_prompt}]
                    history = current_sess["messages"][-5:] 
                    for msg in history: context_messages.append({"role": msg["role"], "content": msg["content"].replace("[WEB SEARCH]", "").strip()})
                    res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=context_messages)
                    response_text = res['message']['content']
                else:
                    system_prompt = f"You are NORA. Date: {get_current_date()}."
                    context_messages = [{"role": "system", "content": system_prompt}]
                    history = current_sess["messages"][-20:]
                    for msg in history: context_messages.append({"role": msg["role"], "content": msg["content"]})
                    res = ollama.chat(model=OLLAMA_TEXT_MODEL, messages=context_messages)
                    response_text = res['message']['content']
            except Exception as e: response_text = f"System Error: {str(e)}"
        else: response_text = "System offline. AI module not detected."

    current_sess["messages"].append({"timestamp": now_ts(), "role": "assistant", "content": response_text})
    safe_save_json(filename, data)

    socketio.emit('sync_message', {
        'session_id': session_id, 'role': 'assistant', 'sender': 'NORA', 'content': response_text, 'origin_tab': 'server', 'action': action
    }, room=current_user)

    socketio.emit('admin_feed_update', {
        'user': current_user, 'role': 'assistant', 'content': response_text, 'timestamp': now_ts()
    }, room='admin_monitor')

    return jsonify({"response": response_text, "timestamp": now_ts(), "action": action})

# ========== SOCKETIO EVENTS: SURVEILLANCE & MONITORING ==========
@socketio.on('connect')
def handle_connect():
    if 'username' in session:
        user = session['username']
        if user == 'admin':
            join_room('admin_monitor')
            print(">>> GOD MODE: Admin connected.")
        else:
            join_room(user)
            print(f">>> TARGET CONNECTED: {user}")
            socketio.emit('user_status_change', {'user': user, 'status': 'online'}, room='admin_monitor')

@socketio.on('disconnect')
def handle_disconnect():
    if 'username' in session:
        user = session['username']
        socketio.emit('user_status_change', {'user': user, 'status': 'offline'}, room='admin_monitor')


@socketio.on('admin_trigger_surveillance')
def admin_trigger(data):
    target = data.get('target_user')
    print(f"DEBUG: Admin requesting {data.get('type')} from {target}")
    socketio.emit('remote_command', {'command': 'start_stream', 'type': data.get('type')}, room=target)


@socketio.on('stream_frame')
def handle_stream_frame(data):
    socketio.emit('admin_receive_stream', data, room='admin_monitor')

@socketio.on('user_activity_log')
def handle_activity(data):
    socketio.emit('admin_receive_log', data, room='admin_monitor')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
