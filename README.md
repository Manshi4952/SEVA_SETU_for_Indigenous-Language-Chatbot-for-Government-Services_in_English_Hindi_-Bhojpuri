<div align="center">

# 🏛️ SevaSetu — सेवासेतु

### *Multilingual AI Chatbot for Indian Government Schemes*

**Ask. Understand. Avail. | पूछें। समझें। लाभ उठाएं। | पूछीं। समझीं। फायदा उठाईं।**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=nodedotjs)](https://nodejs.org)
[![SQLite](https://img.shields.io/badge/SQLite-Local%20Dev-003B57?style=flat-square&logo=sqlite)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Government Schemes Dataset](#-government-schemes-dataset)
- [Language Support](#-language-support)
- [How the AI Works](#-how-the-ai-works)
- [CI/CD](#-cicd)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 About the Project

**SevaSetu (सेवासेतु)** is a final-year B.Tech project — an AI-powered multilingual chatbot that bridges the gap between Indian citizens and government welfare schemes. Millions of eligible citizens miss out on benefits simply because information is unavailable in their local language or too complex to understand.

SevaSetu solves this by allowing users to **ask questions in Hindi, Bhojpuri, or English** and receive clear, simple, actionable information about schemes like PM Kisan, Atal Pension Yojana, PMAY, and more.

> 💡 Targeted at rural and semi-urban users of Bihar and Eastern UP who primarily speak Hindi and Bhojpuri.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🗣️ **Multilingual Chat** | Full support for Hindi, Bhojpuri, and English with auto language detection |
| 🤖 **AI-Powered RAG** | Retrieval-Augmented Generation — keyword search with optional FAISS semantic search |
| 🔍 **Intent Detection** | Understands whether user wants benefits, eligibility, or how to apply |
| 🎙️ **Voice Input / Output** | Speech-to-text and text-to-speech in Hindi/Bhojpuri via gTTS |
| 👤 **JWT Authentication** | Secure register, login, and protected user sessions |
| 💬 **Chat History** | Persistent conversation history per user |
| 🌙 **Dark / Light Mode** | Full theme support with Tailwind CSS `dark:` classes |
| 📱 **Responsive UI** | Mobile and desktop friendly |
| 🔰 **Beginner / Advanced Mode** | Simplified or detailed responses based on user preference |
| 🛡️ **Admin Dashboard** | View user stats and system metrics |

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.111.0 | REST API framework |
| **Uvicorn** | 0.29.0 | ASGI server |
| **SQLAlchemy** | 2.0.30 | ORM / database layer |
| **SQLite** | — | Local development database |
| **PostgreSQL** | — | Production database |
| **Alembic** | 1.13.1 | Database migrations |
| **python-jose** | 3.3.0 | JWT authentication |
| **bcrypt** | 4.x | Password hashing (direct, no passlib) |
| **Pydantic v2** | 2.7.1 | Data validation & settings |
| **gTTS** | 2.5.1 | Text-to-speech |
| **SpeechRecognition** | 3.10.3 | Speech-to-text |
| **langdetect** | 1.0.9 | Automatic language detection |
| **FAISS** | *(optional)* | Vector similarity search |
| **sentence-transformers** | *(optional)* | Multilingual embeddings |

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| **React** | 18.3.1 | UI framework |
| **Vite** | 5.2.13 | Build tool & dev server |
| **React Router** | 6.23.1 | Client-side routing |
| **Zustand** | 4.5.2 | Global state management |
| **Axios** | 1.7.2 | HTTP client |
| **Tailwind CSS** | 3.4.4 | Utility-first styling |
| **Framer Motion** | 11.2.11 | Animations |
| **Lucide React** | 0.383.0 | Icons |
| **react-hot-toast** | 2.4.1 | Toast notifications |

---

## 📁 Project Structure

```
sevasetu/
│
├── backend/                          # FastAPI backend
│   ├── main.py                       # App factory & startup lifecycle
│   ├── requirements.txt              # All dependencies
│   ├── alembic.ini                   # Database migration config
│   ├── .env                          # Environment variables (not committed)
│   ├── .env.example                  # Template for environment setup
│   │
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py             # Settings loaded from .env (pydantic-settings)
│   │   │   ├── security.py           # JWT creation/decode + bcrypt password hashing
│   │   │   └── deps.py               # FastAPI dependency injectors (get_db, get_current_user)
│   │   │
│   │   ├── db/
│   │   │   └── session.py            # SQLAlchemy engine & session factory
│   │   │
│   │   ├── models/
│   │   │   └── orm.py                # User, Conversation, Message, Scheme ORM models
│   │   │
│   │   ├── api/routes/
│   │   │   ├── auth.py               # POST /register, POST /login, GET /me
│   │   │   ├── chat.py               # Chat messages & conversation history
│   │   │   ├── schemes.py            # Scheme listing & detail
│   │   │   ├── voice.py              # TTS & STT endpoints
│   │   │   └── admin.py              # Admin-only stats & user management
│   │   │
│   │   └── services/
│   │       ├── rag_service.py        # RAG pipeline: FAISS + keyword fallback
│   │       └── voice_service.py      # gTTS + SpeechRecognition helpers
│   │
│   └── data/
│       └── schemes.json              # Government schemes dataset (auto-seeded on startup)
│
├── frontend/                         # React + Vite frontend
│   ├── index.html
│   ├── vite.config.js                # Vite config with /api proxy to backend
│   ├── tailwind.config.js            # Custom colors: saffron, ashoka, jade, charcoal
│   ├── package.json
│   ├── .env                          # Frontend env vars (not committed)
│   ├── .env.example                  # Template for frontend env setup
│   │
│   └── src/
│       ├── App.jsx                   # Root component with React Router v6
│       ├── main.jsx                  # Entry point
│       │
│       ├── pages/
│       │   ├── HomePage.jsx          # Landing page with hero, features, scheme preview
│       │   ├── AuthPage.jsx          # Login & Register forms
│       │   ├── ChatPage.jsx          # Main chat interface
│       │   ├── SchemesPage.jsx       # Browse all government schemes
│       │   ├── AboutPage.jsx         # About the project
│       │   └── AdminPage.jsx         # Admin dashboard
│       │
│       ├── components/
│       │   ├── Navbar.jsx            # Top navigation with language & dark mode toggle
│       │   ├── ChatWindow.jsx        # Message display with typing indicator
│       │   ├── ChatInput.jsx         # Message input with voice support
│       │   └── SchemeCard.jsx        # Scheme info card component
│       │
│       ├── store/
│       │   └── useStore.js           # Zustand state: auth, chat, settings, schemes
│       │
│       ├── utils/
│       │   ├── api.js                # Axios instance with base URL + auth header
│       │   └── i18n.js               # UI string translations (English / Hindi / Bhojpuri)
│       │
│       └── styles/
│           └── globals.css           # Global Tailwind + custom CSS
│
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions: backend tests, frontend build, Docker
│
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Minimum Version | Check command |
|---|---|---|
| **Python** | 3.10 | `python --version` |
| **Node.js** | 18 | `node --version` |
| **npm** | 9 | `npm --version` |
| **Git** | any | `git --version` |

---

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/your-username/sevasetu.git
cd sevasetu
```

**2. Backend setup**

```bash
cd backend

# Create & activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\Activate
# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

Edit `backend/.env` with your values (see [Environment Variables](#-environment-variables)).

**3. Frontend setup**

```bash
cd ../frontend

# Install Node dependencies
npm install

# Copy environment file
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

---

### Running the Project

Open **two terminals** side by side.

**Terminal 1 — Backend**

```bash
cd backend
.\venv\Scripts\Activate       # Windows  |  source venv/bin/activate on Mac/Linux
python main.py
```

✅ Ready when you see:
```
🚀 SevaSetu starting up…
✅ Database tables ready
✅ Scheme knowledge base seeded
[RAG] Ready — 45 chunks loaded.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

✅ Ready when you see:
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:3000/
```

**Open in browser:**

| Service | URL |
|---|---|
| 🌐 Web App | http://localhost:3000 |
| 📖 API Docs (Swagger) | http://localhost:8000/api/docs |
| 📖 API Docs (ReDoc) | http://localhost:8000/api/redoc |
| ❤️ Health Check | http://localhost:8000/health |

---

## 🔐 Environment Variables

### Backend — `backend/.env`

```env
# Database — SQLite for local, PostgreSQL for production
DATABASE_URL=sqlite:///./sevasetu.db
# DATABASE_URL=postgresql://user:password@localhost:5432/sevasetu

# JWT — change SECRET_KEY before deploying!
SECRET_KEY=your-super-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS — comma-separated allowed frontend origins
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Dataset & AI paths
KNOWLEDGE_BASE_PATH=./data/schemes.json
FAISS_INDEX_PATH=./data/faiss.index

# Voice output
AUDIO_OUTPUT_DIR=./static/audio

# Debug
DEBUG=True
```

### Frontend — `frontend/.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=SevaSetu
```

> ⚠️ **Never commit `.env` files to Git.** Both are already listed in `.gitignore`.

---

## 📡 API Reference

Full interactive docs available at **http://localhost:8000/api/docs**

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | ❌ | Register a new user |
| `POST` | `/api/v1/auth/login` | ❌ | Login & receive JWT token |
| `GET` | `/api/v1/auth/me` | ✅ | Get current user profile |

### Chat

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/chat/message` | ✅ | Send message, get AI reply |
| `GET` | `/api/v1/chat/conversations` | ✅ | List all conversations |
| `GET` | `/api/v1/chat/conversations/{id}` | ✅ | Get conversation with full message history |
| `DELETE` | `/api/v1/chat/conversations/{id}` | ✅ | Delete a conversation |

### Schemes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/schemes/` | ❌ | List all schemes (supports `?q=` search and `?language=` filter) |
| `GET` | `/api/v1/schemes/{id}` | ❌ | Get full scheme details |

### Voice

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/voice/tts` | ✅ | Convert text to speech (returns audio URL) |
| `POST` | `/api/v1/voice/stt` | ✅ | Convert uploaded audio to text |

### Admin

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/stats` | ✅ Admin | Platform statistics (users, messages, schemes) |
| `GET` | `/api/v1/admin/users` | ✅ Admin | List all registered users |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status":"ok","app":"SevaSetu","version":"1.0.0"}` |

---

## 🏛️ Government Schemes Dataset

The dataset lives in `backend/data/schemes.json` and is **automatically seeded** into the database on first startup. Currently includes:

| Scheme | ID |
|---|---|
| PM Kisan Samman Nidhi | PM-KISAN-001 |
| Pradhan Mantri Jeevan Jyoti Bima Yojana | PMJJBY-002 |
| Atal Pension Yojana | APY-003 |
| Pradhan Mantri Awas Yojana | PMAY-004 |
| Pradhan Mantri Suraksha Bima Yojana | PMSBY-005 |

### Adding New Schemes

Add a new entry to `backend/data/schemes.json`:

```json
{
  "id": "SCHEME-ID-006",
  "scheme": "Full Scheme Name",
  "english": "Description in English",
  "hindi": "हिंदी में विवरण",
  "bhojpuri": "भोजपुरी में जानकारी",
  "benefits": {
    "english": "What the beneficiary receives",
    "hindi": "क्या मिलेगा",
    "bhojpuri": "का मिलेला"
  },
  "eligibility": {
    "english": "Who can apply",
    "hindi": "कौन आवेदन कर सकता है",
    "bhojpuri": "के आवेदन कइ सकेला"
  },
  "age_limit": "18-60",
  "contribution_type": "Government funded",
  "pension_range": "₹X/year"
}
```

Delete `backend/sevasetu.db` and restart — the new scheme will be seeded automatically.

---

## 🌍 Language Support

SevaSetu supports **3 languages** across the entire UI and AI responses:

| Language | Script | UI | AI Responses | Voice |
|---|---|---|---|---|
| 🇬🇧 English | Latin | ✅ | ✅ | ✅ |
| 🇮🇳 Hindi | Devanagari | ✅ | ✅ | ✅ |
| 🗣️ Bhojpuri | Devanagari | ✅ | ✅ | ✅ (via Hindi TTS) |

- Automatic language detection from user's typed message via `langdetect`
- Manual language override via the UI dropdown in the navbar
- All scheme content stored separately for each language in the database
- UI strings fully translated in `frontend/src/utils/i18n.js`

---

## 🤖 How the AI Works

SevaSetu uses a **Retrieval-Augmented Generation (RAG)** pipeline:

```
User Query (Hindi / Bhojpuri / English)
        ↓
  Language Detection  (langdetect)
        ↓
  Intent Detection
  (benefits / eligibility / how-to-apply / description)
        ↓
  Scheme Retrieval
  ├── With FAISS:    semantic vector search (paraphrase-multilingual-MiniLM-L12-v2)
  └── Without FAISS: keyword + alias matching (default, no GPU needed)
        ↓
  Response Generation
  (template-based answer with real scheme data)
        ↓
  Reply in User's Language  +  Optional TTS Audio
```

**FAISS is optional.** The app ships with a smart keyword fallback that works out of the box. To enable full semantic search, install `faiss-cpu` and `sentence-transformers` (they are not in `requirements.txt` by default due to size — add them manually if needed).

---

## ⚙️ CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push to `main` or `develop`:

| Job | What it does |
|---|---|
| **Backend Tests** | Runs `pytest` against a PostgreSQL test database (Python 3.11) |
| **Frontend Build** | Runs `npm ci` + `vite build` (Node 20) |
| **Docker Build** | Builds the backend Docker image and verifies FastAPI imports (runs only on `main`) |

---

## 🤝 Contributing

Contributions are welcome!

1. **Fork** the repository
2. **Create** your feature branch: `git checkout -b feature/YourFeature`
3. **Commit** your changes: `git commit -m 'Add YourFeature'`
4. **Push** to the branch: `git push origin feature/YourFeature`
5. **Open** a Pull Request against `main`

Please make sure your code runs without errors and that the CI checks pass before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ for rural India | भारत के गांवों के लिए

**SevaSetu — सेवासेतु**
*Bridging citizens with their government rights*

</div>
