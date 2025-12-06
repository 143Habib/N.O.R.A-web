// ========== GLOBALS & SOCKET ==========
const tabId = Math.random().toString(36).substr(2, 9); // Unique ID for this browser tab
const socket = io(); // Connect to WebSocket

socket.on('connect', () => {
    console.log("Connected to Neural Sync. Tab ID:", tabId);
});

// LISTEN: Receive messages from other devices (or server)
socket.on('sync_message', (data) => {
    const currentSession = document.getElementById('currentSessionId').value;
    
    // Only update if looking at the same session
    if (data.session_id !== currentSession) return;

    if (data.role === 'user' && data.origin_tab !== tabId) {
        // User message from ANOTHER device
        appendMessageHTML(data.sender, data.content, data.role);
    }
    
    if (data.role === 'assistant') {
        if (!isWaitingForResponse) {
             typeEffectMessage(data.sender, data.content, data.role);
             if(data.action && data.action.type === 'open_url') window.open(data.action.url, '_blank');
        }
    }
});

socket.on('refresh_sessions', () => {
    loadSessions();
});

socket.on('sync_clear', (data) => {
    const currentSession = document.getElementById('currentSessionId').value;
    if (data.session_id === currentSession) {
        document.getElementById('chatBox').innerHTML = '';
    }
});

let isWaitingForResponse = false; // Flag to prevent double AI typing on the sender device

// ========== UI & ANIMATIONS ==========
function unlockSystem() {
    const splash = document.getElementById('splash-screen');
    if(splash) {
        document.body.classList.add('access-granted');
        setTimeout(() => { splash.style.display = 'none'; }, 1000);
    }
}
function toggleSidebar() { document.getElementById('sidebar').classList.toggle('closed'); }
function toggleTools() { document.getElementById('toolsSidebar').classList.toggle('closed'); }
function runQuickCmd(command) { document.getElementById('userInput').value = command; sendMessage(); }
function togglePasswordVisibility(id, btn) {
    const input = document.getElementById(id);
    const icon = btn.querySelector('i');
    if (input.type === "password") {
        input.type = "text"; icon.classList.remove('fa-eye'); icon.classList.add('fa-eye-slash'); icon.style.color = "var(--neon-red)";
    } else {
        input.type = "password"; icon.classList.remove('fa-eye-slash'); icon.classList.add('fa-eye'); icon.style.color = "var(--text-secondary)";
    }
}

// ========== MUTE, FILE & WEB ==========
let isMuted = false;
let isWebSearch = false;
function toggleMute() {
    isMuted = !isMuted;
    const btn = document.getElementById('muteBtn');
    if (isMuted) { btn.classList.add('muted-active'); window.speechSynthesis.cancel(); }
    else { btn.classList.remove('muted-active'); }
}
function toggleWebSearch() {
    isWebSearch = !isWebSearch;
    document.getElementById('webBtn').classList.toggle('active-web');
}
let selectedFile = null;
function handleFileSelect() {
    const fileInput = document.getElementById('fileInput');
    if(fileInput.files.length > 0) {
        selectedFile = fileInput.files[0];
        document.getElementById('fileName').innerHTML = `<i class="fa-regular fa-file"></i> ${selectedFile.name}`;
        document.getElementById('filePreviewArea').style.display = 'flex';
    }
}
function clearFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = "";
    document.getElementById('filePreviewArea').style.display = 'none';
}

// ========== AUTH ==========
async function doLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    if (!user || !pass) return;
    
    const res = await fetch('/login', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify({username: user, password: pass}) 
    });
    
    const data = await res.json();
    
    if(data.status === 'success') {
        // Redirect based on role
        if(data.role === 'admin') {
            window.location.href = '/admin';
        } else {
            window.location.href = '/chat';
        }
    } else { 
        document.getElementById('error').innerText = data.message; 
    }
}
async function doRegister() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    if(!name || !email || !user || !pass) return;
    const res = await fetch('/register', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username: user, password: pass, name: name, email: email, phone: phone}) });
    const data = await res.json();
    if(data.status === 'success') { alert("SUCCESS."); window.location.href = '/login'; }
    else { document.getElementById('error').innerText = data.message; }
}

async function updateProfile() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const pass = document.getElementById('password').value;
    
    const payload = {
        name: name,
        email: email,
        phone: phone,
        password: pass
    };
    
    const res = await fetch('/api/update_profile', {
        method: 'POST', 
        headers: {'Content-Type': 'application/json'}, 
        body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    
    if(data.status === 'success') {
        alert(data.message);
        document.getElementById('password').value = ""; // Clear password field
        document.getElementById('error').innerText = "";
    } else {
        document.getElementById('error').innerText = data.message;
    }
}

function logout() { window.location.href = '/logout'; }

// ========== CHAT ENGINE ==========
let allSessions = [];
if (window.location.pathname === '/chat') {
    loadSessions(); setupVoice(); window.speechSynthesis.getVoices();
    document.addEventListener('click', (e) => { if (!e.target.closest('.session-item')) document.querySelectorAll('.session-dropdown').forEach(el => el.classList.remove('show')); });
}
async function loadSessions() {
    const res = await fetch('/api/get_sessions');
    const data = await res.json();
    allSessions = data.sessions;
    const list = document.getElementById('sessionList');
    list.innerHTML = '';
    
    [...allSessions].reverse().forEach(s => {
        const div = document.createElement('div');
        div.className = 'session-item'; 
        div.id = `sess-${s.session_id}`;
        div.innerHTML = `
            <div onclick="loadChat('${s.session_id}')" style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                <strong>${s.title||s.start_time}</strong>
            </div>
            <div class="session-menu-btn" onclick="toggleSessionMenu(event, '${s.session_id}')">
                <i class="fa-solid fa-ellipsis-vertical"></i>
            </div>
            <div class="session-dropdown" id="menu-${s.session_id}">
                <div class="dropdown-item" onclick="renameSession('${s.session_id}')">Rename</div>
                <div class="dropdown-item" onclick="deleteSession('${s.session_id}')">Delete</div>
            </div>
        `;
        list.appendChild(div);
    });

    if (allSessions.length > 0 && !document.getElementById('currentSessionId').value) {
        loadChat(allSessions[allSessions.length-1].session_id);
    } else if(allSessions.length === 0) {
        newSession();
    }
}
function toggleSessionMenu(event, sessId) { event.stopPropagation(); document.querySelectorAll('.session-dropdown').forEach(el => el.classList.remove('show')); document.getElementById(`menu-${sessId}`).classList.add('show'); }
async function renameSession(id) { const n = prompt("New Name:"); if(n) { await fetch('/api/rename_session', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session_id:id, title:n})}); loadSessions(); } }
async function deleteSession(id) { if(confirm("Delete?")) { await fetch('/api/delete_session', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session_id:id})}); location.reload(); } }
async function newSession() {
    const res = await fetch('/api/new_session', {method:'POST'}); const sess = await res.json();
    document.getElementById('currentSessionId').value = sess.session_id;
    document.getElementById('chatBox').innerHTML = '';
    const name = document.getElementById('userDisplayName').value.split(' ')[0];
    const greeting = `Hello ${name}, systems ready.`;
    await typeEffectMessage("NORA", greeting, "assistant");
    speak(greeting); loadSessions();
}
function loadChat(id) {
    const session = allSessions.find(s => s.session_id === id); if(!session) return;
    document.getElementById('currentSessionId').value = id;
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    document.getElementById(`sess-${id}`).classList.add('active');
    document.getElementById('chatBox').innerHTML = '';
    session.messages.forEach(m => appendMessageHTML(m.role==='user'?'You':'NORA', m.content, m.role));
}
async function clearChat() {
    const id = document.getElementById('currentSessionId').value;
    await fetch('/api/clear_session', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({session_id:id})});
    // Visual clear is handled by socket now, but we can clear locally too for speed
    document.getElementById('chatBox').innerHTML = '';
}
function handleEnter(e) { if(e.key === 'Enter') sendMessage(); }

// ========== MODIFIED SEND MESSAGE ==========
async function sendMessage() {
    const input = document.getElementById('userInput'); const text = input.value.trim(); const id = document.getElementById('currentSessionId').value;
    if(!text && !selectedFile) return;
    
    // 1. Show message locally immediately
    appendMessageHTML("You", text + (selectedFile?` [File: ${selectedFile.name}]`:'') + (isWebSearch?' 🌐':''), "user");
    input.value = '';
    
    isWaitingForResponse = true; // Block socket from doubling AI response

    try {
        const fd = new FormData(); 
        fd.append('message', text); 
        fd.append('session_id', id); 
        fd.append('use_web', isWebSearch);
        fd.append('tab_id', tabId); // Send our ID so server knows who sent it
        
        if(selectedFile) fd.append('file', selectedFile);
        
        const res = await fetch('/api/process_message', {method:'POST', body:fd});
        const data = await res.json();
        
        clearFile();
        
        // 2. Show AI Response locally (Type effect)
        await typeEffectMessage("NORA", data.response, "assistant");
        
        if(data.action && data.action.type === 'open_url') window.open(data.action.url, '_blank');
        speak(data.response);
        
    } catch(e) { 
        appendMessageHTML("System", "Error processing command.", "assistant"); 
    } finally {
        isWaitingForResponse = false; // Allow socket updates again
    }
}

function appendMessageHTML(sender, text, role) {
    const box = document.getElementById('chatBox');
    const clean = text.replace(/\*/g, '').replace(/\n/g, '<br>');
    box.insertAdjacentHTML('beforeend', `<div class="msg ${role}"><strong>${sender}</strong><br>${clean}</div>`);
    box.scrollTop = box.scrollHeight;
}
function typeEffectMessage(sender, text, role) {
    return new Promise(resolve => {
        const box = document.getElementById('chatBox');
        const d = document.createElement('div'); d.className = `msg ${role}`; d.innerHTML = `<strong>${sender}</strong><br><span></span>`;
        box.appendChild(d); const span = d.querySelector('span');
        let i = 0; const clean = text.replace(/\*/g, '');
        function type() { if(i < clean.length) { span.innerHTML += (clean[i]==='\n'?'<br>':clean[i]); i++; box.scrollTop = box.scrollHeight; setTimeout(type, 10); } else resolve(); }
        type();
    });
}
function setupVoice() {
    if('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition(); recognition.continuous = false;
        recognition.onstart = () => document.getElementById('micBtn').style.color = 'red';
        recognition.onend = () => document.getElementById('micBtn').style.color = '';
        recognition.onresult = (e) => { document.getElementById('userInput').value = e.results[0][0].transcript; sendMessage(); };
    }
}
function toggleVoice() { if(recognition) recognition.start(); }
function speak(text) {
    if(isMuted || !('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text.replace(/[*`]/g, ''));
    u.pitch = 1.1; u.rate = 1.1;
    const voices = window.speechSynthesis.getVoices();
    u.voice = voices.find(v => v.name.includes("Zira") || v.name.includes("Google US English")) || voices[0];
    window.speechSynthesis.speak(u);
}
