# N.O.R.A. — Neural Operations & Response Assistant

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Ollama](https://img.shields.io/badge/AI-Ollama-purple)
![License](https://img.shields.io/badge/License-MIT-orange)

**N.O.R.A.** (Neural Operations & Response Assistant) is a locally hosted, intelligent desktop assistant that combines a modern cyberpunk-inspired web interface with powerful local AI capabilities. It enables computer control, image analysis, real-time web search, and context-aware conversations.

---

## Table of Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Installation Guide](#installation-guide)
- [Running the Application](#running-the-application)
- [Usage & Commands](#usage--commands)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Screenshots

<div align="center">
  <img src="static/logo.png" alt="NORA Logo" width="150">
</div>

| Login Splash Screen | Main Dashboard |
|:-------------------:|:--------------:|
| [Add Screenshot]  | [Add Screenshot] |

---

## Features

### Advanced User Interface

- **Cyberpunk-Inspired Design**: Animated glassmorphism interface with neon aesthetics and scanline effects
- **Dual Sidebar Navigation**:
  - **Left Sidebar**: Chat history with session management, rename, and delete functionality
  - **Right Sidebar**: Quick access panel featuring calculator, notepad, and system controls
- **Interactive Controls**: Mute toggle, web search activation, and file upload capabilities

### Intelligence & Vision Capabilities

- **Contextual Memory**: Maintains conversation context throughout the session for natural dialogue flow
- **Computer Vision**: Upload and analyze images with descriptions powered by Llava
- **File Analysis**: Upload text files (.txt, .py, etc.) for summarization or code review
- **Real-Time Web Search**: Access current information through DuckDuckGo integration for news, sports scores, and other up-to-date data

### System Control & Voice Interaction

- **Voice Interaction**: Web-based speech-to-text with prioritized female text-to-speech voices (Zira/Samantha)
- **Application Control**: Launch Calculator, Notepad, Camera, Word, Excel, and other system applications
- **System Utilities**: Screenshot capture, battery status monitoring, Task Manager, and Control Panel access

---

## Installation Guide

### Prerequisites

Ensure the following software is installed on your system:

- [Python 3.10 or higher](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- [Ollama](https://ollama.com/) (Required for AI functionality)

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/NORA-Assistant.git
cd NORA-Assistant
```

### Step 2: Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install all required packages including Flask, AI tools, system utilities, and search/image processing libraries:

```bash
pip install flask ollama pyautogui psutil opencv-python duckduckgo-search Pillow
```

### Step 4: Configure AI Models

Two models are required: one for text-based conversation and one for image analysis.

**Install Text Model (Llama 3.2):**
```bash
ollama pull llama3.2
```

**Install Vision Model (Llava):**
```bash
ollama pull llava
```

---

## Running the Application

### Start the Server

```bash
python app.py
```

### Access the Interface

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

### Authentication

1. Click the logo core to unlock the login interface
2. Register a new account (email and phone fields included)
3. Login with your credentials to access the main terminal

---

## Usage & Commands

### Voice & Text Commands

| Command | Action |
|---------|--------|
| "Open Calculator" | Launches the system calculator application |
| "Open Camera" | Opens the webcam application |
| "Take Screenshot" | Saves a screenshot to the project folder |
| "Check Battery" | Displays battery percentage and charging status |
| "Open Google / YouTube" | Opens specified websites in a new browser tab |

### Web Search

1. Click the globe icon in the interface (it will illuminate green when active)
2. Ask questions about current events (e.g., "Who won the last World Cup?")
3. N.O.R.A. will fetch and present real-time data from the web

### Computer Vision

1. Click the paperclip icon to open the file upload dialog
2. Select an image file
3. Ask questions such as "Describe this image" or "Extract text from this picture"

---

## Project Structure

```
NORA/
│
├── app.py                # Main backend server (Flask, logic, web search integration)
├── users.json            # User database with encrypted passwords
├── chat_[user].json      # Individual user chat history logs
│
├── static/
│   ├── style.css         # Cyberpunk styling and animations
│   ├── script.js         # Frontend logic (voice, uploads, API calls)
│   └── logo.png          # Application logo asset
│
└── templates/
    ├── login.html        # Splash screen and login interface
    ├── register.html     # User registration page
    └── chat.html         # Main dashboard interface
```

---

## Troubleshooting

### Common Issues

**"System offline. AI module not detected"**
- Ensure Ollama is running in the background
- Verify that required models are installed using `ollama list`

**"Search Error" or Slow Response Times**
- Check your internet connection
- Web search functionality requires active DuckDuckGo connectivity

**Voice Recognition Not Functioning**
- Grant microphone permissions in your browser settings
- Ensure your microphone is properly connected and configured

**Image Analysis Failures**
- Verify that the Llava model is installed: `ollama pull llava`
- Check that uploaded files are in supported image formats (JPEG, PNG)

---

## License

Created by me

---

<div align="center">
<p><strong>Developed by Habib</strong></p>
</div>
