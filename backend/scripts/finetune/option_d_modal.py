"""
scripts/finetune/option_d_modal.py
Approach 3 – Option D: Fine-tune using Modal.com (Serverless GPU)

WHY THIS OPTION:
  - No session timeouts — unlike Colab, Modal runs to completion
  - Pay per second of actual GPU use — no idle billing
  - ~$0.50-1.50 total for our dataset (A100 @ $0.000463/GPU-sec)
  - $30 free credit on signup — enough for many training runs
  - Clean Python code — no Jupyter, no browser needed
  - Best option if you're comfortable with terminal

STEPS:
  1. Sign up at https://modal.com (get $30 free credits)
  2. pip install modal
  3. modal token new  (authenticates your machine)
  4. Run generate_finetune_data.py first
  5. Run: python scripts/finetune/option_d_modal.py
  6. Wait ~20-30 minutes — model downloads to ./sevasetu_modal_output/
  7. Set up Ollama with the downloaded model (see instructions at bottom)

Cost: ~$0.50-1.50 for our ~2000 example dataset
GPU: A100-40GB (fastest) or A10G (cheaper)
"""
# ── The actual Modal app code ────────────────────────────────────────────────
MODAL_APP_CODE = '''
# modal_finetune_app.py
# Run with: modal run modal_finetune_app.py

import modal, os, json

# ── Modal setup ──────────────────────────────────────────────────────────────
app   = modal.App("sevasetu-finetune")
vol   = modal.Volume.from_name("sevasetu-training", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.3.0",
        "transformers==4.43.0",
        "datasets==2.20.0",
        "peft==0.11.1",
        "trl==0.9.4",
        "accelerate==0.31.0",
        "bitsandbytes==0.43.1",
        "sentencepiece",
        "protobuf",
    )
)

DATASET_PATH = "/data/finetune_dataset.jsonl"
OUTPUT_PATH  = "/data/sevasetu_model"
BASE_MODEL   = "meta-llama/Meta-Llama-3.1-8B-Instruct"

SYSTEM_MSG = (
    "You are SevaSetu, a warm and knowledgeable AI assistant helping citizens of Bihar "
    "understand government welfare schemes. Reply in the user\'s language (English, Hindi, or Bhojpuri)."
)


@app.function(
    image=image,
    gpu=modal.gpu.A10G(),          # Change to A100() for fastest training
    timeout=7200,                   # 2 hour timeout (more than enough)
    volumes={"/data": vol},
    secrets=[modal.Secret.from_name("huggingface-secret")],  # For gated models
)
def train():
    import torch
    from datasets import Dataset
    from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
    from peft import LoraConfig, get_peft_model, TaskType
    from trl import SFTTrainer
    import json

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # ── Load tokenizer ────────────────────────────────────────────────────────
    hf_token = os.environ.get("HF_TOKEN", "")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, token=hf_token)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ── Load dataset ─────────────────────────────────────────────────────────
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"{DATASET_PATH} not found. "
            "Upload it first: modal volume put sevasetu-training finetune_dataset.jsonl /data/"
        )

    examples = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            ex   = json.loads(line)
            msgs = ex["messages"]
            text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
            examples.append({"text": text})

    dataset = Dataset.from_list(examples)
    print(f"Training examples: {len(dataset)}")

    # ── Load model (4-bit quantized) ─────────────────────────────────────────
    from transformers import BitsAndBytesConfig
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        token=hf_token,
    )
    model.config.use_cache = False

    # ── LoRA adapters ─────────────────────────────────────────────────────────
    lora_config = LoraConfig(
        r=16,
        lora_alpha=16,
        target_modules=["q_proj","k_proj","v_proj","o_proj",
                        "gate_proj","up_proj","down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Training ──────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            output_dir=OUTPUT_PATH,
            num_train_epochs=3,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            bf16=True,
            logging_steps=25,
            save_steps=100,
            warmup_ratio=0.05,
            lr_scheduler_type="cosine",
            report_to="none",
        ),
    )
    print("Starting training...")
    trainer.train()

    # ── Save merged model ─────────────────────────────────────────────────────
    print("Merging LoRA weights and saving...")
    trainer.model.save_pretrained(OUTPUT_PATH + "_lora")
    trainer.tokenizer.save_pretrained(OUTPUT_PATH + "_lora")

    # Merge for easier inference
    from peft import PeftModel
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, torch_dtype=torch.float16, token=hf_token
    )
    merged = PeftModel.from_pretrained(base_model, OUTPUT_PATH + "_lora")
    merged = merged.merge_and_unload()
    merged.save_pretrained(OUTPUT_PATH)
    tokenizer.save_pretrained(OUTPUT_PATH)

    vol.commit()
    print(f"✅ Model saved to Modal volume at {OUTPUT_PATH}")
    print("Download with: modal volume get sevasetu-training /data/sevasetu_model ./sevasetu_modal_output")


@app.local_entrypoint()
def main():
    train.remote()
'''

import os, sys, textwrap

SCRIPT_DIR   = os.path.dirname(__file__)
APP_PATH     = os.path.join(SCRIPT_DIR, "modal_finetune_app.py")
JSONL_PATH   = os.path.join(SCRIPT_DIR, "../../data/finetune_dataset.jsonl")


def write_app():
    with open(APP_PATH, "w", encoding="utf-8") as f:
        f.write(MODAL_APP_CODE)
    print(f"✅ Modal app written to: {APP_PATH}")


def check_setup():
    issues = []
    if not os.path.exists(JSONL_PATH):
        issues.append("finetune_dataset.jsonl not found — run generate_finetune_data.py first")
    try:
        import modal
    except ImportError:
        issues.append("modal not installed — run: pip install modal")
    if issues:
        print("Setup issues:")
        for i in issues: print(f"  ❌ {i}")
        sys.exit(1)
    print("✅ Setup looks good")


def print_instructions():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Modal.com Fine-Tuning — Step by Step                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Sign up: https://modal.com  ($30 free credits)          ║
║                                                              ║
║  2. Install & authenticate:                                  ║
║     pip install modal                                        ║
║     modal token new                                          ║
║                                                              ║
║  3. Generate training data (if not done):                    ║
║     python scripts/generate_finetune_data.py                 ║
║                                                              ║
║  4. Upload dataset to Modal volume:                          ║
║     modal volume create sevasetu-training                    ║
║     modal volume put sevasetu-training \\                     ║
║       data/finetune_dataset.jsonl /data/                     ║
║                                                              ║
║  5. (Optional) For gated models like Llama-3:                ║
║     modal secret create huggingface-secret \\                 ║
║       HF_TOKEN=hf_your_token_here                            ║
║                                                              ║
║  6. Run training (~20-30 min, ~$1):                          ║
║     modal run scripts/finetune/modal_finetune_app.py         ║
║                                                              ║
║  7. Download model:                                          ║
║     modal volume get sevasetu-training \\                     ║
║       /data/sevasetu_model ./sevasetu_modal_output           ║
║                                                              ║
║  8. Set up Ollama (see TRAINING_GUIDE.md Step 3)             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    write_app()
    check_setup()
    print_instructions()
