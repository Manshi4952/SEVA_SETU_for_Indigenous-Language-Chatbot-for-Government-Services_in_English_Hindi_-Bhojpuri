# 🏛️ SevaSetu – Indigenous Language Chatbot for Government Services

**SevaSetu** is a multilingual AI chatbot that helps citizens of Bihar access information about 218+ government welfare schemes in **English**, **Hindi**, and **Bhojpuri**.

---

## ✨ Features

- 🗣️ **Trilingual** – English, Hindi, Bhojpuri (Devanagari + Roman)
- 🤖 **AI-powered** – Groq LLM (Llama 3.3 70B) for natural, human-like responses
- 📚 **218+ Schemes** – Bihar state + central government schemes
- 🔍 **Smart RAG** – FAISS-based semantic search with keyword scoring
- 🎤 **Voice Input** – Speech-to-text support
- 🔊 **Voice Output** – Text-to-speech in all 3 languages
- 🌙 **Dark Mode** – Full dark/light theme
- 📱 **Mobile Responsive** – Works on all screen sizes
- 🔒 **Secure** – JWT authentication, SQLite database

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com)

### 1. Clone & Setup Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API docs at: http://localhost:8000/docs

### 3. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

---

## 🔑 Environment Variables (backend/.env)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Your Groq API key from console.groq.com |
| `SECRET_KEY` | ✅ Yes | JWT secret key (change in production!) |
| `DATABASE_URL` | No | SQLite by default |
| `LLM_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `LLM_MAX_TOKENS` | No | Default: 700 |

---

## 🧠 LLM Models (Groq)

| Purpose | Model |
|---|---|
| Primary | `llama-3.3-70b-versatile` |
| Fast/Simple | `llama-3.1-8b-instant` |

Switch models by changing `LLM_MODEL` in `.env`.

---

## 🐳 Docker

```bash
# Copy and fill in env file first
cp backend/.env.example backend/.env
# Add GROQ_API_KEY to backend/.env

docker-compose up --build
```

---

## 📁 Project Structure

```
sevasetu/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route handlers
│   │   ├── core/              # Config, security, deps
│   │   ├── db/                # SQLAlchemy session
│   │   ├── models/            # ORM models
│   │   └── services/
│   │       ├── llm/           # LLM provider abstraction
│   │       │   └── provider.py  # Groq integration
│   │       ├── rag_service.py   # Core RAG pipeline
│   │       └── voice_service.py # TTS/STT
│   ├── data/
│   │   ├── schemes_cleaned.json  # 218+ schemes
│   │   └── faiss.index           # Semantic search index
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/   # ChatWindow, ChatInput, Navbar, SchemeCard
    │   ├── pages/        # ChatPage, HomePage, AuthPage, SchemesPage
    │   ├── store/        # Zustand state management
    │   └── utils/        # API client, i18n
    └── package.json
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Zustand |
| Backend | FastAPI, SQLAlchemy, SQLite |
| LLM | Groq (Llama 3.3 70B) |
| Search | FAISS + keyword scoring |
| Auth | JWT (python-jose) |
| Voice | gTTS + SpeechRecognition |

---

## 📝 License

MIT License — built for the public good 🇮🇳
