"""
services/llm/provider.py – LLM provider abstraction layer.

Supported providers (set via LLM_PROVIDER in .env):
  groq     → Groq cloud API         (default, recommended)
  local    → Local LoRA adapter      (requires GPU + base model download ~16GB)
  together → Together AI hosted model
  ollama   → Local Ollama server
"""
from __future__ import annotations
from typing import Optional


class LLMProvider:
    """Abstract base for all LLM providers."""
    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        raise NotImplementedError


# ── Local Fine-Tuned LoRA Provider ────────────────────────────────────────────
class LocalLoraProvider(LLMProvider):
    """
    Loads your Colab-trained LoRA adapter on top of the base Llama-3.1-8B model.

    REQUIREMENTS before using this provider:
      1. GPU with 16GB+ VRAM (or 32GB+ RAM for CPU-only, very slow)
      2. First run will download ~16GB base model from HuggingFace
      3. Set in .env:
           LLM_PROVIDER=local
           LLM_MODEL=data/sevasetu_lora_model

    For local Windows machines without GPU, use LLM_PROVIDER=groq instead.
    """
    def __init__(self, model_path: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        print(f"[LLM] Initialising Local LoRA Model from '{model_path}'...")
        base_model_name = "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit"

        # use_fast=True — tokenizer.json (fast tokenizer) is present in the
        # adapter folder; use_fast=False would require tokenizer.model
        # (sentencepiece) which Unsloth does not save in the adapter directory.
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            use_fast=True,
        )

        # Explicit Llama-3 chat template — overrides any template saved by
        # Unsloth that may reference unsupported dictionary-style variables.
        self.tokenizer.chat_template = (
            "{% for message in messages %}"
            "{% if message['role'] == 'system' %}"
            "{{ '<|start_header_id|>system<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}"
            "{% elif message['role'] == 'user' %}"
            "{{ '<|start_header_id|>user<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}"
            "{% elif message['role'] == 'assistant' %}"
            "{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' + message['content'] + '<|eot_id|>' }}"
            "{% endif %}"
            "{% endfor %}"
            "{% if add_generation_prompt %}"
            "{{ '<|start_header_id|>assistant<|end_header_id|>\n\n' }}"
            "{% endif %}"
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cpu":
            print("[LLM] ⚠️  No GPU detected — loading on CPU (slow). Consider using LLM_PROVIDER=groq instead.")

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            low_cpu_mem_usage=True,
        )
        self.model = PeftModel.from_pretrained(base_model, model_path)
        self.model.eval()
        print("✅ Local SevaSetu Fine-Tuned Model loaded successfully!")

    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        import torch
        all_messages = [{"role": "system", "content": system}] + messages
        prompt = self.tokenizer.apply_chat_template(
            all_messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer([prompt], return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=(
                    self.tokenizer.eos_token_id
                    if self.tokenizer.eos_token_id is not None
                    else 128009
                ),
            )
        # Strip the prompt tokens from the output
        generated_ids = [
            output[len(inp):]
            for inp, output in zip(inputs.input_ids, generated_ids)
        ]
        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()


# ── Groq ──────────────────────────────────────────────────────────────────────
class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from groq import Groq
        self.client = Groq(api_key=api_key)
        self.model  = model

    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        all_messages = [{"role": "system", "content": system}] + messages
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content


# ── Together AI ───────────────────────────────────────────────────────────────
class TogetherProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model   = model

    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        import httpx
        all_messages = [{"role": "system", "content": system}] + messages
        resp = httpx.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       self.model,
                "messages":    all_messages,
                "max_tokens":  max_tokens,
                "temperature": temperature,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ── Ollama ────────────────────────────────────────────────────────────────────
class OllamaProvider(LLMProvider):
    """
    Runs your GGUF fine-tuned model locally via Ollama.
    Setup:
      1. Install Ollama: https://ollama.com/download
      2. ollama create sevasetu -f Modelfile
      3. Set LLM_PROVIDER=ollama in .env
    """
    def __init__(self, model: str = "sevasetu", base_url: str = "http://localhost:11434"):
        self.model    = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        import httpx
        all_messages = [{"role": "system", "content": system}] + messages
        resp = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model":    self.model,
                "messages": all_messages,
                "stream":   False,
                "options":  {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]


# ── Singleton ─────────────────────────────────────────────────────────────────
_provider: Optional[LLMProvider] = None


def get_provider() -> Optional[LLMProvider]:
    global _provider
    if _provider is not None:
        return _provider

    try:
        from app.core.config import settings
        provider_name = getattr(settings, "LLM_PROVIDER", "groq").lower()

        if provider_name == "local":
            model_path = getattr(settings, "LLM_MODEL", "data/sevasetu_lora_model")
            _provider = LocalLoraProvider(model_path=model_path)
            return _provider

        if provider_name == "together":
            key   = getattr(settings, "TOGETHER_API_KEY", "")
            model = getattr(settings, "TOGETHER_MODEL", "")
            if not key or not model:
                print("[LLM] TOGETHER_API_KEY or TOGETHER_MODEL not set — falling back to Groq.")
            else:
                _provider = TogetherProvider(api_key=key, model=model)
                print(f"[LLM] Together AI provider initialised (model: {model}).")
                return _provider

        if provider_name == "ollama":
            url   = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
            model = getattr(settings, "OLLAMA_MODEL", "sevasetu")
            _provider = OllamaProvider(model=model, base_url=url)
            print(f"[LLM] Ollama provider initialised (model: {model} @ {url}).")
            return _provider

        # Default → Groq
        if getattr(settings, "GROQ_API_KEY", ""):
            _provider = GroqProvider(
                api_key=settings.GROQ_API_KEY,
                model=settings.LLM_MODEL,
            )
            print(f"[LLM] Groq provider initialised (model: {settings.LLM_MODEL}).")
            return _provider

    except Exception as e:
        print(f"[LLM] Failed to initialise provider: {e}")

    print("[LLM] No provider configured – running in template-only mode.")
    return None


def reset_provider():
    """Force re-initialisation on next call (useful for tests)."""
    global _provider
    _provider = None