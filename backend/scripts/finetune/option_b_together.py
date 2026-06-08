"""
scripts/finetune/option_b_together.py
Approach 3 – Option B: Fine-tune using Together AI

WHY THIS OPTION:
  - Cheapest paid option — ~$1-3 total for your dataset size
  - Supports Llama-3.1-8B and Llama-3.1-70B
  - Model stays hosted on Together AI (fast inference)
  - No GPU setup needed
  - Better than Colab — no session timeouts, full control

STEPS:
  1. Sign up at https://api.together.ai (get $25 free credits)
  2. Get API key from https://api.together.ai/settings/api-keys
  3. Add to backend/.env: TOGETHER_API_KEY=your_key_here
  4. Run generate_finetune_data.py to create finetune_dataset.jsonl
  5. Run: python scripts/finetune/option_b_together.py --upload
  6. Wait 30–60 min, then: python scripts/finetune/option_b_together.py --status
  7. Update .env: LLM_PROVIDER=together, LLM_MODEL=your_model_id

Cost estimate for SevaSetu (~2000 examples):
  Llama-3.1-8B:  ~$1.50  (recommended)
  Llama-3.1-70B: ~$12.00 (overkill for this use case)

Docs: https://docs.together.ai/docs/fine-tuning
"""
import os, sys, json, argparse, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
JSONL_PATH       = os.path.join(os.path.dirname(__file__), "../../data/finetune_dataset.jsonl")
JOB_ID_FILE      = os.path.join(os.path.dirname(__file__), "../../data/together_job_id.txt")

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Reference"


def convert_to_together_format():
    """
    Together AI uses a slightly different format than OpenAI.
    Convert our messages format to Together's prompt format.
    """
    out_path = JSONL_PATH.replace(".jsonl", "_together.jsonl")
    count = 0

    with open(JSONL_PATH, encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line: continue
            ex = json.loads(line)
            msgs = ex["messages"]

            # Build Llama-3 style prompt
            prompt = ""
            completion = ""
            for msg in msgs:
                role    = msg["role"]
                content = msg["content"]
                if role == "system":
                    prompt += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{content}<|eot_id|>\n"
                elif role == "user":
                    prompt += f"<|start_header_id|>user<|end_header_id|>\n{content}<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>\n"
                elif role == "assistant":
                    completion = content + "<|eot_id|>"

            if prompt and completion:
                fout.write(json.dumps({"prompt": prompt, "completion": completion}, ensure_ascii=False) + "\n")
                count += 1

    print(f"✅ Converted {count} examples → {out_path}")
    return out_path


def upload_file(filepath: str) -> str:
    import httpx
    print(f"Uploading {os.path.basename(filepath)} to Together AI...")
    with open(filepath, "rb") as f:
        resp = httpx.post(
            "https://api.together.xyz/v1/files",
            headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
            files={"file": (os.path.basename(filepath), f, "application/jsonl")},
            data={"purpose": "fine-tune"},
            timeout=180.0,
        )
    resp.raise_for_status()
    file_id = resp.json()["id"]
    print(f"✅ Uploaded: {file_id}")
    return file_id


def create_job(file_id: str) -> str:
    import httpx
    print(f"Creating fine-tuning job...")
    payload = {
        "training_file": file_id,
        "model":         BASE_MODEL,
        "n_epochs":      3,
        "batch_size":    16,
        "learning_rate": 0.00003,
        "suffix":        "sevasetu",
        "warmup_ratio":  0.05,
        "lora":          True,      # LoRA = faster, cheaper, same quality
        "lora_r":        16,
    }
    resp = httpx.post(
        "https://api.together.xyz/v1/fine-tunes",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=30.0,
    )
    resp.raise_for_status()
    result = resp.json()
    job_id = result["id"]
    print(f"✅ Job created: {job_id}")
    with open(JOB_ID_FILE, "w") as f:
        f.write(job_id)
    return job_id


def check_status(job_id: str = None):
    import httpx
    if not job_id and os.path.exists(JOB_ID_FILE):
        with open(JOB_ID_FILE) as f:
            job_id = f.read().strip()
    if not job_id:
        print("No job ID. Run with --upload first.")
        sys.exit(1)

    resp = httpx.get(
        f"https://api.together.xyz/v1/fine-tunes/{job_id}",
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data   = resp.json()
    status = data.get("status", "unknown")
    model  = data.get("output_name", "not ready")
    events = data.get("events", [])

    print(f"\n{'='*50}")
    print(f"Job ID:  {job_id}")
    print(f"Status:  {status}")
    print(f"Model:   {model}")
    if events:
        print(f"Latest:  {events[-1].get('message','')}")
    print(f"{'='*50}")

    if status == "complete":
        print(f"\n✅ Training complete! Model: {model}")
        print(f"\nAdd to backend/.env:")
        print(f"  LLM_PROVIDER=together")
        print(f"  TOGETHER_MODEL={model}")
        print(f"  TOGETHER_API_KEY=<your key>")
        print(f"\nRestart backend — done!")
    elif status in ("error", "failed"):
        print(f"\n❌ Failed. Check Together AI dashboard.")
    else:
        print(f"\n⏳ Still training... check again in 15 min.")
        print(f"   python scripts/finetune/option_b_together.py --status")


def main():
    parser = argparse.ArgumentParser(description="Together AI Fine-Tuning for SevaSetu")
    parser.add_argument("--upload", action="store_true", help="Upload data and start training")
    parser.add_argument("--status", action="store_true", help="Check job status")
    parser.add_argument("--job-id", type=str, default=None)
    args = parser.parse_args()

    if not TOGETHER_API_KEY:
        print("ERROR: TOGETHER_API_KEY not set in .env")
        print("Sign up free at https://api.together.ai — you get $25 credits")
        sys.exit(1)

    if args.status:
        check_status(args.job_id)
    elif args.upload:
        converted = convert_to_together_format()
        file_id   = upload_file(converted)
        job_id    = create_job(file_id)
        print(f"\n⏳ Training started! (~30-60 min)")
        print(f"   python scripts/finetune/option_b_together.py --status")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
