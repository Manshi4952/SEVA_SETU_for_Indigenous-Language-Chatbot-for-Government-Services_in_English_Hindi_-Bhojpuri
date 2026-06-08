"""
scripts/finetune/option_a_groq.py
Approach 3 – Option A: Fine-tune using Groq Fine-Tuning API

WHY THIS OPTION:
  - No GPU required — Groq handles all compute
  - Uses same GROQ_API_KEY you already have
  - Model hosted on Groq — same speed as current setup
  - Cost: Currently FREE during Groq's fine-tuning beta

STEPS:
  1. Run generate_finetune_data.py first to create finetune_dataset.jsonl
  2. Run: python scripts/finetune/option_a_groq.py --upload
  3. Wait for training email (usually 30 min – 2 hours)
  4. Run: python scripts/finetune/option_a_groq.py --status
  5. Update .env with your new model ID

Docs: https://console.groq.com/docs/fine-tuning
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
JSONL_PATH   = os.path.join(os.path.dirname(__file__), "../../data/finetune_dataset.jsonl")
JOB_ID_FILE  = os.path.join(os.path.dirname(__file__), "../../data/groq_job_id.txt")

# Groq fine-tuning only supports specific base models
SUPPORTED_BASE_MODELS = [
    "llama3-8b-8192",          # Llama 3 8B — recommended (fast, cheap)
    "llama3-70b-8192",         # Llama 3 70B — higher quality, more cost
    "gemma2-9b-it",            # Gemma 2 9B
]
BASE_MODEL = "llama3-8b-8192"


def validate_dataset():
    """Validate JSONL format before uploading."""
    if not os.path.exists(JSONL_PATH):
        print(f"ERROR: {JSONL_PATH} not found.")
        print("Run: python scripts/generate_finetune_data.py first.")
        sys.exit(1)

    errors = []
    count  = 0
    with open(JSONL_PATH, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
                msgs = ex.get("messages", [])
                if len(msgs) < 2:
                    errors.append(f"Line {i}: less than 2 messages")
                    continue
                roles = [m["role"] for m in msgs]
                if "assistant" not in roles:
                    errors.append(f"Line {i}: no assistant message")
                count += 1
            except json.JSONDecodeError as e:
                errors.append(f"Line {i}: JSON error — {e}")

    if errors:
        print(f"Dataset validation FAILED ({len(errors)} errors):")
        for e in errors[:10]: print(f"  {e}")
        sys.exit(1)

    print(f"✅ Dataset valid: {count} training examples")
    return count


def split_dataset(count: int):
    """
    Groq requires a separate validation file.
    Split 90% train / 10% validation.
    """
    examples = []
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(line)

    import random
    random.seed(42)
    random.shuffle(examples)

    split_idx  = int(len(examples) * 0.9)
    train_data = examples[:split_idx]
    val_data   = examples[split_idx:]

    train_path = JSONL_PATH.replace(".jsonl", "_train.jsonl")
    val_path   = JSONL_PATH.replace(".jsonl", "_val.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        f.write("\n".join(train_data))
    with open(val_path, "w", encoding="utf-8") as f:
        f.write("\n".join(val_data))

    print(f"✅ Split: {len(train_data)} train / {len(val_data)} validation")
    return train_path, val_path


def upload_file(filepath: str, purpose: str) -> str:
    import httpx
    print(f"Uploading {os.path.basename(filepath)}...")
    with open(filepath, "rb") as f:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/files",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": (os.path.basename(filepath), f, "application/jsonl")},
            data={"purpose": purpose},
            timeout=120.0,
        )
    resp.raise_for_status()
    file_id = resp.json()["id"]
    print(f"✅ Uploaded: {file_id}")
    return file_id


def create_job(train_file_id: str, val_file_id: str) -> str:
    import httpx
    print(f"Creating fine-tuning job (base model: {BASE_MODEL})...")
    payload = {
        "training_file":   train_file_id,
        "validation_file": val_file_id,
        "model":           BASE_MODEL,
        "hyperparameters": {
            "n_epochs":       3,
            "learning_rate_multiplier": 0.1,
        },
        "suffix": "sevasetu",
    }
    resp = httpx.post(
        "https://api.groq.com/openai/v1/fine_tuning/jobs",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    job_id = resp.json()["id"]
    print(f"✅ Job created: {job_id}")
    # Save job ID for later status checks
    with open(JOB_ID_FILE, "w") as f:
        f.write(job_id)
    return job_id


def check_status(job_id: str = None):
    import httpx
    if not job_id and os.path.exists(JOB_ID_FILE):
        with open(JOB_ID_FILE) as f:
            job_id = f.read().strip()
    if not job_id:
        print("No job ID found. Run with --upload first.")
        sys.exit(1)

    resp = httpx.get(
        f"https://api.groq.com/openai/v1/fine_tuning/jobs/{job_id}",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    status     = data.get("status", "unknown")
    model_id   = data.get("fine_tuned_model", "not ready yet")
    created_at = data.get("created_at", "")

    print(f"\n{'='*50}")
    print(f"Job ID:     {job_id}")
    print(f"Status:     {status}")
    print(f"Model:      {model_id}")
    print(f"Created:    {created_at}")
    print(f"{'='*50}")

    if status == "succeeded":
        print(f"\n✅ Training complete! Your model ID: {model_id}")
        print(f"\nUpdate backend/.env:")
        print(f"  LLM_PROVIDER=groq")
        print(f"  LLM_MODEL={model_id}")
        print(f"\nRestart backend — done!")
    elif status == "failed":
        error = data.get("error", {})
        print(f"\n❌ Training failed: {error}")
    else:
        print(f"\n⏳ Still training... check again in 15 minutes.")
        print(f"   Run: python scripts/finetune/option_a_groq.py --status")


def main():
    parser = argparse.ArgumentParser(description="Groq Fine-Tuning for SevaSetu")
    parser.add_argument("--upload",   action="store_true", help="Upload data and start training")
    parser.add_argument("--status",   action="store_true", help="Check training job status")
    parser.add_argument("--job-id",   type=str, default=None, help="Specific job ID to check")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in .env")
        sys.exit(1)

    if args.status:
        check_status(args.job_id)
    elif args.upload:
        count = validate_dataset()
        train_path, val_path = split_dataset(count)
        train_id = upload_file(train_path, "fine-tune")
        val_id   = upload_file(val_path,   "fine-tune")
        job_id   = create_job(train_id, val_id)
        print(f"\n⏳ Training started! Job ID saved to {JOB_ID_FILE}")
        print(f"   Check status: python scripts/finetune/option_a_groq.py --status")
        print(f"   Estimated time: 30 min – 2 hours")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
