"""
scripts/finetune_colab.py
Approach 3 – Step 2: Fine-tune Llama-3-8B on Google Colab (FREE T4 GPU).

HOW TO USE:
  1. Run generate_finetune_data.py first to create data/finetune_dataset.jsonl
  2. Go to https://colab.research.google.com
  3. Create a new notebook → Runtime → Change runtime type → T4 GPU
  4. Upload finetune_dataset.jsonl to Colab Files panel
  5. Copy-paste this entire script into a code cell and run it
  6. After training, download sevasetu_model/ folder
  7. Run with Ollama locally (see instructions at bottom)

Estimated time: 15-30 minutes on T4 GPU
Cost: FREE on Colab free tier
"""

# ============================================================
# CELL 1: Install dependencies
# ============================================================
INSTALL = """
!pip install -q unsloth
!pip install -q xformers trl peft accelerate bitsandbytes
"""

# ============================================================
# CELL 2: Load model and training data
# ============================================================
TRAIN_SCRIPT = '''
import json
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# ── 1. Load base model (4-bit quantized = fits in 15GB T4) ──
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

# ── 2. Add LoRA adapters (trains only 1-3% of params) ──
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                  # LoRA rank
    target_modules=["q_proj","k_proj","v_proj","o_proj",
                    "gate_proj","up_proj","down_proj"],
    lora_alpha=16,
    lora_dropout=0.05,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# ── 3. Load SevaSetu dataset ──
examples = []
with open("finetune_dataset.jsonl", encoding="utf-8") as f:
    for line in f:
        ex = json.loads(line)
        messages = ex["messages"]
        # Format as Llama-3 chat template
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        examples.append({"text": text})

dataset = Dataset.from_list(examples)
print(f"Training examples: {len(dataset)}")

# ── 4. Training config ──
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    args=TrainingArguments(
        output_dir="./sevasetu_checkpoints",
        num_train_epochs=2,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=50,
        save_steps=200,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        report_to="none",
    ),
)

# ── 5. Train ──
print("Starting training...")
trainer.train()

# ── 6. Save merged model for Ollama ──
print("Saving model...")
model.save_pretrained_merged(
    "sevasetu_model",
    tokenizer,
    save_method="merged_16bit",  # Full merged weights
)
print("✅ Model saved to sevasetu_model/")
print("Download this folder and follow the Ollama instructions below.")
'''

# ============================================================
# CELL 3: Export to GGUF for Ollama (run after training)
# ============================================================
EXPORT_SCRIPT = '''
# Convert to GGUF format for Ollama
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained("sevasetu_model")
model.save_pretrained_gguf(
    "sevasetu_gguf",
    tokenizer,
    quantization_method="q4_k_m",  # Good quality/size balance
)
print("✅ GGUF model saved to sevasetu_gguf/")
print("Files:", os.listdir("sevasetu_gguf"))
'''

INSTRUCTIONS = """
============================================================
AFTER TRAINING: Run the model locally with Ollama
============================================================

1. Install Ollama: https://ollama.com/download

2. Create a Modelfile (create a file named 'Modelfile'):

   FROM ./sevasetu_gguf/sevasetu-model-q4_k_m.gguf
   SYSTEM "You are SevaSetu, a warm AI assistant helping Bihar citizens understand government welfare schemes. Reply in the user's language (English, Hindi, or Bhojpuri)."
   PARAMETER temperature 0.3
   PARAMETER num_predict 500

3. Import the model:
   ollama create sevasetu -f Modelfile

4. Test it:
   ollama run sevasetu "PM Kisan के बारे में बताओ"

5. Update backend/app/services/llm/provider.py to use OllamaProvider:
   Set LLM_PROVIDER=ollama in backend/.env

The provider.py already has OllamaProvider ready — just set the env variable!
============================================================
"""

if __name__ == "__main__":
    print("This script is meant to be run in Google Colab.")
    print("Copy the TRAIN_SCRIPT and EXPORT_SCRIPT sections to Colab cells.")
    print(INSTRUCTIONS)
