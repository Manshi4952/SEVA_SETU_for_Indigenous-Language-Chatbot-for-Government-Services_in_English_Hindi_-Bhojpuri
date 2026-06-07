"""
llm_service.py – Tool-driven answer generation via an OpenAI-compatible LLM.

Flow (what the model actually does):
  1. It reads ONLY the user's message — no scheme data is pre-stuffed into the
     prompt, so the context stays small.
  2. It detects the user's language (English / Hindi / Bhojpuri) on its own.
  3. It figures out which scheme the user is asking about and calls the
     relevant tool to fetch the facts, passing the detected language so the
     tool returns content in that same language.
  4. It writes the final reply in the user's language, grounded on the tool
     results (never inventing scheme facts).

Tools exposed to the model:
  • list_schemes()                     – catalogue of available schemes (ids + names)
  • get_scheme_details(scheme_id, language) – grounded facts for one scheme

Uses OpenRouter (configurable via `LLM_BASE_URL` / `LLM_MODEL`) with the key in
`OPENAI_API_KEY`. If no key is configured or the call fails, callers fall back
to the template-based responses in `rag_service`.
"""
from __future__ import annotations
import json
import time
import uuid
from typing import Dict, List, Optional, Tuple

import httpx

from app.core.config import settings
from app.core.logging_config import get_ai_logger

log = get_ai_logger()

# How many tool-call ↔ result round-trips we allow before forcing an answer.
MAX_TOOL_ITERATIONS = 5

_LANG_NAME = {
    "english": "English",
    "hindi": "Hindi (Devanagari)",
    "bhojpuri": "Bhojpuri (Devanagari)",
}
_SUPPORTED_LANGS = list(_LANG_NAME.keys())


def is_enabled() -> bool:
    return bool(settings.OPENAI_API_KEY)


def _truncate(text: str, limit: int = 500) -> str:
    """Shorten long strings for INFO-level logs (full text still hits DEBUG)."""
    if text is None:
        return ""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"… (+{len(text) - limit} chars)"


# ── System prompt ───────────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    return (
        "You are SevaSetu, a friendly AI assistant for Indian government welfare "
        "schemes, helping rural citizens.\n"
        "\n"
        "LANGUAGE — this is critical:\n"
        "• The user may write in English, Hindi, or Bhojpuri.\n"
        "• Detect the language of the user's message yourself.\n"
        "• ALWAYS write your final reply in that SAME language "
        "(english, hindi, or bhojpuri). Hindi and Bhojpuri must use Devanagari script.\n"
        "• When you call a tool, pass that detected language so the facts come "
        "back in the user's language.\n"
        "\n"
        "USING TOOLS:\n"
        "• Figure out which scheme the user is asking about. If unsure of the "
        "exact scheme or its id, call `list_schemes` first.\n"
        "• Call `get_scheme_details` to fetch facts (benefits, eligibility, age "
        "limits, how to apply). Use ONLY the facts the tools return — never "
        "invent amounts, eligibility, or application steps.\n"
        "• You may call tools for more than one scheme if the user asks about "
        "several.\n"
        "\n"
        "STYLE:\n"
        "• Answer greetings, small talk and general questions naturally without "
        "tools.\n"
        "• If the requested detail isn't available, say what you do know and "
        "invite them to ask about PM-KISAN, PMJJBY, APY, PMAY, or PMSBY.\n"
        "• Keep replies concise and clear for a rural citizen. Reply in plain "
        "text (no JSON)."
    )


# ── Tool definitions ──────────────────────────────────────────────────────────

def _build_tools(scheme_ids: List[str]) -> List[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "list_schemes",
                "description": (
                    "List every government scheme SevaSetu knows about, with its "
                    "id and name. Call this when you are not sure which scheme the "
                    "user means or need the correct scheme_id."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": _SUPPORTED_LANGS,
                            "description": "The user's language, for any localized names.",
                        }
                    },
                    "required": ["language"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scheme_details",
                "description": (
                    "Get the full grounded details for ONE scheme — description, "
                    "benefits, eligibility, age limit, contribution and how to "
                    "apply — returned in the requested language."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scheme_id": {
                            "type": "string",
                            "enum": scheme_ids,
                            "description": "The id of the scheme to look up.",
                        },
                        "language": {
                            "type": "string",
                            "enum": _SUPPORTED_LANGS,
                            "description": (
                                "The language the user wrote in; details are "
                                "returned in this language."
                            ),
                        },
                    },
                    "required": ["scheme_id", "language"],
                },
            },
        },
    ]


# ── Tool execution ──────────────────────────────────────────────────────────

def _parse_field(val) -> dict:
    """Parse a field that might be a JSON string, dict, or plain string."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {"english": val, "hindi": val, "bhojpuri": val}
    return {}


def _localize(field: dict, language: str) -> str:
    return field.get(language) or field.get("english") or ""


def _run_tool(name: str, args: dict, schemes: List[dict],
              apply_info: Dict[str, Dict[str, str]]) -> Tuple[str, Optional[str]]:
    """Execute a tool call against the scheme data.

    Returns (json_result_for_model, scheme_id_used_or_None).
    """
    language = args.get("language", "english")
    if language not in _LANG_NAME:
        language = "english"

    if name == "list_schemes":
        catalogue = [{"id": s["id"], "name": s["scheme"]} for s in schemes]
        return json.dumps(catalogue, ensure_ascii=False), None

    if name == "get_scheme_details":
        scheme_id = args.get("scheme_id")
        scheme = next((s for s in schemes if s["id"] == scheme_id), None)
        if scheme is None:
            return json.dumps(
                {"error": f"No scheme with id {scheme_id!r}.",
                 "available_ids": [s["id"] for s in schemes]},
                ensure_ascii=False,
            ), None

        benefits = _parse_field(scheme.get("benefits", {}))
        eligibility = _parse_field(scheme.get("eligibility", {}))
        how_to_apply = (apply_info.get(language) or apply_info.get("english", {})).get(scheme_id, "")

        details = {
            "id": scheme["id"],
            "scheme": scheme["scheme"],
            "language": language,
            "description": _localize(
                {"english": scheme.get("english"),
                 "hindi": scheme.get("hindi"),
                 "bhojpuri": scheme.get("bhojpuri")},
                language,
            ),
            "benefits": _localize(benefits, language),
            "eligibility": _localize(eligibility, language),
            "age_limit": scheme.get("age_limit", ""),
            "contribution_type": scheme.get("contribution_type", ""),
            "pension_range": scheme.get("pension_range", ""),
            "how_to_apply": how_to_apply,
        }
        return json.dumps(details, ensure_ascii=False), scheme_id

    return json.dumps({"error": f"Unknown tool {name!r}."}, ensure_ascii=False), None


# ── HTTP ──────────────────────────────────────────────────────────────────────

def _post_chat(payload: dict, req_id: str) -> Optional[dict]:
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
        # Optional but recommended by OpenRouter for attribution.
        "HTTP-Referer": "https://sevasetu.local",
        "X-Title": "SevaSetu",
    }
    url = f"{settings.LLM_BASE_URL.rstrip('/')}/chat/completions"
    started = time.perf_counter()
    try:
        r = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        elapsed = time.perf_counter() - started
        body = _truncate(e.response.text if e.response is not None else "")
        log.error("[%s] LLM HTTP %s after %.2fs: %s",
                  req_id, e.response.status_code if e.response else "?", elapsed, body)
    except Exception as e:
        elapsed = time.perf_counter() - started
        log.error("[%s] LLM request failed after %.2fs: %s",
                  req_id, elapsed, e, exc_info=True)
    return None


# ── Public entry point ──────────────────────────────────────────────────────

def generate_answer(query: str, schemes: List[dict],
                    apply_info: Optional[Dict[str, Dict[str, str]]] = None,
                    mode: str = "beginner",
                    ) -> Optional[Tuple[str, List[str], Optional[str]]]:
    """Run the tool-driven LLM flow.

    The model detects the language, decides which scheme(s) to look up, calls
    the tools to fetch grounded facts, and writes the reply in the user's
    language.

    Returns (answer, scheme_ids_used, detected_language) or None on failure.
    Deterministic: temperature is fixed at 0.
    """
    req_id = uuid.uuid4().hex[:8]
    apply_info = apply_info or {}

    if not is_enabled():
        log.info("[%s] LLM disabled (no OPENAI_API_KEY) — skipping", req_id)
        return None

    scheme_ids = [s["id"] for s in schemes]
    tools = _build_tools(scheme_ids)
    messages: List[dict] = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": query},
    ]

    used_scheme_ids: List[str] = []
    detected_language: Optional[str] = None

    log.info("[%s] LLM tool flow → model=%s mode=%s catalogue=%s query=%r",
             req_id, settings.LLM_MODEL, mode, scheme_ids, _truncate(query, 200))

    for step in range(MAX_TOOL_ITERATIONS):
        payload = {
            "model": settings.LLM_MODEL,
            "temperature": 0,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }

        # AI ko payload aur req_ID BHEJDI AUR Ai NE REPLY DIYA DATA ME
        data = _post_chat(payload, req_id)
        if data is None:
            return None

        # data ko parse kiya
        choice = (data.get("choices") or [{}])[0] or {}
        message = choice.get("message") or {}
        tool_calls = message.get("tool_calls") or []
        usage = data.get("usage", {}) or {}
        log.info("[%s] step %d ← finish=%s tool_calls=%d tokens(p/c/t)=%s/%s/%s",
                 req_id, step, choice.get("finish_reason"), len(tool_calls),
                 usage.get("prompt_tokens"), usage.get("completion_tokens"),
                 usage.get("total_tokens"))

        # No tool calls → this is the final answer.
        if not tool_calls:
            answer = (message.get("content") or "").strip()
            if not answer:
                log.warning("[%s] empty final content", req_id)
                return None
            log.info("[%s] answer (lang=%s, schemes=%s): %s",
                     req_id, detected_language, used_scheme_ids, _truncate(answer))
            return answer, used_scheme_ids, detected_language

        # Record the assistant turn that requested the tools, then answer each.
        messages.append(message)
        for call in tool_calls:
            fn = call.get("function", {}) or {}
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}

            lang_arg = args.get("language")
            if lang_arg in _LANG_NAME:
                detected_language = lang_arg  # keep the most recent language used

            result, sid = _run_tool(name, args, schemes, apply_info)
            if sid and sid not in used_scheme_ids:
                used_scheme_ids.append(sid)

            log.info("[%s] tool %s(%s) → %s",
                     req_id, name, args, _truncate(result, 200))
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id"),
                "content": result,
            })

    # Ran out of iterations — make one last call WITHOUT tools to force an answer.
    log.warning("[%s] hit MAX_TOOL_ITERATIONS — forcing a final answer", req_id)
    final = _post_chat(
        {"model": settings.LLM_MODEL, "temperature": 0, "messages": messages},
        req_id,
    )
    if final is None:
        return None
    answer = ((final.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    if not answer:
        return None
    return answer, used_scheme_ids, detected_language
