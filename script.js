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

// ========== MUTE LOGIC ==========
let isMuted = false;
function toggleMute() {
    isMuted = !isMuted;
    const btn = document.getElementById('muteBtn');
    if (isMuted) {
        btn.innerText = '🔇';
        btn.classList.add('muted-active');
        window.speechSynthesis.cancel();
    } else {
        btn.innerText = '🔊';
        btn.classList.remove('muted-active');
    }
}

// ========== FILE UPLOAD LOGIC ==========
let selectedFile = null;

function handleFileSelect() {
    const fileInput = document.getElementById('fileInput');
    if(fileInput.files.length > 0) {
        selectedFile = fileInput.files[0];
        document.getElementById('fileName').innerText = selectedFile.name;
        document.getElementById('filePreviewArea').style.display = 'flex';
    }
}

function clearFile() {
    selectedFile = null;
    document.getElementById('fileInput').value = "";
    document.getElementById('filePreviewArea').style.display = 'none';
}

// ========== AUTHENTICATION ==========
async function doLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('error');
    if (!user || !pass) { errorEl.innerText = "Credentials required."; return; }
    errorEl.innerText = "Authenticating...";
    try {
        const res = await fetch('/login', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: user, password: pass})
        });
        const data = await res.json();
        if(data.status === 'success') window.location.href = '/chat';
        else errorEl.innerText = "Access Denied: " + data.message;
    } catch (e) { errorEl.innerText = "Connection Failure."; }
}

async function doRegister() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const phone = document.getElementById('phone').value;
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    if(!name || !email || !user || !pass) {
        document.getElementById('error').innerText = "All fields except phone are required.";
        return;
    }
    const res = await fetch('/register', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: user, password: pass, name: name, email: email, phone: phone})
    });
    const data = await res.json();
    if(data.status === 'success') { alert("Identity Created. Proceed to Login."); window.location.href = '/login'; }
    else { document.getElementById('error').innerText = data.message; }
}
function logout() { window.location.href = '/logout'; }

// ========== CHAT ENGINE ==========
let allSessions = [];
let recognition = null;
let isTyping = false;

if (window.location.pathname === '/chat') {
    loadSessions();
    setupVoice();
    window.speechSynthesis.getVoices();
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.session-item')) {
            document.querySelectorAll('.session-dropdown').forEach(el => el.classList.remove('show'));
        }
    });
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
        const displayTitle = s.title ? s.title : `${s.start_time.split(' ')[0]} ${s.start_time.split(' ')[1]}`;
        div.innerHTML = `
            <div class="session-click-area" onclick="loadChat('${s.session_id}')">
                <strong>${displayTitle}</strong><br><small>${s.start_time.split(' ')[0]}</small>
            </div>
            <div class="session-menu-btn" onclick="toggleSessionMenu(event, '${s.session_id}')">⋮</div>
            <div class="session-dropdown" id="menu-${s.session_id}">
                <div class="dropdown-item" onclick="renameSession('${s.session_id}')">Edit Name</div>
                <div class="dropdown-item delete" onclick="deleteSession('${s.session_id}')">Delete</div>
            </div>`;
        list.appendChild(div);
    });
    if (allSessions.length > 0) {
        const current = document.getElementById('currentSessionId').value;
        if (!current) loadChat(allSessions[allSessions.length - 1].session_id);
        else {
            document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
            const activeItem = document.getElementById(`sess-${current}`);
            if(activeItem) activeItem.classList.add('active');
        }
    } else { newSession(); }
}

function toggleSessionMenu(event, sessId) {
    event.stopPropagation();
    document.querySelectorAll('.session-dropdown').forEach(el => el.classList.remove('show'));
    const menu = document.getElementById(`menu-${sessId}`);
    if(menu) menu.classList.add('show');
}
async function renameSession(sessId) {
    const newName = prompt("Enter new session name:");
    if(newName) {
        await fetch('/api/rename_session', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessId, title: newName})
        });
        loadSessions();
    }
}
async function deleteSession(sessId) {
    if(confirm("Are you sure you want to delete this history?")) {
        await fetch('/api/delete_session', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessId})
        });
        if(document.getElementById('currentSessionId').value === sessId) {
            document.getElementById('currentSessionId').value = "";
            location.reload();
        } else { loadSessions(); }
    }
}
async function newSession() {
    const res = await fetch('/api/new_session', {method: 'POST'});
    const sess = await res.json();
    document.getElementById('currentSessionId').value = sess.session_id;
    document.getElementById('chatBox').innerHTML = '';
    const fullName = document.getElementById('userDisplayName').value || "Operator";
    const firstName = fullName.trim().split(' ')[0];
    const greeting = `Hello ${firstName}, how can I help you?`;
    await typeEffectMessage("NORA", greeting, "assistant");
    speak(greeting);
    loadSessions();
}
function loadChat(sessionId) {
    const session = allSessions.find(s => s.session_id === sessionId);
    if(!session) return;
    document.getElementById('currentSessionId').value = sessionId;
    document.querySelectorAll('.session-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.getElementById(`sess-${sessionId}`);
    if(activeItem) activeItem.classList.add('active');
    const box = document.getElementById('chatBox');
    box.innerHTML = '';
    session.messages.forEach(m => {
        appendMessageHTML(m.role === 'user' ? 'You' : 'NORA', m.content, m.role, m.timestamp);
    });
    scrollToBottom();
}
async function clearChat() {
    const sessId = document.getElementById('currentSessionId').value;
    if(sessId) {
        await fetch('/api/clear_session', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessId})
        });
        document.getElementById('chatBox').innerHTML = '';
        appendMessageHTML('NORA', 'Chat memory cleared.', 'assistant');
    }
}

// ========== MESSAGING (UPDATED FOR FILE UPLOAD) ==========
function handleEnter(e) { if(e.key === 'Enter') sendMessage(); }

async function sendMessage() {
    if (isTyping) return;
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    const sessId = document.getElementById('currentSessionId').value;
    
    // Allow sending if there is text OR a file
    if(!text && !selectedFile) return;
    
    // Display Message
    let displayText = text;
    if(selectedFile) displayText += ` [Attached: ${selectedFile.name}]`;
    appendMessageHTML("You", displayText, "user");
    
    input.value = '';
    setStatus("Processing...");
    isTyping = true;

    try {
        // Use FormData for File Upload
        const formData = new FormData();
        formData.append('message', text);
        formData.append('session_id', sessId);
        if(selectedFile) {
            formData.append('file', selectedFile);
        }

        const res = await fetch('/api/process_message', {
            method: 'POST',
            body: formData // No Content-Type header needed, browser sets it
        });
        
        const data = await res.json();
        
        // Clear file after sending
        clearFile();

        setStatus("Receiving Stream...");
        await typeEffectMessage("NORA", data.response, "assistant", data.timestamp);
        
        if(data.action && data.action.type === 'open_url') window.open(data.action.url, '_blank');
        
        const sessRes = await fetch('/api/get_sessions');
        const sessData = await sessRes.json();
        allSessions = sessData.sessions;
        
        speak(data.response);
    } catch (e) { appendMessageHTML("System", "Connection Error.", "assistant"); } 
    finally { setStatus("Ready"); isTyping = false; }
}

function appendMessageHTML(sender, text, role, time=null) {
    const box = document.getElementById('chatBox');
    const timestamp = time || new Date().toLocaleTimeString();
    let cleanText = text.replace(/\*/g, '');
    let formatted = cleanText.replace(/\n/g, '<br>');
    const html = `<div class="msg ${role}"><span class="timestamp">${sender} // ${timestamp}</span><div>${formatted}</div></div>`;
    box.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

function typeEffectMessage(sender, text, role, time=null) {
    return new Promise((resolve) => {
        const box = document.getElementById('chatBox');
        const timestamp = time || new Date().toLocaleTimeString();
        const msgDiv = document.createElement('div');
        msgDiv.className = `msg ${role}`;
        msgDiv.innerHTML = `<span class="timestamp">${sender} // ${timestamp}</span><div class="msg-content"></div>`;
        box.appendChild(msgDiv);
        scrollToBottom();
        const contentDiv = msgDiv.querySelector('.msg-content');
        let cleanText = text.replace(/\*/g, '');
        let i = 0; const speed = 15;
        function type() {
            if (i < cleanText.length) {
                if(cleanText.charAt(i) === '\n') contentDiv.innerHTML += '<br>';
                else contentDiv.innerHTML += cleanText.charAt(i);
                i++; scrollToBottom(); setTimeout(type, speed);
            } else { resolve(); }
        }
        type();
    });
}
function scrollToBottom() { const box = document.getElementById('chatBox'); box.scrollTop = box.scrollHeight; }
function setStatus(msg) { document.getElementById('status').innerText = msg; }

// ========== FEMALE VOICE LOGIC ==========
function setupVoice() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition(); recognition.continuous = false; recognition.lang = 'en-US';
        recognition.onstart = () => { document.getElementById('micBtn').classList.add('listening'); document.getElementById('micIcon').innerText = '🛑'; setStatus("Listening..."); };
        recognition.onend = () => { document.getElementById('micBtn').classList.remove('listening'); document.getElementById('micIcon').innerText = '🎤'; setStatus("Ready"); };
        recognition.onresult = (event) => { document.getElementById('userInput').value = event.results[0][0].transcript; sendMessage(); };
    } else { document.getElementById('micBtn').style.display = 'none'; }
}
function toggleVoice() { if(recognition) recognition.start(); }
function speak(text) {
    if (isMuted) return;
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*`_#]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    let voices = window.speechSynthesis.getVoices();
    if (voices.length === 0) {
        window.speechSynthesis.onvoiceschanged = function() {
            voices = window.speechSynthesis.getVoices();
            setFemaleVoice(utterance, voices);
            window.speechSynthesis.speak(utterance);
        };
    } else { setFemaleVoice(utterance, voices); window.speechSynthesis.speak(utterance); }
}
function setFemaleVoice(utterance, voices) {
    let selected = voices.find(v => v.name.includes("Microsoft Zira")) || 
                   voices.find(v => v.name.includes("Google US English")) || 
                   voices.find(v => v.name.includes("Samantha")) || 
                   voices.find(v => v.name.toLowerCase().includes("female"));
    if (selected) { utterance.voice = selected; utterance.pitch = 1.1; utterance.rate = 1.1; }
}
