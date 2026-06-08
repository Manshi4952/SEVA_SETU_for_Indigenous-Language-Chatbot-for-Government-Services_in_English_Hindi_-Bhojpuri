# 📦 SevaSetu – Installation Guide

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Ubuntu 22.04 |
| Python | 3.10 | 3.11+ |
| Node.js | 18 | 20 LTS |
| RAM | 4 GB | 8 GB |
| Disk | 2 GB | 5 GB |

---

## Step 1 – Get a Groq API Key (Free)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Create a new API key
4. Copy the key — you'll need it in Step 3

---

## Step 2 – Extract the Project

```bash
unzip SEVA_SETU_*.zip
cd SEVA_SETU_for_Indigenous-Language-Chatbot-for-Government-Services_in_English_Hindi_-Bhojpuri
```

---

## Step 3 – Configure Environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` in a text editor and set:

```env
GROQ_API_KEY=gsk_your_actual_groq_key_here
SECRET_KEY=any-random-32-character-string-here
```

---

## Step 4 – Install Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

---

## Step 5 – Install Frontend

```bash
cd ../frontend
npm install
```

---

## Step 6 – Run the Application

Open **two terminal windows**:

**Terminal 1 – Backend:**
```bash
cd backend
# Activate venv first (see Step 4)
uvicorn main:app --reload --port 8000
```

You should see:
```
[RAG] Loaded 218 schemes from ./data/schemes_cleaned.json.
[LLM] Groq provider initialised (model: llama-3.3-70b-versatile).
INFO: Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 – Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

---

## Step 7 – Open the App

Go to [http://localhost:3000](http://localhost:3000)

1. Click **Register** to create an account
2. Log in
3. Start chatting in English, Hindi, or Bhojpuri!

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'groq'"
```bash
pip install groq>=0.9.0
```

### "GROQ_API_KEY not set" / Running in template mode
- Make sure you created `backend/.env` (not just `.env.example`)
- Check that `GROQ_API_KEY=gsk_...` is set correctly (no quotes needed)

### Frontend shows blank page / API errors
- Make sure the backend is running on port 8000
- Check browser console for CORS errors
- Verify `ALLOWED_ORIGINS` in `.env` includes `http://localhost:3000`

### Port already in use
```bash
# Backend on different port:
uvicorn main:app --reload --port 8001
# Then update frontend/.env: VITE_API_URL=http://localhost:8001/api/v1
```

### npm install fails
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```
