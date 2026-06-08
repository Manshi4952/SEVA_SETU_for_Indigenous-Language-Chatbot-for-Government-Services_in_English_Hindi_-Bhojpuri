"""
rag_service.py – Production RAG pipeline for SevaSetu.

v3 changes:
  - Groq replaces Anthropic as the LLM provider
  - Uses services/llm/provider.py abstraction
  - Fixed _answer_follow_up using correct field names from schemes JSON
  - Improved SYSTEM_PROMPT for natural, ChatGPT-quality responses
  - Template fallback covers missing eligibility/docs gracefully
  - [cite: XX] artifact stripping
  - Relevance scores in snippets
  - State bias: Bihar/Central schemes ranked higher
  - Transliterated Bhojpuri detection in Roman script
  - Smart topic-aware fallback
"""

from __future__ import annotations
import json
import re
from typing import List, Tuple

import faiss

_faiss_index = None
_all_schemes: List[dict] = []

CITE_PATTERN = re.compile(r'\[cite:\s*\d+\]')


def _clean_text(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = CITE_PATTERN.sub('', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def _parse_field(val):
    if isinstance(val, dict):
        return {k: _clean_text(v) if isinstance(v, str) else v for k, v in val.items()}
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return {k: _clean_text(v) if isinstance(v, str) else v for k, v in parsed.items()}
            return parsed
        except Exception:
            return {"english": _clean_text(val), "hindi": _clean_text(val), "bhojpuri": _clean_text(val)}
    return {}


def _parse_list(val):
    if isinstance(val, list): return val
    if isinstance(val, str):
        try: return json.loads(val)
        except: return []
    return []


def initialize_rag(knowledge_base_path: str, index_path: str):
    global _all_schemes, _faiss_index
    try:
        with open(knowledge_base_path, encoding="utf-8") as f:
            _all_schemes = json.load(f)
        print(f"[RAG] Loaded {len(_all_schemes)} schemes from {knowledge_base_path}.")
    except Exception as e:
        print(f"[RAG] Warning loading JSON: {e}")

    try:
        _faiss_index = faiss.read_index(index_path)
        print(f"[RAG] Successfully loaded FAISS index from {index_path}.")
    except Exception as e:
        print(f"[RAG] Warning loading FAISS index: {e}")


TRANSLITERATED_BHOJPURI = [
    "kaise", "kahe", "kavan", "kavana", "batain", "badin", "milela",
    "jaala", "baate", "kachu", "samjh", "aavata", "hamar", "tohar",
    "hamni", "raura", "bhaiya", "maai", "baap", "kari", "karo", "hoi",
]


def detect_language(text: str) -> str:
    if re.search(r'[\u0900-\u097F]', text):
        bhojpuri_markers = ["बा ", "बा?", "खातिर", "मिलेला", "करेला", "जाला",
                            "बाटे", "काहे", "रहल", "गइल", "बाड़न", "ओकरा",
                            "एकरा", "कइसे", "पइसा"]
        if any(m in text for m in bhojpuri_markers):
            return "bhojpuri"
        return "hindi"
    text_lower = text.lower()
    bhojpuri_hits = sum(1 for m in TRANSLITERATED_BHOJPURI if m in text_lower)
    if bhojpuri_hits >= 2:
        return "bhojpuri"
    try:
        from langdetect import detect
        if detect(text) == "hi": return "hindi"
    except: pass
    return "english"


INTENT_PATTERNS = {
    "benefits": {
        "english":  ["benefit", "get", "amount", "money", "receive", "rupee", "how much", "gain"],
        "hindi":    ["लाभ", "फायदा", "राशि", "रुपए", "पैसा", "कितना", "मिलता", "मिलेगा"],
        "bhojpuri": ["फायदा", "मिलेला", "पइसा", "रुपया", "कतना", "लाभ"],
    },
    "eligibility": {
        "english":  ["eligible", "eligibility", "qualify", "who can", "criteria", "age", "requirement"],
        "hindi":    ["पात्रता", "पात्र", "योग्यता", "कौन", "उम्र", "आयु", "शर्त"],
        "bhojpuri": ["पात्रता", "पाता", "खातिर", "कवन", "उमर", "उमिर", "उमरि"],
    },
    "documents": {
        "english":  ["document", "required", "paper", "certificate", "aadhaar", "proof", "need"],
        "hindi":    ["दस्तावेज", "कागज", "प्रमाण", "आधार", "जरूरी", "चाहिए"],
        "bhojpuri": ["कागज", "दस्तावेज", "आधार", "जरूरी", "चाही"],
    },
    "apply": {
        "english":  ["apply", "register", "how to", "process", "application", "enroll", "form", "fill"],
        "hindi":    ["आवेदन", "कैसे", "पंजीकरण", "प्रक्रिया", "फॉर्म", "भरें"],
        "bhojpuri": ["आवेदन", "कइसे", "पंजीकरण", "फॉर्म", "कइल जाला", "भरीं"],
    },
    "description": {
        "english":  ["what is", "about", "tell me", "explain", "describe", "information", "details"],
        "hindi":    ["क्या है", "बताएं", "जानकारी", "विवरण", "बारे में"],
        "bhojpuri": ["का बा", "बताईं", "जानकारी", "बारे में"],
    },
}


def detect_intent(query: str, language: str) -> str:
    q = query.lower()
    for intent, lang_patterns in INTENT_PATTERNS.items():
        patterns = lang_patterns.get(language, []) + lang_patterns.get("english", [])
        if any(p in q for p in patterns):
            return intent
    return "description"


STOP_WORDS = {
    "the", "and", "for", "about", "tell", "what", "how", "please", "is", "me",
    "में", "के", "की", "का", "है", "हैं", "कि", "से", "को", "पर", "एक",
    "बारे", "बताएं", "बताओ", "क्या", "कैसे", "मुझे", "मेरे", "यह", "वह",
    "खातिर", "बा", "का", "एह", "ओह", "आउर", "बाटे", "हम", "तू", "आप",
}

BIHAR_STATES = {"bihar", "central", "all india", "national", ""}


def _score_scheme(scheme: dict, keywords: List[str], query: str, language: str) -> float:
    score = 0.0
    name_lower = scheme["scheme"].lower()
    name_hindi = scheme.get("scheme_hindi", "")
    desc = scheme.get(language, scheme.get("english", "")).lower()
    scheme_kw_text = " ".join(_parse_list(scheme.get("keywords", []))).lower()
    is_devanagari = re.search(r'[\u0900-\u097F]', query)

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in name_lower: score += 4.0
        if kw in name_hindi: score += 4.0
        if kw_lower in scheme_kw_text or kw in scheme_kw_text: score += 3.0
        if is_devanagari:
            if kw in desc or kw in scheme.get(language, ""): score += 1.5
        else:
            if kw_lower in desc: score += 1.5
        if kw_lower in scheme.get("official_category", "").lower(): score += 2.0

    state = scheme.get("state", "").lower().strip()
    if state in BIHAR_STATES: score += 1.5
    elif state: score -= 0.5

    score += _alias_boost(scheme, query)
    return score


def _find_matching_schemes_scored(query: str, language: str, top_k: int = 3) -> List[Tuple[dict, float]]:
    if not _all_schemes:
        return []

    if re.search(r'[\u0900-\u097F]', query):
        keywords = [w.strip('।,?!।॥') for w in query.split() if len(w.strip('।,?!।॥')) >= 2]
    else:
        keywords = [w for w in re.findall(r'\w+', query.lower()) if len(w) >= 3]

    keywords = [kw for kw in keywords if kw.lower() not in STOP_WORDS and kw not in STOP_WORDS]
    if not keywords:
        return []

    scored = [(s, _score_scheme(s, keywords, query, language)) for s in _all_schemes]
    scored = [(s, sc) for s, sc in scored if sc > 0]
    scored.sort(key=lambda x: -x[1])

    if not scored:
        return []

    top_score = scored[0][1]
    return [(s, sc) for s, sc in scored if sc >= top_score * 0.6][:top_k]


LABELS = {
    "english": {
        "intro": "Here is the information:\n\n",
        "description": "📖 About", "full_detail": "📋 Full Details",
        "benefits": "💰 Benefits", "eligibility": "✅ Eligibility",
        "documents": "📄 Documents Required", "apply": "📝 How to Apply",
        "age": "📅 Age Limit", "benefit_range": "💵 Benefit Amount",
        "category": "🏷️ Category", "state": "📍 State",
        "not_found": "Sorry, I couldn't find a scheme matching your query. Try asking about 'Bihar Student Credit Card', 'Kanya Utthan', 'Vridhjan Pension', 'PMAY', 'PM Kisan'.",
        "greeting": "Hello! I am SevaSetu. I have information on 218+ Bihar government schemes. Ask me about education loans, pensions, farming, housing or health schemes.",
        "multi_found": "I found multiple relevant schemes:",
    },
    "hindi": {
        "intro": "यहाँ जानकारी है:\n\n",
        "description": "📖 विवरण", "full_detail": "📋 पूरी जानकारी",
        "benefits": "💰 लाभ", "eligibility": "✅ पात्रता",
        "documents": "📄 जरूरी दस्तावेज़", "apply": "📝 आवेदन कैसे करें",
        "age": "📅 आयु सीमा", "benefit_range": "💵 लाभ राशि",
        "category": "🏷️ श्रेणी", "state": "📍 राज्य",
        "not_found": "माफ करें, इस विषय से संबंधित कोई योजना नहीं मिली। 'बिहार स्टूडेंट क्रेडिट कार्ड', 'कन्या उत्थान', 'वृद्धजन पेंशन', 'किसान', 'आवास' जैसे विषयों पर पूछें।",
        "greeting": "नमस्ते! मैं SevaSetu हूँ। मेरे पास 218 से अधिक बिहार सरकार की योजनाओं की जानकारी है।",
        "multi_found": "आपके लिए कई संबंधित योजनाएं मिलीं:",
    },
    "bhojpuri": {
        "intro": "ई रहल जानकारी:\n\n",
        "description": "📖 जानकारी", "full_detail": "📋 पूरा ब्यौरा",
        "benefits": "💰 फायदा", "eligibility": "✅ पात्रता",
        "documents": "📄 जरूरी कागज", "apply": "📝 आवेदन कइसे करीं",
        "age": "📅 उमर सीमा", "benefit_range": "💵 मिलेवाला रकम",
        "category": "🏷️ श्रेणी", "state": "📍 राज्य",
        "not_found": "माफ करीं, एह बिसय से जुड़ल कवनो योजना ना मिलल। 'बिहार स्टूडेंट क्रेडिट कार्ड', 'कन्या उत्थान', 'वृद्धजन पेंशन', 'किसान', 'घर' जइसन बिसय पर पूछीं।",
        "greeting": "प्रणाम! हम SevaSetu हईं। हमनी के लगे 218 से बेसी बिहार सरकार के योजना के जानकारी बा।",
        "multi_found": "आपसे जुड़ल कई योजना मिलल:",
    },
}

TOPIC_HINTS = {
    r"student|education|college|school|padhai|पढ़ाई|लड़का|लड़की|bscc|scholarship": {
        "english":  "Try: 'Bihar Student Credit Card', 'Mukhyamantri Kanya Utthan Yojana', or 'National Scholarship'.",
        "hindi":    "'बिहार स्टूडेंट क्रेडिट कार्ड', 'मुख्यमंत्री कन्या उत्थान योजना' के बारे में पूछें।",
        "bhojpuri": "'बिहार स्टूडेंट क्रेडिट कार्ड', 'कन्या उत्थान योजना' के बारे में पूछीं।",
    },
    r"farmer|kisan|farming|crop|किसान|खेती|फसल|agriculture": {
        "english":  "Try: 'PM Kisan Samman Nidhi', 'Kisan Credit Card', 'PM Fasal Bima'.",
        "hindi":    "'PM किसान', 'किसान क्रेडिट कार्ड', 'फसल बीमा' के बारे में पूछें।",
        "bhojpuri": "'PM किसान', 'किसान क्रेडिट कार्ड' के बारे में पूछीं।",
    },
    r"house|home|ghar|aawas|awas|घर|आवास": {
        "english":  "Ask about 'Pradhan Mantri Awas Yojana (PMAY)'.",
        "hindi":    "'प्रधानमंत्री आवास योजना (PMAY)' के बारे में पूछें।",
        "bhojpuri": "'प्रधानमंत्री आवास योजना' के बारे में पूछीं।",
    },
    r"pension|old|elderly|budhapa|वृद्ध|बुढ़ापा|पेंशन": {
        "english":  "Ask about 'Bihar Vridhjan Pension Yojana'.",
        "hindi":    "'बिहार वृद्धजन पेंशन योजना' के बारे में पूछें।",
        "bhojpuri": "'वृद्धजन पेंशन योजना' के बारे में पूछीं।",
    },
    r"health|hospital|ayushman|इलाज|स्वास्थ्य": {
        "english":  "Ask about 'Ayushman Bharat PM-JAY' – free health coverage up to ₹5 lakh.",
        "hindi":    "'आयुष्मान भारत PM-JAY' के बारे में पूछें।",
        "bhojpuri": "'आयुष्मान भारत' के बारे में पूछीं।",
    },
    r"gas|lpg|cylinder|ujjwala|गैस|सिलेंडर": {
        "english":  "Ask about 'Pradhan Mantri Ujjwala Yojana' for free LPG connections.",
        "hindi":    "'प्रधानमंत्री उज्ज्वला योजना' के बारे में पूछें।",
        "bhojpuri": "'उज्ज्वला योजना' के बारे में पूछीं।",
    },
}


def _smart_fallback(query: str, language: str) -> str:
    q = query.lower()
    prefixes = {
        "english":  "I couldn't find an exact match, but you might be looking for: ",
        "hindi":    "सीधा मिलान नहीं मिला, लेकिन शायद यह आपके काम आए: ",
        "bhojpuri": "सीधे मिलल नाहीं, बाकिर ई पूछीं: ",
    }
    for pattern, responses in TOPIC_HINTS.items():
        if re.search(pattern, q, re.IGNORECASE):
            prefix = prefixes.get(language, prefixes["english"])
            return prefix + responses.get(language, responses["english"])
    return LABELS.get(language, LABELS["english"])["not_found"]


def _build_scheme_response(scheme: dict, intent: str, language: str, mode: str) -> str:
    L = LABELS[language]
    name = scheme["scheme"]
    name_hindi = scheme.get("scheme_hindi", "")
    benefits    = _parse_field(scheme.get("benefits", {}))
    eligibility = _parse_field(scheme.get("eligibility", {}))
    docs        = _parse_field(scheme.get("documents_required", {}))
    apply_proc  = _parse_field(scheme.get("application_process", {}))
    full_desc   = _parse_field(scheme.get("full_description", {}))

    def g(d):
        if not d:
            return ""
        return d.get(language, d.get("english", "")) if isinstance(d, dict) else str(d)

    header = f"**{name}**"
    if name_hindi and name_hindi != name:
        header += f" ({name_hindi})"
    parts = [header, ""]

    age = scheme.get("age_limit", "")
    benefit_range = scheme.get("benefit_range", "")
    category = scheme.get("official_category", "")
    short_desc = _clean_text(scheme.get(language, scheme.get("english", "")))

    if intent == "description":
        parts.append(f"{L['description']}: {short_desc}")
        if mode == "advanced" and g(full_desc):
            parts.append(f"\n{L['full_detail']}: {g(full_desc)}")
        parts.append(f"\n{L['benefits']}: {g(benefits)}")
        if benefit_range: parts.append(f"{L['benefit_range']}: {benefit_range}")
        if age: parts.append(f"{L['age']}: {age}")
        if category: parts.append(f"{L['category']}: {category}")
    elif intent == "benefits":
        parts.append(f"{L['benefits']}: {g(benefits)}")
        if benefit_range: parts.append(f"{L['benefit_range']}: {benefit_range}")
    elif intent == "eligibility":
        elig_text = g(eligibility)
        if not elig_text:
            elig_text = g(_parse_field(scheme.get("eligibility_criteria", {})))
        if not elig_text:
            elig_text = short_desc
        parts.append(f"{L['eligibility']}: {elig_text}")
        if age: parts.append(f"{L['age']}: {age}")
    elif intent == "documents":
        doc_text = g(docs)
        if not doc_text:
            doc_text = "Aadhaar Card, Bank Account, Passport Photo" if language == "english" else "आधार कार्ड, बैंक खाता, पासपोर्ट फोटो"
        parts.append(f"{L['documents']}: {doc_text}")
    elif intent == "apply":
        apply_text = g(apply_proc)
        if not apply_text or not str(apply_text).strip():
            apply_text = g(full_desc)
            if not apply_text or not str(apply_text).strip():
                apply_text = short_desc
            if not apply_text or not str(apply_text).strip():
                apply_text = "Visit the official state portal or nearest CSC (Common Service Centre) to apply." if language == "english" else "आवेदन के लिए नजदीकी CSC केंद्र या आधिकारिक पोर्टल पर जाएं।"
        parts.append(f"{L['apply']}: {apply_text}")

    return "\n".join(p for p in parts if p is not None)


def generate_response(query: str, language: str, mode: str, matched: list) -> str:
    L = LABELS.get(language, LABELS["english"])
    greet_words = ["hello", "hi", "नमस्ते", "हेलो", "प्रणाम", "नमस्कार", "hey"]

    if any(w in query.lower() for w in greet_words) and len(query) < 25:
        return L["greeting"]

    if not matched:
        return _smart_fallback(query, language)

    if _is_follow_up(query):
        return _answer_follow_up(matched[0], query, language)

    intent = detect_intent(query, language)

    if len(matched) == 1 or mode == "beginner":
        return L["intro"] + _build_scheme_response(matched[0], intent, language, mode)

    parts = [L["multi_found"], ""]
    for scheme in matched[:3]:
        parts.append(_build_scheme_response(scheme, intent, language, mode))
        parts.append("\n---\n")

    return "\n".join(parts)


SYSTEM_PROMPT = """You are SevaSetu, a warm and knowledgeable AI assistant helping citizens of Bihar (India) understand government welfare schemes. You have a database of 218+ central and state schemes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE RULES — follow strictly
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Bhojpuri (Devanagari or Roman script) → reply 100% in Bhojpuri
• Hindi → reply 100% in Hindi
• English → reply in English
• Translate the database context into the user's language — never reply in a different language than the user used
• Never mix languages in one reply

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You are like a knowledgeable friend at the village panchayat — patient, direct, and clear. You use simple everyday words. You always give the specific rupee amount, real eligibility conditions, and clear steps. You never make up information.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Start DIRECTLY with the answer — NEVER open with "Here is the information:", "As per the database:", "Sure!", or any filler phrase
• Use **bold** for scheme names and rupee amounts
• For "how to apply" queries → numbered steps (1. 2. 3.)
• For "how much money" queries → lead with the exact amount in the first sentence
• End with one short follow-up question or next-step suggestion (not "I hope this helps")
• BEGINNER MODE: max 4 bullet points, simplest language, biggest benefit first
• DETAILED MODE: full eligibility, complete document list, official portal URL, all amounts and deadlines

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Use ONLY information from the scheme context provided — never invent eligibility, amounts, or steps
• If a specific detail (e.g. exact eligibility) is missing from context, say honestly: "This specific detail isn't in our database — please check [official portal] or nearest CSC centre"
• Never repeat the same sentence twice in one response
• Avoid robotic phrases: "I am an AI", "I cannot", "Feel free to ask", "I hope this helps"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOLLOW-UP HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• If the user asks a short follow-up (age, documents, how to apply, amount), answer about the SAME scheme from context
• Do NOT switch to a different scheme unless the user explicitly names one

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEW-SHOT EXAMPLES (match this style exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1 — English description query:
User: Tell me about PM Kisan scheme
Assistant: **PM Kisan Samman Nidhi** gives farmers ₹6,000 every year — split into 3 payments of ₹2,000 each, sent directly to your bank account every 4 months.
✅ Who can apply: Small and marginal farmers with up to 2 hectares of land
📅 Age: 18 years and above
Would you like to know how to apply, or check your payment status?

Example 2 — Hindi benefits query:
User: वृद्धजन पेंशन में कितना पैसा मिलता है?
Assistant: **मुख्यमंत्री वृद्धजन पेंशन योजना** में हर महीने ₹400 सीधे आपके बैंक खाते में आते हैं।
💰 60 से 79 साल के बुजुर्गों को ₹400/महीना
💰 80 साल या उससे ज्यादा उम्र के बुजुर्गों को ₹500/महीना
क्या आप जानना चाहते हैं कि आवेदन कैसे करें?

Example 3 — Bhojpuri how-to-apply query:
User: बिहार स्टूडेंट क्रेडिट कार्ड में आवेदन कइसे करीं?
Assistant: **बिहार स्टूडेंट क्रेडिट कार्ड** में आवेदन करे के तरीका:
1. 7nishchay-yuvaupmission.bihar.gov.in पर जाईं
2. 'Student Credit Card' पर क्लिक करीं
3. अपना आधार नंबर आ मोबाइल नंबर भरीं
4. कॉलेज एडमिशन के कागज अपलोड करीं
5. DRCC कार्यालय में जाके verification करवाईं
का आपके पास आधार कार्ड आ कॉलेज admission letter बा?

Example 4 — English eligibility follow-up:
User: age limit
Assistant: For **Bihar Student Credit Card Scheme**, the age limit is **up to 25 years** at the time of application.
You must also be a Bihar resident and have passed 12th standard from a recognized board."""


def _build_rag_context(matched: list, language: str) -> str:
    if not matched:
        return "No matching schemes found."
    lang_keys = [language, "english"]

    def g(d):
        if not d:
            return ""
        if isinstance(d, dict):
            for k in lang_keys:
                v = d.get(k, "")
                if v: return v
            return ""
        return str(d)

    parts = []
    for i, s in enumerate(matched, 1):
        benefits    = _parse_field(s.get("benefits", {}))
        eligibility = _parse_field(s.get("eligibility", {}))
        docs        = _parse_field(s.get("documents_required", {}))
        apply_proc  = _parse_field(s.get("application_process", {}))
        full_desc   = _parse_field(s.get("full_description", {}))
        short       = _clean_text(s.get(language, s.get("english", "")))
        parts.append(
            f"--- SCHEME {i} ---\n"
            f"Name: {s['scheme']} ({s.get('scheme_hindi', '')})\n"
            f"State: {s.get('state', 'Bihar/National')}\n"
            f"Category: {s.get('official_category', '')}\n"
            f"Age Limit: {s.get('age_limit', 'Not specified')}\n"
            f"Benefit Amount: {s.get('benefit_range', 'Not specified')}\n"
            f"Description: {short}\n"
            f"Full Description: {g(full_desc)}\n"
            f"Benefits: {g(benefits)}\n"
            f"Eligibility: {g(eligibility)}\n"
            f"Documents: {g(docs)}\n"
            f"How to Apply: {g(apply_proc)}"
        )
    return "\n\n".join(parts)


def generate_response_llm(
    query: str, language: str, mode: str,
    matched: list, conversation_history: list,
) -> str:
    from app.services.llm.provider import get_provider
    provider = get_provider()

    if provider is None:
        return generate_response(query, language, mode, matched)

    greet_words = ["hello", "hi", "नमस्ते", "हेलो", "प्रणाम", "नमस्कार", "hey"]
    if any(w in query.lower() for w in greet_words) and len(query) < 25:
        return LABELS.get(language, LABELS["english"])["greeting"]

    scheme_context = _build_rag_context(matched, language)
    messages = [{"role": m["role"], "content": m["content"]} for m in (conversation_history or [])[-6:]]

    mode_instruction = (
        "BEGINNER MODE: very simple language, max 4 bullet points, biggest benefit first, end with one simple next step."
        if mode == "beginner"
        else "DETAILED MODE: provide full eligibility criteria, complete document list, application steps, and official portal links if available."
    )

    user_content = (
        f"User question: {query}\n\n"
        f"=== SCHEME DATABASE CONTEXT ===\n{scheme_context}\n\n"
        f"Response instruction: {mode_instruction}\n"
        f"Reply language: {language} (translate everything to this language)"
    )
    messages.append({"role": "user", "content": user_content})

    # Build dynamic system prompt
    dynamic_system = SYSTEM_PROMPT
    dynamic_system += f"\n\nIMPORTANT: The user is communicating in {language}. Translate and reply ENTIRELY in {language}."

    if _is_follow_up(query) and matched:
        pinned_scheme_name = matched[0]["scheme"]
        dynamic_system += f"\n\nFOLLOW-UP CONTEXT: This is a follow-up question. Answer ONLY about '{pinned_scheme_name}'. Do not switch schemes."

    try:
        from app.core.config import settings
        reply = provider.chat(
            messages=messages,
            system=dynamic_system,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
        return reply
    except Exception as e:
        print(f"[LLM] Error: {e}. Falling back to template.")
        return generate_response(query, language, mode, matched)


def process_chat(
    message: str, language: str = "hindi",
    mode: str = "beginner", conversation_history: list = None,
) -> Tuple[str, List[dict], str]:

    detected = detect_language(message)
    if language in ["hindi", "bhojpuri", "english"]:
        effective_language = language
    else:
        effective_language = detected if language == "auto" else language

    history = conversation_history or []

    # Handle follow-up questions
    if _is_follow_up(message) and history:
        pinned = _scheme_from_history(history)
        if pinned:
            matched_with_scores = [(pinned, 999.0)]
        else:
            # Can't pin a scheme — use the last substantive user question to re-search.
            # Do NOT concatenate with the current follow-up word (e.g. "उमिर" alone
            # would corrupt a good PM Kisan query).
            last_user_msg = next(
                (m["content"] for m in reversed(history)
                 if m["role"] == "user" and len(m["content"].split()) > 2),
                ""
            )
            search_query = last_user_msg if last_user_msg else message
            matched_with_scores = _find_matching_schemes_scored(search_query, effective_language, top_k=3)
    else:
        matched_with_scores = _find_matching_schemes_scored(message, effective_language, top_k=3)

    # Reject very weak matches
    if matched_with_scores and matched_with_scores[0][1] < 5.0:
        matched_with_scores = []

    matched = [s for s, _ in matched_with_scores]

    reply = generate_response_llm(
        query=message, language=effective_language, mode=mode,
        matched=matched, conversation_history=history,
    )

    # Fallback guard
    if not reply or len(reply.strip()) < 40:
        reply = generate_response(
            query=message, language=effective_language,
            mode=mode, matched=matched
        )

    top_score = matched_with_scores[0][1] if matched_with_scores else 1
    snippets = []
    for s, sc in matched_with_scores:
        rel_score = round(sc / top_score, 2) if top_score else 0
        if rel_score >= 0.5:
            snippets.append({
                "id": str(s["id"]),
                "name": s["scheme"],
                "relevance_score": rel_score
            })
    snippets = snippets[:3]

    return reply, snippets, effective_language


ACRONYMS = {"pm", "lpg", "bscc", "pmjay", "pmkmy", "fme", "neet", "ssc"}


SCHEME_ALIASES = {
    "pm kisan": ["pm-kisan", "pradhan mantri kisan samman nidhi", "kisan samman"],
    "pmay": ["pradhan mantri awas", "pm awas", "awas yojana"],
    "pm-jay": ["ayushman bharat", "jan arogya"],
}


def _alias_boost(scheme: dict, query: str) -> float:
    q = query.lower()
    name = scheme["scheme"].lower()
    for alias_key, variants in SCHEME_ALIASES.items():
        if alias_key in q or any(v in q for v in variants):
            if alias_key.replace(" ", "") in name.replace(" ", "") or any(v in name for v in variants):
                return 8.0
    return 0.0


FOLLOW_UP_RE = re.compile(
    r'^('
    # English age/eligibility
    r'age\s*limit|eligibility|eligible|qualify|documents?|benefits?|'
    r'how\s+(to\s+)?apply|form|fill|steps?|apply|'
    # Hindi age/eligibility/follow-up
    r'आयु|उम्र|पात्रता|कागज|फायदा|आवेदन|दस्तावेज|लाभ|'
    # Bhojpuri age words (all common spellings)
    r'उमिर|उमर|उमरि|उमिरि|'
    # Bhojpuri follow-up words
    r'पइसा|रकम|कागज|खातिर|कइसे|मिलेला|फायदा'
    r').*$',
    re.I | re.UNICODE
)


def _is_follow_up(query: str) -> bool:
    q = query.strip()
    # Allow up to 7 words for Bhojpuri/Hindi where words are shorter
    return len(q.split()) <= 7 and bool(FOLLOW_UP_RE.match(q))


def _scheme_from_history(history: list) -> dict | None:
    """
    Find the most recently discussed scheme from conversation history.

    Strategy (in order of reliability):
    1. Look for '=== SCHEME DATABASE CONTEXT ===' in the last user message
       sent to the LLM — the scheme name is always the first 'Name:' line there.
    2. Look for **bold scheme name** in assistant messages.
    3. Re-run keyword search on the last user question as final fallback.
    """
    # Strategy 1: Parse the RAG context injected into user messages
    # The LLM user message contains: "=== SCHEME DATABASE CONTEXT ===\n--- SCHEME 1 ---\nName: X"
    for msg in reversed(history):
        if msg["role"] != "user":
            continue
        content = msg.get("content", "")
        m = re.search(r'--- SCHEME 1 ---\s*\nName:\s*(.+?)[\n(]', content)
        if m:
            name = m.group(1).strip()
            for s in _all_schemes:
                if s["scheme"].lower() == name.lower():
                    return s

    # Strategy 2: Look for **bold** scheme name in assistant messages
    for msg in reversed(history):
        if msg["role"] != "assistant":
            continue
        m = re.search(r'\*\*(.+?)\*\*', msg["content"])
        if m:
            name = m.group(1).strip()
            for s in _all_schemes:
                if s["scheme"].lower() == name.lower():
                    return s

    return None


def _answer_follow_up(scheme: dict, query: str, language: str) -> str:
    """Template fallback for follow-up questions when LLM is unavailable."""
    q = query.lower()
    name = scheme.get("scheme", "")
    L = LABELS.get(language, LABELS["english"])

    if any(word in q for word in ["age", "आयु", "उम्र", "उमर", "उमिर", "उमरि", "eligibility", "eligiblity", "eligible", "पात्रता"]):
        age = scheme.get("age_limit", "")
        eligibility = _parse_field(scheme.get("eligibility", {}))
        def g(d): return d.get(language, d.get("english", "")) if isinstance(d, dict) else str(d)
        elig_text = g(eligibility)
        parts = [f"**{name}**"]
        if elig_text:
            parts.append(f"{L['eligibility']}: {elig_text}")
        if age:
            parts.append(f"{L['age']}: {age}")
        if not elig_text and not age:
            parts.append("Eligibility details are not available in our database. Please check the official portal or nearest CSC centre.")
        return "\n".join(parts)

    if any(word in q for word in ["apply", "form", "fill", "आवेदन", "कइसे"]):
        apply_proc = _parse_field(scheme.get("application_process", {}))
        full_desc  = _parse_field(scheme.get("full_description", {}))
        def g(d): return d.get(language, d.get("english", "")) if isinstance(d, dict) else str(d)
        apply_text = g(apply_proc) or g(full_desc) or "Visit your nearest CSC centre or the official state portal to apply."
        return f"**{name}**\n{L['apply']}: {apply_text}"

    if any(word in q for word in ["document", "कागज", "documents", "दस्तावेज"]):
        docs = _parse_field(scheme.get("documents_required", {}))
        def g(d): return d.get(language, d.get("english", "")) if isinstance(d, dict) else str(d)
        doc_text = g(docs) or "Aadhaar Card, Bank Passbook, Passport-size Photo, Income Certificate"
        return f"**{name}**\n{L['documents']}: {doc_text}"

    if any(word in q for word in ["benefit", "फायदा", "benefits", "amount", "रकम", "राशि"]):
        benefits     = _parse_field(scheme.get("benefits", {}))
        benefit_range = scheme.get("benefit_range", "")
        def g(d): return d.get(language, d.get("english", "")) if isinstance(d, dict) else str(d)
        benefit_text = g(benefits)
        parts = [f"**{name}**"]
        if benefit_text:
            parts.append(f"{L['benefits']}: {benefit_text}")
        if benefit_range:
            parts.append(f"{L['benefit_range']}: {benefit_range}")
        return "\n".join(parts)

    short_desc = _clean_text(scheme.get(language, scheme.get("english", "")))
    return f"**{name}**\n{short_desc or 'More details are not available in our database.'}"
