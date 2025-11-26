# N.O.R.A-web
N.O.R.A. — Neural Operations & Response Assistant

Python 3.8+ Flask Framework Ollama AI MIT License

N.O.R.A. is a locally hosted desktop assistant interface inspired by
futuristic Sci-Fi systems. It provides an animated cyberpunk-style
interface along with intelligent system-control capabilities powered by
local Large Language Models (LLMs) using Ollama.

------------------------------------------------------------------------

SCREENSHOTS

(Add your screenshots inside the folder and reference them here.)

static/logo.png

Login Screen | Main Dashboard [Insert Screenshot] | [Insert Screenshot]

------------------------------------------------------------------------

FEATURES

Interface - Animated splash screen with interactive logo. - Cyberpunk
and glassmorphism UI design. - Dual sidebar system: - Left: Chat history
with rename and delete functionalities. - Right: Tools panel including
calculator, camera access, and more. - Typewriter-style streaming AI
responses.

Intelligence and Voice - Local AI chat using Ollama (Llama 3 model
recommended). - Voice Interaction: - Speech-to-Text for voice
commands. - Text-to-Speech output (optimized for female voices such as
Zira/Samantha).

System Control - Launch applications such as Calculator, Notepad,
Camera, Word, and Excel. - System utilities: screenshots, battery info,
task manager, and more. - Web utilities: open Google, YouTube, Google
Maps.

------------------------------------------------------------------------

INSTALLATION GUIDE

1.  Prerequisites Install:

-   Python 3.10+
-   Git
-   Ollama

2.  Clone the Repository git clone
    https://github.com/YOUR_USERNAME/NORA-Assistant.git cd
    NORA-Assistant

3.  Create a Virtual Environment

Windows: python -m venv venv venv

Mac/Linux: python3 -m venv venv source venv/bin/activate

4.  Install Dependencies pip install flask ollama pyautogui psutil
    opencv-python

5.  Set Up the AI Model ollama pull llama3:8b (or: ollama pull
    tinyllama)

------------------------------------------------------------------------

RUNNING THE PROJECT

Start Server: python app.py

Open Interface: http://127.0.0.1:5000

Login: Click the core logo → Register → Login.

------------------------------------------------------------------------

VOICE AND SYSTEM COMMANDS

Open Calculator - Launches Windows Calculator
Open Notepad - Opens Notepad
Open Camera - Opens Camera App
Take Screenshot - Saves screenshot
Check Battery - Shows battery percentage
Open Task Manager - Opens Task Manager
Open Google - Opens google.com
Open YouTube - Opens youtube.com
Clear Chat - Clears current chat

------------------------------------------------------------------------

PROJECT STRUCTURE

NORA/ app.py users.json chat_[user].json static/ style.css script.js
logo.png templates/ login.html register.html chat.html

------------------------------------------------------------------------

TROUBLESHOOTING

AI Module Not Detected: Ensure Ollama is installed and running.

Voice Input Not Working: Allow microphone access in the browser.

System Commands Not Opening: Windows optimized. Mac/Linux users may need
to edit app.py.

------------------------------------------------------------------------

LICENSE MIT License

AUTHOR Made by Habib
