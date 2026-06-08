"""
services/llm/provider.py – LLM provider abstraction layer.

Supported providers:
  - GroqProvider  (default) – cloud, fast, free tier
  - OllamaProvider          – local fine-tuned model (post Approach 3)

Switch providers via LLM_PROVIDER env variable:
  LLM_PROVIDER=groq    → uses GROQ_API_KEY + LLM_MODEL
  LLM_PROVIDER=ollama  → uses local Ollama server
"""
from __future__ import annotations
from typing import Optional


class LLMProvider:
    """Abstract base for all LLM providers."""
    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        raise NotImplementedError


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


# ── Together AI (hosted fine-tuned model) ────────────────────────────────────
class TogetherProvider(LLMProvider):
    """
    Runs your fine-tuned model hosted on Together AI.
    After Approach 3 Option B, set LLM_PROVIDER=together in .env.
    Sign up free at https://api.together.ai ($25 credits)
    """
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


# ── Ollama (local fine-tuned model) ──────────────────────────────────────────
class OllamaProvider(LLMProvider):
    """
    Runs the fine-tuned SevaSetu model locally via Ollama.
    After Approach 3 (fine-tuning), set LLM_PROVIDER=ollama in .env.

    Install Ollama: https://ollama.com/download
    Then: ollama create sevasetu -f Modelfile
    """
    def __init__(self, model: str = "sevasetu", base_url: str = "http://localhost:11434"):
        self.model    = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list, system: str,
             max_tokens: int = 700, temperature: float = 0.4) -> str:
        import httpx
        all_messages = [{"role": "system", "content": system}] + messages
        payload = {
            "model":   self.model,
            "messages": all_messages,
            "stream":  False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
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

        if provider_name == "together":
            together_key   = getattr(settings, "TOGETHER_API_KEY", "")
            together_model = getattr(settings, "TOGETHER_MODEL", "")
            if not together_key or not together_model:
                print("[LLM] TOGETHER_API_KEY or TOGETHER_MODEL not set — falling back to Groq.")
            else:
                _provider = TogetherProvider(api_key=together_key, model=together_model)
                print(f"[LLM] Together AI provider initialised (model: {together_model}).")
                return _provider

        if provider_name == "ollama":
            ollama_url   = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
            ollama_model = getattr(settings, "OLLAMA_MODEL", "sevasetu")
            _provider = OllamaProvider(model=ollama_model, base_url=ollama_url)
            print(f"[LLM] Ollama provider initialised (model: {ollama_model} @ {ollama_url}).")
            return _provider

        # Default → Groq
        if settings.GROQ_API_KEY:
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
