# 🧠 SevaSetu – Model Training & Improvement Guide

Three approaches to make SevaSetu smarter — each builds on the last.

---

## Approach 1 — Enrich the Data (Run First, Free, Biggest Impact)

### Step 1: Audit
```bash
cd backend && source venv/bin/activate
python scripts/audit_schemes.py
```

### Step 2: Auto-fill missing Bhojpuri translations
```bash
python scripts/enrich_schemes.py
```
Calls Groq to translate Hindi → Bhojpuri for the 29 schemes missing it. Takes ~5 min. Backs up your JSON first.

### Step 3: Rebuild FAISS index
```bash
pip install sentence-transformers   # first time only
python scripts/rebuild_index.py
```

### Step 4: Restart backend
```bash
uvicorn main:app --reload --port 8000
```

**Expected improvement:** 60-80% fewer "details not available" responses for Bhojpuri users.

---

## Approach 2 — System Prompt Tuning (Already Applied, Free)

Already upgraded in `app/services/rag_service.py` with:
- 4 few-shot examples in English, Hindi, Bhojpuri
- Strict language enforcement rules
- Anti-filler phrase rules
- Separate beginner/detailed mode instructions

**To add your own examples:** Edit `SYSTEM_PROMPT` in `rag_service.py`, restart backend. No retraining needed.

---

## Approach 3 — Fine-Tune a Custom Model

**No Colab needed.** Choose the option that suits you:

| Option | Cost | Time | Difficulty | Best For |
|--------|------|------|------------|----------|
| A – Groq API | Free (beta) | 30min–2hr | ⭐ Easiest | Everyone |
| B – Together AI | ~$1-3 | 30–60 min | ⭐⭐ Easy | Best quality/cost |
| C – HuggingFace | Free tier / ~$2-5 | 1–2 hr | ⭐⭐ Easy | No-code UI |
| D – Modal.com | ~$0.50–1.50 | 20–30 min | ⭐⭐⭐ Dev | Fastest, most control |

### Step 1: Generate training data (required for all options)
```bash
cd backend
python scripts/generate_finetune_data.py
# → Creates data/finetune_dataset.jsonl (~2000+ examples)
```

---

### Option A — Groq Fine-Tuning API (Recommended — Free during beta)

No GPU, no setup. Groq trains it on their infrastructure and you get a hosted model.

```bash
# 1. Start training
python scripts/finetune/option_a_groq.py --upload

# 2. Check status (run again in 30–60 min)
python scripts/finetune/option_a_groq.py --status
```

When complete, update `backend/.env`:
```env
LLM_PROVIDER=groq
LLM_MODEL=ft:llama3-8b-8192:sevasetu:xxxxxxxx   # shown in --status output
```
Restart backend — done.

---

### Option B — Together AI (~$1-3 total)

Best quality/cost ratio. You get $25 free credits on signup.

```bash
# 1. Sign up at https://api.together.ai → get API key
# 2. Add to backend/.env:
#    TOGETHER_API_KEY=your_key_here

# 3. Upload data and start training
python scripts/finetune/option_b_together.py --upload

# 4. Check status
python scripts/finetune/option_b_together.py --status
```

When complete, update `backend/.env`:
```env
LLM_PROVIDER=together
TOGETHER_API_KEY=your_key
TOGETHER_MODEL=your-username/sevasetu-llama3-8b    # shown in --status output
```

---

### Option C — HuggingFace AutoTrain (No-code UI)

Best for non-developers. Free tier available.

```bash
# 1. Sign up at https://huggingface.co
# 2. Add to backend/.env:
#    HF_TOKEN=hf_your_token
#    HF_USERNAME=your_username

# 3. Convert and upload dataset
python scripts/finetune/option_c_huggingface.py --upload
```

Then go to https://ui.autotrain.huggingface.co:
1. New Project → LLM Fine-tuning → SFT
2. Select your uploaded dataset (`your-username/sevasetu-finetune-data`)
3. Base model: `meta-llama/Llama-3.2-3B-Instruct`
4. Text column: `text`
5. Hardware: Free (queued) or A10G Small
6. Click **Train**

When complete, update `backend/.env`:
```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=sevasetu
```
Download model → set up Ollama (see Ollama setup below).

---

### Option D — Modal.com (~$0.50-1.50, No timeouts)

Best for developers. Uses serverless GPU — only pay for actual compute time, no timeouts.

```bash
# 1. Sign up at https://modal.com ($30 free credits)
# 2. Install and authenticate:
pip install modal
modal token new

# 3. Generate the Modal app file + see instructions:
python scripts/finetune/option_d_modal.py

# 4. Upload dataset to Modal volume:
modal volume create sevasetu-training
modal volume put sevasetu-training data/finetune_dataset.jsonl /data/

# 5. Run training (~20-30 min, ~$1):
modal run scripts/finetune/modal_finetune_app.py

# 6. Download trained model:
modal volume get sevasetu-training /data/sevasetu_model ./sevasetu_modal_output
```

---

### After Options C or D — Set Up Ollama (Local Model)

```bash
# 1. Install Ollama: https://ollama.com/download

# 2. Create Modelfile in the output folder:
cat > Modelfile << 'MEOF'
FROM ./sevasetu_modal_output/sevasetu_model
SYSTEM "You are SevaSetu, a warm AI assistant helping Bihar citizens understand government welfare schemes. Reply in the user's language (English, Hindi, or Bhojpuri)."
PARAMETER temperature 0.3
PARAMETER num_predict 600
MEOF

# 3. Import model into Ollama:
ollama create sevasetu -f Modelfile

# 4. Test it:
ollama run sevasetu "PM Kisan के बारे में बताओ"

# 5. Update backend/.env:
#    LLM_PROVIDER=ollama
#    OLLAMA_MODEL=sevasetu
```

---

## Test Quality After Any Change

```bash
cd backend
python scripts/test_responses.py
```

Runs 10 queries (English, Hindi, Bhojpuri) and shows pass/fail for each.

---

## Recommended Order

1. **Run Approach 1** (data enrichment) — free, biggest impact, 30 min
2. **Approach 2** already applied — tweak prompt examples if needed
3. **Approach 3 Option A** (Groq fine-tuning) — free, no setup, try first
4. If you want a permanently hosted fine-tuned model → **Option B** (Together AI)
5. If you want full local control → **Option D** (Modal) → Ollama
