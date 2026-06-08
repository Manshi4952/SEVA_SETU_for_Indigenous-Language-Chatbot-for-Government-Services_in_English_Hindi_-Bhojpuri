# ▶️ SevaSetu — Complete Run Order & Commands

Everything you need from a fresh unzip to a fully trained, running application.

---

## Prerequisites — Install These First

### Python 3.10+
```bash
# Check version
python --version   # or python3 --version
# Must be 3.10 or higher
```

### Node.js 18+
```bash
node --version   # Must be 18 or higher
npm --version
```

### Get a Groq API Key (Free)
1. Go to → https://console.groq.com
2. Sign up (free)
3. Create a new API key
4. Copy it — you'll use it in Step 2 below

---

---

# PART 1 — FIRST-TIME SETUP

## Step 1 — Extract & Navigate

```bash
# Extract the ZIP
unzip SevaSetu_Production_v5.zip
cd project
```

---

## Step 2 — Configure Backend Environment

```bash
cd backend
cp .env.example .env
```

Now open `backend/.env` in any text editor and set these two values:

```env
GROQ_API_KEY=gsk_paste_your_actual_key_here
SECRET_KEY=any-random-32-character-string-here
```

Everything else can stay as default for local development.

---

## Step 3 — Install Backend Dependencies

```bash
# Still inside backend/
# Create virtual environment
python -m venv venv

# Activate it:
# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Linux / macOS:
source venv/bin/activate

# Install all packages
pip install -r requirements.txt
```

Expected output at the end:
```
Successfully installed fastapi uvicorn groq faiss-cpu ...
```

---

## Step 4 — Install Frontend Dependencies

Open a **second terminal** (keep the first one for backend):

```bash
# From the project/ root folder
cd frontend
npm install
```

Expected output at the end:
```
added 312 packages in 45s
```

---

---

# PART 2 — APPROACH 1: DATA ENRICHMENT (Run Before Starting App)

These scripts improve the quality of responses before you even start the server.

## Step 5 — Audit the Dataset

```bash
# In backend/ with venv activated
cd backend
python scripts/audit_schemes.py
```

This shows which schemes have missing or thin content across all languages.

---

## Step 6 — Enrich Missing Bhojpuri Translations

```bash
python scripts/enrich_schemes.py
```

- Translates missing Bhojpuri fields for 29 schemes using Groq
- Backs up `schemes_cleaned.json` → `schemes_cleaned_backup.json` first
- Saves progress every 10 schemes
- Takes approximately 5 minutes

---

## Step 7 — Rebuild the FAISS Search Index

```bash
# Install sentence-transformers (first time only — ~300MB download)
pip install sentence-transformers

# Rebuild the index
python scripts/rebuild_index.py
```

Expected output:
```
Loading schemes...
Loaded 218 schemes.
Loading sentence-transformers model...
Building embeddings...  ████████████ 100% 218/218
Building FAISS index...
✅ FAISS index saved to ./data/faiss.index
```

This takes 1–2 minutes. Only needs to be run once, or whenever you change `schemes_cleaned.json`.

---

---

# PART 3 — START THE APPLICATION

## Step 8 — Start the Backend Server

```bash
# In backend/ with venv activated
cd backend
uvicorn main:app --reload --port 8000
```

You should see:
```
[RAG] Loaded 218 schemes from ./data/schemes_cleaned.json.
[LLM] Groq provider initialised (model: llama-3.3-70b-versatile).
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

If you see `[LLM] No provider configured` — check that `GROQ_API_KEY` is set in `backend/.env`.

---

## Step 9 — Start the Frontend Server

In your **second terminal**:

```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in 800ms
  ➜  Local:   http://localhost:3000/
```

---

## Step 10 — Open the App

Go to → **http://localhost:3000**

1. Click **Register** → create an account
2. Log in
3. Start chatting in **English**, **Hindi**, or **Bhojpuri**

API documentation → http://localhost:8000/docs

---

---

# PART 4 — APPROACH 3: FINE-TUNING

Run Approach 1 (Steps 5–7) first. Then choose ONE of the options below.

## Step 11 — Generate Training Data (Required for all options)

```bash
# In backend/ with venv activated
python scripts/generate_finetune_data.py
```

Output:
```
✅ Generated 2184 training examples
   Saved to: ./data/finetune_dataset.jsonl
```

---

## Option A — Groq Fine-Tuning API (FREE — Recommended)

No GPU. No extra account. Uses your existing GROQ_API_KEY.

```bash
# Upload dataset and start training
python scripts/finetune/option_a_groq.py --upload
```

Output:
```
✅ Dataset valid: 2184 training examples
✅ Split: 1965 train / 219 validation
✅ Uploaded: file-abc123
✅ Uploaded: file-def456
✅ Job created: ftjob-xyz789
⏳ Training started! (~30 min – 2 hours)
```

```bash
# Check status (run after 30–60 minutes)
python scripts/finetune/option_a_groq.py --status
```

When status shows `succeeded`:
```
✅ Training complete! Your model ID: ft:llama3-8b-8192:sevasetu:abc123
```

Update `backend/.env`:
```env
LLM_PROVIDER=groq
LLM_MODEL=ft:llama3-8b-8192:sevasetu:abc123
```

Restart backend (Ctrl+C then run again):
```bash
uvicorn main:app --reload --port 8000
```

---

## Option B — Together AI (~$1–3 total)

Sign up at https://api.together.ai — you get $25 free credits.

```bash
# Add your Together AI key to backend/.env:
# TOGETHER_API_KEY=your_key_here

# Upload and start training
python scripts/finetune/option_b_together.py --upload
```

```bash
# Check status (run after 30–60 minutes)
python scripts/finetune/option_b_together.py --status
```

When complete, update `backend/.env`:
```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your_key_here
TOGETHER_MODEL=your-username/sevasetu-llama3-8b
```

Restart backend.

---

## Option C — HuggingFace AutoTrain (No-code UI)

```bash
# Add to backend/.env:
# HF_TOKEN=hf_your_token
# HF_USERNAME=your_hf_username

# Convert and upload dataset to HuggingFace Hub
python scripts/finetune/option_c_huggingface.py --upload
```

Then go to https://ui.autotrain.huggingface.co:
1. New Project → LLM Fine-tuning → SFT
2. Dataset: `your-username/sevasetu-finetune-data`
3. Base model: `meta-llama/Llama-3.2-3B-Instruct`
4. Text column: `text`
5. Click **Train**

After training, download the model and continue with Ollama setup below.

---

## Option D — Modal.com (~$0.50–1.50, No timeouts)

Best alternative to Colab — runs completely, no session cuts.

```bash
# Install Modal
pip install modal

# Authenticate (opens browser)
modal token new

# Generate the Modal app file
python scripts/finetune/option_d_modal.py

# Create a Modal storage volume
modal volume create sevasetu-training

# Upload your training data to Modal
modal volume put sevasetu-training data/finetune_dataset.jsonl /data/

# Run training (~20–30 min on A10G GPU, ~$1)
modal run scripts/finetune/modal_finetune_app.py

# Download the trained model to your machine
modal volume get sevasetu-training /data/sevasetu_model ./sevasetu_modal_output
```

---

## After Option C or D — Run Model Locally with Ollama

```bash
# 1. Install Ollama from https://ollama.com/download

# 2. Create a Modelfile
#    (run from the folder that contains sevasetu_modal_output/)
cat > Modelfile << 'EOF'
FROM ./sevasetu_modal_output/sevasetu_model
SYSTEM "You are SevaSetu, a warm AI assistant helping Bihar citizens understand government welfare schemes. Reply in the user's language (English, Hindi, or Bhojpuri)."
PARAMETER temperature 0.3
PARAMETER num_predict 600
EOF

# 3. Import into Ollama
ollama create sevasetu -f Modelfile

# 4. Test the model
ollama run sevasetu "PM Kisan के बारे में बताओ"

# 5. Update backend/.env
#    LLM_PROVIDER=ollama
#    OLLAMA_MODEL=sevasetu
#    OLLAMA_BASE_URL=http://localhost:11434
```

Restart backend:
```bash
uvicorn main:app --reload --port 8000
```

---

---

# PART 5 — VERIFY EVERYTHING IS WORKING

## Step 12 — Run Quality Tests

```bash
# In backend/ with venv activated
python scripts/test_responses.py
```

This runs 10 test queries (English, Hindi, Bhojpuri) and shows pass/fail.

Expected output:
```
SevaSetu Response Quality Test
────────────────────────────────────────────────────────────
Test 1: English description
Query [english/beginner]: Tell me about PM Kisan scheme
Response: **PM Kisan Samman Nidhi** gives farmers ₹6,000 every year...
✅ Pass

Test 2: English apply
...
Results: 10/10 tests passed ✅
```

---

---

# PART 6 — DOCKER (Optional — Run Everything in One Command)

If you have Docker installed, skip Steps 3–9 and use this instead:

```bash
# From the project/ root folder

# 1. Configure environment first
cp backend/.env.example backend/.env
# Edit backend/.env and add GROQ_API_KEY + SECRET_KEY

# 2. Build and start everything
docker-compose up --build

# 3. Open http://localhost:3000
```

To stop:
```bash
docker-compose down
```

To run in background:
```bash
docker-compose up --build -d
docker-compose logs -f   # view live logs
```

---

---

# QUICK REFERENCE — DAILY USE

Once setup is complete, every day you just need:

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate     # Linux/Mac
# OR: venv\Scripts\activate  # Windows
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Then open http://localhost:3000

---

---

# TROUBLESHOOTING

### Backend won't start — "ModuleNotFoundError"
```bash
# Make sure venv is activated, then reinstall
pip install -r requirements.txt
```

### "No provider configured" / template-only mode
```bash
# Check your .env file exists and has the key
cat backend/.env | grep GROQ_API_KEY
# Should show: GROQ_API_KEY=gsk_...
```

### Frontend shows blank page
```bash
# Check backend is running on port 8000
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### FAISS index error on startup
```bash
# Rebuild the index
cd backend
source venv/bin/activate
pip install sentence-transformers
python scripts/rebuild_index.py
```

### Port already in use
```bash
# Kill whatever is using the port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Fine-tuning job check — "No job ID found"
```bash
# Pass the job ID manually
python scripts/finetune/option_a_groq.py --status --job-id ftjob-yourjobid
```

---

---

# COMPLETE COMMAND SUMMARY (All at once)

```
SETUP:
  cd backend
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env          ← edit: add GROQ_API_KEY + SECRET_KEY

APPROACH 1 (Data Enrichment):
  python scripts/audit_schemes.py
  python scripts/enrich_schemes.py
  pip install sentence-transformers
  python scripts/rebuild_index.py

RUN APP:
  [Terminal 1] uvicorn main:app --reload --port 8000
  [Terminal 2] cd frontend && npm install && npm run dev
  → Open http://localhost:3000

APPROACH 3A (Fine-tune with Groq — FREE):
  python scripts/generate_finetune_data.py
  python scripts/finetune/option_a_groq.py --upload
  # Wait 30–60 min
  python scripts/finetune/option_a_groq.py --status
  # Update LLM_MODEL in .env with returned model ID
  # Restart backend

TEST QUALITY:
  python scripts/test_responses.py
```
