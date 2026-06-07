"""
rag_service.py – Smarter keyword search with detailed, query-specific responses.
"""
from __future__ import annotations
import json
import re
from typing import List, Tuple

from app.core.logging_config import get_ai_logger

log = get_ai_logger()

_faiss_index = None
_scheme_chunks: List[dict] = []
_all_schemes: List[dict] = []   # raw scheme data for detailed answers


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_schemes(path: str) -> List[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse_field(val):
    """Parse a field that might be a JSON string, dict, or plain string."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return {"english": val, "hindi": val, "bhojpuri": val}
    return {}


def initialize_rag(knowledge_base_path: str, index_path: str):
    global _all_schemes, _scheme_chunks
    try:
        _all_schemes = _load_schemes(knowledge_base_path)
        _build_chunks()
        print(f"[RAG] Loaded {len(_all_schemes)} schemes, {len(_scheme_chunks)} chunks.")
    except Exception as e:
        print(f"[RAG] Warning: {e}")


def _build_chunks():
    global _scheme_chunks
    _scheme_chunks = []
    for s in _all_schemes:
        benefits   = _parse_field(s.get("benefits", {}))
        eligibility = _parse_field(s.get("eligibility", {}))
        for lang in ("english", "hindi", "bhojpuri"):
            desc = s.get(lang, "")
            ben  = benefits.get(lang, "")
            elig = eligibility.get(lang, "")
            _scheme_chunks.append({
                "scheme_id":   s["id"],
                "scheme_name": s["scheme"],
                "lang":        lang,
                "description": desc,
                "benefits":    ben,
                "eligibility": elig,
                "age_limit":   s.get("age_limit", ""),
                "pension_range": s.get("pension_range", ""),
                "contribution": s.get("contribution_type", ""),
                # Combined searchable text
                "search_text": f"{s['scheme']} {desc} {ben} {elig}",
            })


# ── Intent detection ──────────────────────────────────────────────────────────

INTENT_PATTERNS = {
    "benefits": {
        "english":  ["benefit", "get", "amount", "money", "receive", "give", "pay", "rupee", "₹", "how much"],
        "hindi":    ["लाभ", "फायदा", "राशि", "रुपए", "पैसा", "कितना", "मिलता", "मिलेगा", "धनराशि"],
        "bhojpuri": ["फायदा", "मिलेला", "पइसा", "रुपया", "कतना", "लाभ"],
    },
    "eligibility": {
        "english":  ["eligible", "eligibility", "qualify", "who can", "criteria", "apply", "requirement", "age"],
        "hindi":    ["पात्रता", "पात्र", "योग्यता", "कौन", "आवेदन", "उम्र", "आयु", "शर्त"],
        "bhojpuri": ["पात्रता", "पाता", "खातिर", "कवन", "उमर", "आवेदन", "का बा"],
    },
    "apply": {
        "english":  ["apply", "register", "how to", "process", "application", "enroll"],
        "hindi":    ["आवेदन", "कैसे", "पंजीकरण", "प्रक्रिया", "आवेदन कैसे करें"],
        "bhojpuri": ["आवेदन", "कइसे", "पंजीकरण", "कइल जाला"],
    },
    "description": {
        "english":  ["what is", "about", "tell me", "explain", "describe", "information", "details"],
        "hindi":    ["क्या है", "बताएं", "जानकारी", "विवरण", "बारे में", "समझाएं"],
        "bhojpuri": ["का बा", "बताईं", "जानकारी", "बारे में", "का ह"],
    },
}


def detect_intent(query: str, language: str) -> str:
    q = query.lower()
    for intent, lang_patterns in INTENT_PATTERNS.items():
        patterns = lang_patterns.get(language, []) + lang_patterns.get("english", [])
        if any(p in q for p in patterns):
            return intent
    return "description"  # default


# ── Language detection ────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    if re.search(r'[\u0900-\u097F]', text):
        bhojpuri_markers = ["बा ", "बा?", "खातिर", "मिलेला", "करेला",
                            "जाला", "बाटे", "काहे", "रहल", "गइल", "बाड़न"]
        if any(m in text for m in bhojpuri_markers):
            return "bhojpuri"
        return "hindi"
    try:
        from langdetect import detect
        if detect(text) == "hi":
            return "hindi"
    except Exception:
        pass
    return "english"


# ── Scheme matching ───────────────────────────────────────────────────────────

# Scheme name aliases for fuzzy matching
SCHEME_ALIASES = {
    "PM-KISAN-001": ["pm kisan", "पीएम किसान", "pm-kisan", "kisan samman",
                     "किसान सम्मान", "किसान योजना", "किसान"],
    "PMJJBY-002":  ["jeevan jyoti", "जीवन ज्योति", "pmjjby", "life insurance",
                    "जीवन बीमा", "bima yojana"],
    "APY-003":     ["atal pension", "अटल पेंशन", "apy", "pension yojana",
                    "पेंशन योजना", "पेंशन"],
    "PMAY-004":    ["awas yojana", "आवास योजना", "pmay", "housing", "घर",
                    "pradhan mantri awas", "आवास"],
    "PMSBY-005":   ["suraksha bima", "सुरक्षा बीमा", "pmsby", "accident",
                    "दुर्घटना", "accidental insurance"],
}


def _find_matching_schemes(query: str, language: str) -> List[dict]:
    """Find schemes that match the query — specific matching, not broad."""
    q_lower = query.lower()
    matched_ids = set()

    # 1. Check scheme name aliases first (most specific)
    for scheme_id, aliases in SCHEME_ALIASES.items():
        for alias in aliases:
            if alias in q_lower or alias in query:
                matched_ids.add(scheme_id)
                break

    # 2. If no alias match, do keyword scoring on scheme names + descriptions
    if not matched_ids:
        if re.search(r'[\u0900-\u097F]', query):
            keywords = [w.strip('।,?!।') for w in query.split() if len(w.strip('।,?!।')) >= 2]
        else:
            keywords = [w for w in re.findall(r'\w+', q_lower) if len(w) >= 3]

        # Filter out very common/generic words
        stop_words = {
            "the", "and", "for", "about", "tell", "what", "how", "please",
            "में", "के", "की", "का", "है", "हैं", "कि", "से", "को", "पर",
            "बारे", "बताएं", "बताओ", "क्या", "कैसे", "मुझे", "मेरे",
            "खातिर", "बा", "का", "एह", "ओह", "आउर", "बाटे"
        }
        keywords = [kw for kw in keywords if kw not in stop_words]

        scheme_scores = {}
        for scheme in _all_schemes:
            score = 0.0
            name_lower = scheme["scheme"].lower()
            desc = scheme.get(language, scheme.get("english", ""))
            benefits = _parse_field(scheme.get("benefits", {}))
            ben_text = benefits.get(language, benefits.get("english", ""))
            search_text = f"{name_lower} {desc} {ben_text}".lower()

            for kw in keywords:
                if kw in name_lower:
                    score += 3.0  # strong weight for name match
                elif kw in search_text:
                    score += 1.0

            if score > 0:
                scheme_scores[scheme["id"]] = score

        # Only return schemes with meaningful scores; take top 2
        if scheme_scores:
            top = sorted(scheme_scores.items(), key=lambda x: -x[1])[:2]
            matched_ids = {sid for sid, sc in top if sc >= 2.0}
            if not matched_ids:
                # Relax threshold if nothing strong matched
                matched_ids = {sid for sid, sc in top[:1]}

    # Return matched scheme data
    return [s for s in _all_schemes if s["id"] in matched_ids]


# ── Response generation ───────────────────────────────────────────────────────

LABELS = {
    "english":  {
        "intro":       "Here is detailed information:\n\n",
        "description": "📖 About",
        "benefits":    "💰 Benefits",
        "eligibility": "✅ Eligibility",
        "apply":       "📝 How to Apply",
        "age":         "📅 Age Limit",
        "contribution":"💳 Contribution",
        "pension":     "💵 Benefit Amount",
        "not_found":   "Sorry, I couldn't find information about that. Please try asking about a specific scheme like PM Kisan, Atal Pension Yojana, PMAY, PMJJBY, or PMSBY.",
        "greeting":    "Hello! I am SevaSetu. Ask me about government schemes like PM Kisan, Atal Pension, PMAY, PMJJBY, or PMSBY.",
    },
    "hindi": {
        "intro":       "यहाँ विस्तृत जानकारी है:\n\n",
        "description": "📖 विवरण",
        "benefits":    "💰 लाभ",
        "eligibility": "✅ पात्रता",
        "apply":       "📝 आवेदन कैसे करें",
        "age":         "📅 आयु सीमा",
        "contribution":"💳 अंशदान",
        "pension":     "💵 लाभ राशि",
        "not_found":   "माफ करें, मुझे इस विषय पर जानकारी नहीं मिली। कृपया PM किसान, अटल पेंशन, PMAY, PMJJBY या PMSBY के बारे में पूछें।",
        "greeting":    "नमस्ते! मैं SevaSetu हूँ। PM किसान, अटल पेंशन योजना, PMAY जैसी सरकारी योजनाओं के बारे में पूछें।",
    },
    "bhojpuri": {
        "intro":       "ई रहल विस्तार से जानकारी:\n\n",
        "description": "📖 जानकारी",
        "benefits":    "💰 फायदा",
        "eligibility": "✅ पात्रता",
        "apply":       "📝 आवेदन कइसे करीं",
        "age":         "📅 उमर सीमा",
        "contribution":"💳 अंशदान",
        "pension":     "💵 मिलेवाला रकम",
        "not_found":   "माफ करीं, एह बिसय पर जानकारी ना मिलल। PM किसान, अटल पेंशन, PMAY के बारे में पूछीं।",
        "greeting":    "प्रणाम! हम SevaSetu हईं। PM किसान, अटल पेंशन, आवास योजना के बारे में पूछीं।",
    },
}

APPLY_INFO = {
    "english": {
        "PM-KISAN-001": "Visit pmkisan.gov.in or your nearest Common Service Centre (CSC). Required documents: Aadhaar card, land records, bank account details.",
        "PMJJBY-002":   "Contact your bank or visit their official website. The annual premium of ₹436 is auto-debited from your account each year in May.",
        "APY-003":      "Visit your bank or post office. Fill the APY enrollment form with your Aadhaar and bank account details. Contributions auto-debit monthly.",
        "PMAY-004":     "Apply at pmaymis.gov.in or visit your nearest bank/housing finance company. Required: Aadhaar, income proof, property documents.",
        "PMSBY-005":    "Contact your bank branch or apply online through net banking. Annual premium of ₹20 is auto-debited every June.",
    },
    "hindi": {
        "PM-KISAN-001": "pmkisan.gov.in पर जाएं या निकटतम Common Service Centre (CSC) पर जाएं। आवश्यक दस्तावेज़: आधार कार्ड, भूमि रिकॉर्ड, बैंक खाता विवरण।",
        "PMJJBY-002":   "अपने बैंक से संपर्क करें या उनकी आधिकारिक वेबसाइट पर जाएं। ₹436 वार्षिक प्रीमियम हर मई में खाते से स्वतः कट जाता है।",
        "APY-003":      "अपने बैंक या डाकघर जाएं। आधार और बैंक विवरण के साथ APY फॉर्म भरें। मासिक अंशदान स्वतः कटेगा।",
        "PMAY-004":     "pmaymis.gov.in पर या निकटतम बैंक/हाउसिंग फाइनेंस कंपनी में आवेदन करें। आवश्यक: आधार, आय प्रमाण, संपत्ति दस्तावेज़।",
        "PMSBY-005":    "अपनी बैंक शाखा में संपर्क करें या नेट बैंकिंग से ऑनलाइन आवेदन करें। ₹20 वार्षिक प्रीमियम हर जून में स्वतः कटता है।",
    },
    "bhojpuri": {
        "PM-KISAN-001": "pmkisan.gov.in पर जाईं या नजदीकी Common Service Centre (CSC) पर जाईं। जरूरी कागज: आधार कार्ड, जमीन के कागज, बैंक खाता।",
        "PMJJBY-002":   "अपना बैंक से बात करीं। ₹436 सालाना प्रीमियम हर मई में खाता से कट जाला।",
        "APY-003":      "अपना बैंक या डाकघर जाईं। आधार आउर बैंक जानकारी के साथ APY फॉर्म भरीं। हर महीना पइसा अपने आप कट जाला।",
        "PMAY-004":     "pmaymis.gov.in पर या नजदीकी बैंक में आवेदन करीं। जरूरी: आधार, आय प्रमाण, जमीन के कागज।",
        "PMSBY-005":    "अपना बैंक में जाईं या नेट बैंकिंग से आवेदन करीं। ₹20 सालाना प्रीमियम हर जून में कट जाला।",
    },
}


def _build_scheme_response(scheme: dict, intent: str, language: str) -> str:
    L = LABELS[language]
    sid = scheme["id"]
    name = scheme["scheme"]
    benefits    = _parse_field(scheme.get("benefits", {}))
    eligibility = _parse_field(scheme.get("eligibility", {}))
    desc     = scheme.get(language, scheme.get("english", ""))
    ben_text = benefits.get(language, benefits.get("english", ""))
    elig_text = eligibility.get(language, eligibility.get("english", ""))
    age      = scheme.get("age_limit", "")
    pension  = scheme.get("pension_range", "")
    contrib  = scheme.get("contribution_type", "")

    parts = [f"**{name}**\n"]

    if intent == "description":
        parts.append(f"{L['description']}: {desc}")
        parts.append(f"{L['benefits']}: {ben_text}")
        parts.append(f"{L['eligibility']}: {elig_text}")
        if age:
            parts.append(f"{L['age']}: {age}")

    elif intent == "benefits":
        parts.append(f"{L['benefits']}: {ben_text}")
        if pension:
            parts.append(f"{L['pension']}: {pension}")
        if contrib:
            parts.append(f"{L['contribution']}: {contrib}")

    elif intent == "eligibility":
        parts.append(f"{L['eligibility']}: {elig_text}")
        if age:
            parts.append(f"{L['age']}: {age}")

    elif intent == "apply":
        apply_text = APPLY_INFO.get(language, APPLY_INFO["english"]).get(sid, "")
        if not apply_text:
            apply_text = APPLY_INFO["english"].get(sid, "Please visit the official government portal.")
        parts.append(f"{L['apply']}:\n{apply_text}")

    return "\n".join(parts)


def _template_response(query: str, language: str, mode: str,
                       matched_schemes: List[dict]) -> str:
    """Keyword/template answer — used only when the LLM is off or fails."""
    L = LABELS.get(language, LABELS["english"])

    greet_words = ["hello", "hi", "नमस्ते", "हेलो", "प्रणाम", "नमस्कार", "hey"]
    if any(w in query.lower() for w in greet_words) and len(query) < 25:
        return L["greeting"]

    if not matched_schemes:
        return L["not_found"]

    limit  = 1 if mode == "beginner" else 2  # beginner: focus on 1 scheme
    intent = detect_intent(query, language)
    parts = [L["intro"]]
    for scheme in matched_schemes[:limit]:
        parts.append(_build_scheme_response(scheme, intent, language))
        parts.append("")  # spacer

    return "\n".join(parts).strip()


# ── Public entry point ────────────────────────────────────────────────────────

def process_chat(message: str, language: str = "hindi",
                 mode: str = "beginner") -> Tuple[str, List[dict], str]:
    """Tool-driven AI flow with a template fallback.

    The LLM gets only the user's message — it detects the language itself and
    calls tools (over the full scheme catalogue) to pull the relevant facts in
    that language. We use the language and scheme ids the AI actually chose.
    The regex `detect_language` / keyword matching is kept only as a fallback
    for when the LLM is disabled or fails.
    """
    fallback_language = detect_language(message) if language == "auto" else language
    log.info("process_chat | lang_in=%s fallback_lang=%s mode=%s msg=%r",
             language, fallback_language, mode, message[:200])

    # ── AI-first: hand the whole catalogue to the tool-driven model ──────────
    from app.services import llm_service
    if llm_service.is_enabled():
        try:
            result = llm_service.generate_answer(
                message, _all_schemes, APPLY_INFO, mode,
            )
        except Exception as e:
            log.error("LLM error — using template fallback: %s", e, exc_info=True)
            result = None

        if result:
            reply, used_ids, ai_language = result
            effective_language = ai_language or fallback_language
            by_id = {s["id"]: s for s in _all_schemes}
            snippets = [{"id": sid, "name": by_id[sid]["scheme"]}
                        for sid in used_ids if sid in by_id]
            log.info("process_chat done (AI) | lang=%s reply_len=%d schemes=%s",
                     effective_language, len(reply or ""), used_ids)
            return reply, snippets, effective_language
        log.warning("LLM enabled but returned no answer — using template fallback")

    # ── Template fallback (LLM disabled or failed) ───────────────────────────
    matched = _find_matching_schemes(message, fallback_language)
    matched_ids = [s["id"] for s in matched]
    log.info("retrieval (fallback) | matched %d scheme(s): %s", len(matched), matched_ids)

    reply = _template_response(message, fallback_language, mode, matched)
    snippets = [{"id": s["id"], "name": s["scheme"]} for s in matched]
    log.info("process_chat done (template) | reply_len=%d snippets=%s",
             len(reply or ""), matched_ids)
    return reply, snippets, fallback_language