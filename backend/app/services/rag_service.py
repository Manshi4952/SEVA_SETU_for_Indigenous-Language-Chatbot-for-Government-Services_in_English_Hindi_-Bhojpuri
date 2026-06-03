"""
rag_service.py – Upgraded RAG pipeline for SevaSetu.

Changes from v1:
  - LLM-powered response generation (Anthropic Claude)
  - Conversation history injected into every LLM call
  - [cite: XX] artifact stripping
  - Relevance scores in snippets (fixes NaN% UI bug)
  - State bias: Bihar/Central schemes ranked higher
  - Transliterated Bhojpuri detection in Roman script
  - Smart topic-aware fallback
"""

from __future__ import annotations
import json
import re
from typing import List, Tuple

import faiss  # Make sure this is imported at the top of your file!

# Add a global variable to store the index so your search function can use it
 
_faiss_index = None
_all_schemes: List[dict] = []
_llm_client = None

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
    global _all_schemes, _faiss_index  # Grab both globals
    
    # 1. Load the JSON text data (Your original code)
    try:
        with open(knowledge_base_path, encoding="utf-8") as f:
            _all_schemes = json.load(f)
        print(f"[RAG] Loaded {len(_all_schemes)} schemes from {knowledge_base_path}.")
    except Exception as e:
        print(f"[RAG] Warning loading JSON: {e}")

    # 2. Load the FAISS embeddings (The new code for Step C)
    try:
        _faiss_index = faiss.read_index(index_path)
        print(f"[RAG] Successfully loaded FAISS index from {index_path}.")
    except Exception as e:
        print(f"[RAG] Warning loading FAISS index: {e}")


def _get_llm_client():
    global _llm_client
    if _llm_client is not None:
        return _llm_client
    try:
        from app.core.config import settings
        if settings.ANTHROPIC_API_KEY:
            import anthropic
            _llm_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            print("[LLM] Anthropic Claude client initialised.")
            return _llm_client
    except ImportError:
        pass
    print("[LLM] No ANTHROPIC_API_KEY – running in template mode.")
    return None


TRANSLITERATED_BHOJPURI = [
    "kaise","kahe","kavan","kavana","batain","badin","milela",
    "jaala","baate","kachu","samjh","aavata","hamar","tohar",
    "hamni","raura","bhaiya","maai","baap","kari","karo","hoi",
]


def detect_language(text: str) -> str:
    if re.search(r'[\u0900-\u097F]', text):
        bhojpuri_markers = ["बा ","बा?","खातिर","मिलेला","करेला","जाला",
                            "बाटे","काहे","रहल","गइल","बाड़न","ओकरा",
                            "एकरा","कइसे","पइसा"]
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
        "english":  ["benefit","get","amount","money","receive","rupee","how much","gain"],
        "hindi":    ["लाभ","फायदा","राशि","रुपए","पैसा","कितना","मिलता","मिलेगा"],
        "bhojpuri": ["फायदा","मिलेला","पइसा","रुपया","कतना","लाभ"],
    },
    "eligibility": {
        "english":  ["eligible","eligibility","qualify","who can","criteria","age","requirement"],
        "hindi":    ["पात्रता","पात्र","योग्यता","कौन","उम्र","आयु","शर्त"],
        "bhojpuri": ["पात्रता","पाता","खातिर","कवन","उमर"],
    },
    "documents": {
        "english":  ["document","required","paper","certificate","aadhaar","proof","need"],
        "hindi":    ["दस्तावेज","कागज","प्रमाण","आधार","जरूरी","चाहिए"],
        "bhojpuri": ["कागज","दस्तावेज","आधार","जरूरी","चाही"],
    },
    "apply": {
        "english":  ["apply","register","how to","process","application","enroll","form","fill"],
        "hindi":    ["आवेदन","कैसे","पंजीकरण","प्रक्रिया","फॉर्म","भरें"],
        "bhojpuri": ["आवेदन","कइसे","पंजीकरण","फॉर्म","कइल जाला","भरीं"],
    },
    "description": {
        "english":  ["what is","about","tell me","explain","describe","information","details"],
        "hindi":    ["क्या है","बताएं","जानकारी","विवरण","बारे में"],
        "bhojpuri": ["का बा","बताईं","जानकारी","बारे में"],
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
    "the","and","for","about","tell","what","how","please","is","me",
    "में","के","की","का","है","हैं","कि","से","को","पर","एक",
    "बारे","बताएं","बताओ","क्या","कैसे","मुझे","मेरे","यह","वह",
    "खातिर","बा","का","एह","ओह","आउर","बाटे","हम","तू","आप",
}

BIHAR_STATES = {"bihar","central","all india","national",""}


def _score_scheme(scheme: dict, keywords: List[str], query: str, language: str) -> float:
    score = 0.0
    name_lower = scheme["scheme"].lower()
    name_hindi = scheme.get("scheme_hindi","")
    desc = scheme.get(language, scheme.get("english","")).lower()
    scheme_kw_text = " ".join(_parse_list(scheme.get("keywords",[]))).lower()
    is_devanagari = re.search(r'[\u0900-\u097F]', query)

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in name_lower: score += 4.0
        if kw in name_hindi: score += 4.0
        if kw_lower in scheme_kw_text or kw in scheme_kw_text: score += 3.0
        if is_devanagari:
            if kw in desc or kw in scheme.get(language,""): score += 1.5
        else:
            if kw_lower in desc: score += 1.5
        if kw_lower in scheme.get("official_category","").lower(): score += 2.0

    state = scheme.get("state","").lower().strip()
    if state in BIHAR_STATES: score += 1.5
    elif state: score -= 0.5

    # --- ADD THE ALIAS BOOST HERE ---
    score += _alias_boost(scheme, query)

    return score


def _find_matching_schemes_scored(
    query: str, language: str, top_k: int = 3
) -> List[Tuple[dict, float]]:
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
    name_hindi = scheme.get("scheme_hindi","")
    benefits    = _parse_field(scheme.get("benefits",{}))
    eligibility = _parse_field(scheme.get("eligibility",{}))
    docs        = _parse_field(scheme.get("documents_required",{}))
    apply_proc  = _parse_field(scheme.get("application_process",{}))
    full_desc   = _parse_field(scheme.get("full_description",{}))

    def g(d): return d.get(language, d.get("english",""))

    header = f"**{name}**"
    if name_hindi and name_hindi != name:
        header += f" ({name_hindi})"
    parts = [header,""]

    age = scheme.get("age_limit","")
    benefit_range = scheme.get("benefit_range","")
    category = scheme.get("official_category","")
    short_desc = _clean_text(scheme.get(language, scheme.get("english","")))

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
        parts.append(f"{L['eligibility']}: {g(eligibility)}")
        if age: parts.append(f"{L['age']}: {age}")
    elif intent == "documents":
        parts.append(f"{L['documents']}: {g(docs)}")
    elif intent == "apply":
        # ==========================================
        # NEW LOGIC: PREVENT EMPTY FORM RESPONSES
        # ==========================================
        apply_text = g(apply_proc)
        
        # If application instructions are empty, try falling back to other descriptions
        if not apply_text or not str(apply_text).strip():
            apply_text = g(full_desc)
            if not apply_text or not str(apply_text).strip():
                apply_text = short_desc
            # Final fallback if the scheme is completely empty
            if not apply_text or not str(apply_text).strip():
                apply_text = "Application details are not in our database. Visit the official state portal or CSC."
                
        parts.append(f"{L['apply']}: {apply_text}")

    return "\n".join(p for p in parts if p is not None)


def generate_response(query: str, language: str, mode: str, matched: list) -> str:
    L = LABELS.get(language, LABELS["english"])
    greet_words = ["hello","hi","नमस्ते","हेलो","प्रणाम","नमस्कार","hey"]
    
    if any(w in query.lower() for w in greet_words) and len(query) < 25:
        return L["greeting"]
        
    if not matched:
        return _smart_fallback(query, language)

    # ==========================================
    # FINAL FIX: TEMPLATE FOLLOW-UP AMNESIA
    # ==========================================
    # If the user asks a follow-up, intercept it before the normal template builder runs
    if _is_follow_up(query):
        return _answer_follow_up(matched[0], query, language)

    # Otherwise, continue with normal template building
    intent = detect_intent(query, language)
    
    if len(matched) == 1 or mode == "beginner":
        return L["intro"] + _build_scheme_response(matched[0], intent, language, mode)
        
    parts = [L["multi_found"],""]
    for scheme in matched[:3]:
        parts.append(_build_scheme_response(scheme, intent, language, mode))
        parts.append("\n---\n")
        
    return "\n".join(parts)


SYSTEM_PROMPT = """You are SevaSetu, a warm and helpful AI assistant that helps citizens of Bihar (India) understand government welfare schemes. You have access to a database of 218+ schemes.

LANGUAGE RULES:
- User writes Bhojpuri (Devanagari or Roman) → reply in Bhojpuri
- User writes Hindi → reply in Hindi
- User writes English → reply in English
- Never reply in Roman transliteration when user used Devanagari

PERSONA: warm friend at the village panchayat — patient, simple words, specific amounts

BEGINNER MODE: max 4 bullets, no jargon, lead with biggest benefit, end with one simple next step
ADVANCED MODE: all eligibility, full documents list, official portal URL, all amounts

FORMAT RULES:
1. Start DIRECTLY with content — never say "Here is the information:"
2. For apply/process queries: use numbered steps (1. 2. 3.)
3. Always end with ONE follow-up question or clear next step
4. Use **bold** for scheme names and key rupee amounts
5. If user says they don't understand → simplify the SAME topic, don't change subject
6. If query is ambiguous → ask ONE clarifying question

CRITICAL: Only use scheme information from the context provided. Never invent details."""


def _build_rag_context(matched: list, language: str) -> str:
    if not matched:
        return "No matching schemes found."
    lang_keys = [language, "english"]

    def g(d):
        for k in lang_keys:
            v = d.get(k,"")
            if v: return v
        return ""

    parts = []
    for i, s in enumerate(matched, 1):
        benefits   = _parse_field(s.get("benefits",{}))
        eligibility = _parse_field(s.get("eligibility",{}))
        docs       = _parse_field(s.get("documents_required",{}))
        apply_proc = _parse_field(s.get("application_process",{}))
        full_desc  = _parse_field(s.get("full_description",{}))
        short      = _clean_text(s.get(language, s.get("english","")))
        parts.append(
            f"--- SCHEME {i} ---\n"
            f"Name: {s['scheme']} ({s.get('scheme_hindi','')})\n"
            f"State: {s.get('state','Bihar/National')}\n"
            f"Category: {s.get('official_category','')}\n"
            f"Age Limit: {s.get('age_limit','Not specified')}\n"
            f"Benefit Amount: {s.get('benefit_range','Not specified')}\n"
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
    client = _get_llm_client()
    if client is None:
        return generate_response(query, language, mode, matched)

    greet_words = ["hello","hi","नमस्ते","हेलो","प्रणाम","नमस्कार","hey"]
    if any(w in query.lower() for w in greet_words) and len(query) < 25:
        return LABELS.get(language, LABELS["english"])["greeting"]

    scheme_context = _build_rag_context(matched, language)
    messages = [{"role": m["role"], "content": m["content"]} for m in (conversation_history or [])[-6:]]

    mode_instruction = (
        "BEGINNER MODE: very simple language, max 4 points, end with one simple next step."
        if mode == "beginner"
        else "ADVANCED MODE: full details, all conditions, official links."
    )
    user_content = (
        f"User question: {query}\n\n"
        f"=== SCHEMES FROM DATABASE ===\n{scheme_context}\n\n"
        f"{mode_instruction}"
    )
    messages.append({"role": "user", "content": user_content})

    # ==========================================
    # FINAL FIXES: DYNAMIC SYSTEM PROMPT
    # ==========================================
    # 1. Grab your existing global system prompt
    dynamic_system_prompt = SYSTEM_PROMPT 

    # 2. Fix Issue 5 (Bhojpuri Language Bug): Force translation
    dynamic_system_prompt += f"\n\nCRITICAL LANGUAGE INSTRUCTION: Even if the context documents below are written in English, you MUST translate and reply entirely in {language}. Do not mix languages."

    # 3. Fix Follow-up Amnesia: Force the AI to stick to the active scheme
    if _is_follow_up(query) and matched:
        pinned_scheme_name = matched[0]["scheme"]
        dynamic_system_prompt += f"\n\nCRITICAL CONTEXT INSTRUCTION: The user is asking a follow-up about the scheme already discussed. Do NOT switch to a different scheme. Answer ONLY about: {pinned_scheme_name}."

    try:
        from app.core.config import settings
        resp = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=settings.LLM_MAX_TOKENS,
            system=dynamic_system_prompt,  # <--- We pass the new, strict prompt here!
            messages=messages,
        )
        return resp.content[0].text
    except Exception as e:
        print(f"[LLM] Error: {e}. Falling back to template.")
        return generate_response(query, language, mode, matched)


def process_chat(
    message: str, language: str = "hindi",
    mode: str = "beginner", conversation_history: list = None,
) -> Tuple[str, List[dict], str]:
    
    # ==========================================
    # FIX: ISSUE 5 (FORCE UI LANGUAGE)
    # ==========================================
    detected = detect_language(message)
    # If the user explicitly picked a language in the UI menu, force the bot to use it.
    if language in ["hindi", "bhojpuri", "english"]:
        effective_language = language
    else:
        effective_language = detected if language == "auto" else language
    
    # Ensure history is always a list
    history = conversation_history or []

    # ==========================================
    # 1. NEW LOGIC: HANDLE FOLLOW-UP QUESTIONS
    # ==========================================
    if _is_follow_up(message) and history:
        pinned = _scheme_from_history(history)
        if pinned:
            # We found the scheme! Lock onto it with a 999.0 score.
            matched_with_scores = [(pinned, 999.0)]
        else:
            # We couldn't find the exact scheme, so glue their last question to this new one
            last_user_msg = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
            message_for_search = f"{last_user_msg} {message}"
            matched_with_scores = _find_matching_schemes_scored(message_for_search, effective_language, top_k=3)
    else:
        # It's a brand new question, do a normal search
        matched_with_scores = _find_matching_schemes_scored(message, effective_language, top_k=3)

    # ==========================================
    # 2. NEW LOGIC: REJECT WEAK MATCHES
    # ==========================================
    # If the absolute best match is terrible (under 5.0), throw it away so the bot doesn't hallucinate
    if matched_with_scores and matched_with_scores[0][1] < 5.0:
        matched_with_scores = []

    # Extract just the scheme dictionaries to pass to the LLM
    matched = [s for s, _ in matched_with_scores]

    # Generate the actual chat reply
    reply = generate_response_llm(
        query=message, language=effective_language, mode=mode,
        matched=matched, conversation_history=history,
    )

    # ==========================================
    # FIX: ISSUE 3 (EMPTY AI FALLBACK GUARD)
    # ==========================================
    # If the AI fails and returns a blank/short string, fall back to the standard template
    if not reply or len(reply.strip()) < 40:
        reply = generate_response(
            query=message, language=effective_language, 
            mode=mode, matched=matched
        )

    # ==========================================
    # FIX: ISSUE 6 (THE 100% UI CHIPS & 0.5 CUTOFF)
    # ==========================================
    # Find the top score (or default to 1 if empty)
    top_score = matched_with_scores[0][1] if matched_with_scores else 1
    
    snippets = []
    for s, sc in matched_with_scores:
        rel_score = round(sc / top_score, 2) if top_score else 0
        
        # Only show the chip in the UI if it is at least a 50% match
        if rel_score >= 0.5:
            snippets.append({
                "id": str(s["id"]), 
                "name": s["scheme"], 
                "relevance_score": rel_score
            })
            
    # Cap the display at a maximum of 3 chips
    snippets = snippets[:3]
    
    return reply, snippets, effective_language



ACRONYMS = {"pm", "lpg", "bscc", "pmjay", "pmkmy", "fme", "neet", "ssc"}

def _extract_keywords(query: str) -> list[str]:
    if re.search(r'[\u0900-\u097F]', query):
        words = [w.strip('।,?!।॥') for w in query.split() if len(w.strip('।,?!।॥')) >= 2]
    else:
        words = re.findall(r'\w+', query.lower())
    keywords = []
    for w in words:
        wl = w.lower()
        if wl in STOP_WORDS:
            continue
        if len(wl) >= 3 or wl in ACRONYMS:
            keywords.append(wl if not re.search(r'[\u0900-\u097F]', w) else w)
    return keywords


SCHEME_ALIASES = {
    "pm kisan": ["pm-kisan", "pradhan mantri kisan samman nidhi", "kisan samman"],
    "pmay": ["pradhan mantri awas", "pm awas", "awas yojana"],
    "pm-jay": ["ayushman bharat", "jan arogya"],
    # add 20–30 common ones users ask for
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
    r'^(age\s*limit|आयु|उम्र|eligibility|documents?|benefits?|'
    r'how\s+(to\s+)?apply|form|fill|steps?|पात्रता|कागज|फायदा|आवेदन).*$',
    re.I
)

def _is_follow_up(query: str) -> bool:
    q = query.strip()
    return len(q.split()) <= 5 and bool(FOLLOW_UP_RE.match(q))


def _scheme_from_history(history: list) -> dict | None:
    for msg in reversed(history):
        if msg["role"] != "assistant":
            continue
        # Match **Scheme Name** from markdown
        m = re.search(r'\*\*(.+?)\*\*', msg["content"])
        if m:
            name = m.group(1).strip()
            for s in _all_schemes:
                if s["scheme"].lower() == name.lower():
                    return s
    return None

def _answer_follow_up(scheme: dict, query: str, language: str) -> str:
    """Handles follow-up questions when the LLM is turned off."""
    q = query.lower()
    name = scheme.get("scheme", "")
    
    if any(word in q for word in ["age", "आयु", "उम्र", "eligibility", "पात्रता"]):
        ans = scheme.get("eligibility_criteria", "Eligibility details not available.")
        return f"**{name}** - Eligibility & Age:\n{ans}"
        
    if any(word in q for word in ["apply", "form", "fill", "आवेदन"]):
        ans = scheme.get("application_process", "Application details not available.")
        return f"**{name}** - How to Apply:\n{ans}"
        
    if any(word in q for word in ["document", "कागज", "documents"]):
        ans = scheme.get("documents_required", "Document details not available.")
        return f"**{name}** - Required Documents:\n{ans}"
        
    return f"**{name}**:\n{scheme.get('scheme_short_description', 'More details not available.')}"