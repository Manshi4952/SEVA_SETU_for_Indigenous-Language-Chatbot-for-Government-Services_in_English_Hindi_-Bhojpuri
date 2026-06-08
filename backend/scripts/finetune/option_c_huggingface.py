"""
scripts/finetune/option_c_huggingface.py
Approach 3 – Option C: Fine-tune using Hugging Face AutoTrain

WHY THIS OPTION:
  - No-code browser UI — upload JSONL, click Train, done
  - Free tier available (limited GPU hours per month)
  - Paid: ~$2-5 using HF Spaces GPU
  - Model saved to your HF Hub repo (private or public)
  - Can run inference via HF Inference API (free for private models)

STEPS:
  1. Create account at https://huggingface.co
  2. Get token from https://huggingface.co/settings/tokens (read+write)
  3. Add to .env: HF_TOKEN=hf_your_token_here
  4. Run generate_finetune_data.py first
  5. Run: python scripts/finetune/option_c_huggingface.py --prepare
     (this converts data to HF format and uploads to your Hub)
  6. Go to https://ui.autotrain.huggingface.co → New Project → LLM Fine-tuning
     Upload the converted file, select your model, click Train
  7. OR run: python scripts/finetune/option_c_huggingface.py --train-api
     (fully automated via HF AutoTrain API)

Cost: Free with HF free GPU tier (may queue), or ~$0.60/hr with A10G
"""
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

HF_TOKEN   = os.getenv("HF_TOKEN", "")
HF_USERNAME = os.getenv("HF_USERNAME", "")  # Your HF username
JSONL_PATH  = os.path.join(os.path.dirname(__file__), "../../data/finetune_dataset.jsonl")
HF_REPO_ID  = f"{HF_USERNAME}/sevasetu-finetune-data" if HF_USERNAME else "your-username/sevasetu-finetune-data"

BASE_MODEL  = "meta-llama/Llama-3.2-3B-Instruct"  # Smallest — fits HF free tier


def prepare_hf_format():
    """Convert to HF AutoTrain chat format and save locally."""
    out_path = JSONL_PATH.replace(".jsonl", "_hf.jsonl")
    count = 0

    with open(JSONL_PATH, encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line: continue
            ex  = json.loads(line)
            # HF AutoTrain expects {"text": "<full_conversation>"} format
            msgs = ex["messages"]
            # Build chat format
            chat_parts = []
            for msg in msgs:
                role    = msg["role"]
                content = msg["content"]
                if role == "system":
                    chat_parts.append(f"<|system|>\n{content}</s>")
                elif role == "user":
                    chat_parts.append(f"<|user|>\n{content}</s>")
                elif role == "assistant":
                    chat_parts.append(f"<|assistant|>\n{content}</s>")
            fout.write(json.dumps({"text": "\n".join(chat_parts)}, ensure_ascii=False) + "\n")
            count += 1

    print(f"✅ Converted {count} examples → {out_path}")
    print(f"\nFor HF AutoTrain UI:")
    print(f"  1. Go to https://ui.autotrain.huggingface.co")
    print(f"  2. New Project → LLM Fine-tuning → Supervised Fine-tuning (SFT)")
    print(f"  3. Upload: {out_path}")
    print(f"  4. Base model: {BASE_MODEL}")
    print(f"  5. Text column: 'text'")
    print(f"  6. Hardware: Free (queued) or A10G Small (~$0.60/hr)")
    print(f"  7. Click Train")
    return out_path


def upload_to_hub(filepath: str):
    """Upload dataset to HF Hub so AutoTrain can access it."""
    try:
        from huggingface_hub import HfApi, login
    except ImportError:
        print("Run: pip install huggingface-hub")
        sys.exit(1)

    if not HF_TOKEN:
        print("ERROR: HF_TOKEN not set in .env")
        sys.exit(1)

    login(token=HF_TOKEN)
    api = HfApi()

    # Create dataset repo
    try:
        api.create_repo(repo_id=HF_REPO_ID, repo_type="dataset", private=True)
        print(f"✅ Created private dataset repo: {HF_REPO_ID}")
    except Exception:
        print(f"ℹ️  Repo {HF_REPO_ID} already exists, uploading file...")

    api.upload_file(
        path_or_fileobj=filepath,
        path_in_repo="train.jsonl",
        repo_id=HF_REPO_ID,
        repo_type="dataset",
    )
    print(f"✅ Dataset uploaded to: https://huggingface.co/datasets/{HF_REPO_ID}")
    print(f"\nIn AutoTrain UI, select 'Hub Dataset' and enter: {HF_REPO_ID}")


def train_via_api():
    """Fully automated fine-tuning via HF AutoTrain API."""
    try:
        import httpx
    except ImportError:
        print("Run: pip install httpx")
        sys.exit(1)

    if not HF_TOKEN or not HF_USERNAME:
        print("ERROR: Set HF_TOKEN and HF_USERNAME in .env")
        sys.exit(1)

    print("Starting AutoTrain job via API...")
    payload = {
        "username":   HF_USERNAME,
        "project_name": "sevasetu-llm",
        "task":       "llm-sft",
        "base_model": BASE_MODEL,
        "hub_dataset": HF_REPO_ID,
        "hub_col":    "text",
        "hardware":   "spaces-a10g-small",  # or "spaces-t4-medium" for cheaper
        "params": {
            "epochs":       3,
            "batch_size":   4,
            "lr":           2e-4,
            "peft":         True,   # LoRA
            "quantization": "int4", # 4-bit quantization
            "trainer":      "sft",
            "model_max_length": 2048,
            "use_flash_attention_2": True,
        },
    }
    resp = httpx.post(
        "https://ui.autotrain.huggingface.co/api/create_project",
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
        json=payload,
        timeout=30.0,
    )
    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ Training started!")
        print(f"   Monitor at: https://huggingface.co/{HF_USERNAME}/sevasetu-llm")
        print(f"   Result: {result}")
    else:
        print(f"❌ API error {resp.status_code}: {resp.text}")
        print("Try the UI approach instead: https://ui.autotrain.huggingface.co")


def main():
    parser = argparse.ArgumentParser(description="HuggingFace AutoTrain for SevaSetu")
    parser.add_argument("--prepare",    action="store_true", help="Convert data to HF format")
    parser.add_argument("--upload",     action="store_true", help="Upload dataset to HF Hub")
    parser.add_argument("--train-api",  action="store_true", help="Start training via AutoTrain API")
    args = parser.parse_args()

    if args.prepare:
        prepare_hf_format()
    elif args.upload:
        filepath = prepare_hf_format()
        upload_to_hub(filepath)
    elif args.train_api:
        filepath = prepare_hf_format()
        upload_to_hub(filepath)
        train_via_api()
    else:
        prepare_hf_format()  # Default: just convert


if __name__ == "__main__":
    main()
