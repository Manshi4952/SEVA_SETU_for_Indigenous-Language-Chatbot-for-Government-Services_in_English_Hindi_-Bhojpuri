"""
scripts/generate_finetune_data.py
Approach 3 – Step 1: Generate fine-tuning training data from schemes_cleaned.json.

This creates a JSONL file with thousands of Q&A pairs in English, Hindi, and Bhojpuri.
The dataset can be used to fine-tune a small LLM (e.g. Llama-3-8B) on Google Colab.

Run: python scripts/generate_finetune_data.py
Output: data/finetune_dataset.jsonl  (~2000+ training examples)
"""
import json, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_PATH   = os.path.join(os.path.dirname(__file__), "../data/schemes_cleaned.json")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/finetune_dataset.jsonl")

SYSTEM_MSG = (
    "You are SevaSetu, a warm and knowledgeable AI assistant helping citizens of Bihar "
    "understand government welfare schemes. You give accurate, concise, and helpful answers "
    "in the user's language (English, Hindi, or Bhojpuri)."
)

# Question templates per intent, per language
TEMPLATES = {
    "description": {
        "english": [
            "Tell me about {name}",
            "What is {name}?",
            "Explain {name} scheme",
            "Give me information about {name}",
            "What does {name} offer?",
        ],
        "hindi": [
            "{name} के बारे में बताएं",
            "{name} क्या है?",
            "{name} योजना की जानकारी दें",
            "{name} के बारे में जानकारी चाहिए",
            "{name_hindi} योजना क्या है?",
        ],
        "bhojpuri": [
            "{name} के बारे में बताईं",
            "{name} का बा?",
            "{name_hindi} के बारे में बताईं",
            "{name} के जानकारी दीहीं",
        ],
    },
    "benefits": {
        "english": [
            "What are the benefits of {name}?",
            "How much money do I get from {name}?",
            "What is the benefit amount for {name}?",
            "What will I receive under {name}?",
        ],
        "hindi": [
            "{name} से क्या लाभ मिलता है?",
            "{name} में कितना पैसा मिलता है?",
            "{name} के फायदे क्या हैं?",
            "{name} में क्या मिलेगा?",
        ],
        "bhojpuri": [
            "{name} से कतना पइसा मिलेला?",
            "{name} के का फायदा बा?",
            "{name} में का मिलेला?",
            "{name_hindi} में कतना लाभ मिलेला?",
        ],
    },
    "eligibility": {
        "english": [
            "Who is eligible for {name}?",
            "What is the eligibility for {name}?",
            "Can I apply for {name}?",
            "What are the requirements for {name}?",
            "What is the age limit for {name}?",
        ],
        "hindi": [
            "{name} के लिए कौन पात्र है?",
            "{name} की पात्रता क्या है?",
            "{name} के लिए क्या शर्त है?",
            "{name} के लिए उम्र सीमा क्या है?",
            "क्या मैं {name} के लिए आवेदन कर सकता हूँ?",
        ],
        "bhojpuri": [
            "{name} खातिर के पात्र बा?",
            "{name} के लिए का योग्यता चाहीं?",
            "{name} खातिर उमिर सीमा का बा?",
            "{name_hindi} में आवेदन करे के पात्रता का बा?",
        ],
    },
    "documents": {
        "english": [
            "What documents are needed for {name}?",
            "What papers do I need to apply for {name}?",
            "List the documents required for {name}",
        ],
        "hindi": [
            "{name} के लिए कौन से दस्तावेज चाहिए?",
            "{name} आवेदन में कौन से कागज लगेंगे?",
            "{name} के लिए जरूरी कागजात बताएं",
        ],
        "bhojpuri": [
            "{name} खातिर कवन कागज चाहीं?",
            "{name} में आवेदन करे खातिर कवन दस्तावेज लागी?",
            "{name_hindi} के लिए कवन कागज चाहीं?",
        ],
    },
    "apply": {
        "english": [
            "How do I apply for {name}?",
            "How to register for {name}?",
            "What is the process to apply for {name}?",
            "Steps to apply for {name}",
            "How to fill the form for {name}?",
        ],
        "hindi": [
            "{name} में आवेदन कैसे करें?",
            "{name} के लिए रजिस्ट्रेशन कैसे करें?",
            "{name} का फॉर्म कैसे भरें?",
            "{name} में apply करने का तरीका बताएं",
        ],
        "bhojpuri": [
            "{name} में आवेदन कइसे करीं?",
            "{name} खातिर आवेदन कइसे होई?",
            "{name} के फॉर्म कइसे भरीं?",
            "{name_hindi} में पंजीकरण कइसे कइल जाला?",
        ],
    },
}

# Answer builders per intent
def get_field(scheme, field, lang):
    val = scheme.get(field, {})
    if not isinstance(val, dict):
        try:    val = json.loads(val)
        except: return str(val)
    return val.get(lang, val.get("english", "")).strip()


def build_answer(scheme, intent, lang):
    name        = scheme["scheme"]
    name_hindi  = scheme.get("scheme_hindi", name)
    benefit_range = scheme.get("benefit_range", "")
    age_limit   = scheme.get("age_limit", "")

    if intent == "description":
        short = scheme.get(lang, scheme.get("english", ""))
        benefits_text = get_field(scheme, "benefits", lang)
        if lang == "english":
            ans = f"**{name}** — {short}"
            if benefits_text: ans += f"\n\n**Benefits:** {benefits_text}"
            if benefit_range:  ans += f"\n**Amount:** {benefit_range}"
            if age_limit:      ans += f"\n**Age Limit:** {age_limit}"
        elif lang == "hindi":
            ans = f"**{name}** ({name_hindi}) — {short}"
            if benefits_text: ans += f"\n\n**लाभ:** {benefits_text}"
            if benefit_range:  ans += f"\n**राशि:** {benefit_range}"
            if age_limit:      ans += f"\n**आयु सीमा:** {age_limit}"
        else:  # bhojpuri
            ans = f"**{name}** — {short}"
            if benefits_text: ans += f"\n\n**फायदा:** {benefits_text}"
            if benefit_range:  ans += f"\n**मिलेवाला रकम:** {benefit_range}"
            if age_limit:      ans += f"\n**उमिर सीमा:** {age_limit}"
        return ans

    elif intent == "benefits":
        benefits_text = get_field(scheme, "benefits", lang)
        if not benefits_text: return ""
        if lang == "english":
            ans = f"Under **{name}**, you receive:\n{benefits_text}"
            if benefit_range: ans += f"\n\n**Total amount:** {benefit_range}"
        elif lang == "hindi":
            ans = f"**{name}** के अंतर्गत मिलने वाले लाभ:\n{benefits_text}"
            if benefit_range: ans += f"\n\n**कुल राशि:** {benefit_range}"
        else:
            ans = f"**{name}** में मिलेवाला फायदा:\n{benefits_text}"
            if benefit_range: ans += f"\n\n**कुल रकम:** {benefit_range}"
        return ans

    elif intent == "eligibility":
        elig_text = get_field(scheme, "eligibility", lang)
        if not elig_text: return ""
        if lang == "english":
            ans = f"**{name}** eligibility:\n{elig_text}"
            if age_limit: ans += f"\n\n**Age Limit:** {age_limit}"
        elif lang == "hindi":
            ans = f"**{name}** की पात्रता:\n{elig_text}"
            if age_limit: ans += f"\n\n**आयु सीमा:** {age_limit}"
        else:
            ans = f"**{name}** खातिर पात्रता:\n{elig_text}"
            if age_limit: ans += f"\n\n**उमिर सीमा:** {age_limit}"
        return ans

    elif intent == "documents":
        docs_text = get_field(scheme, "documents_required", lang)
        if not docs_text: return ""
        if lang == "english":
            return f"Documents required for **{name}**:\n{docs_text}"
        elif lang == "hindi":
            return f"**{name}** के लिए जरूरी दस्तावेज:\n{docs_text}"
        else:
            return f"**{name}** खातिर जरूरी कागज:\n{docs_text}"

    elif intent == "apply":
        apply_text = get_field(scheme, "application_process", lang)
        full_desc  = get_field(scheme, "full_description", lang)
        if not apply_text: apply_text = full_desc
        if not apply_text: return ""
        if lang == "english":
            return f"How to apply for **{name}**:\n{apply_text}"
        elif lang == "hindi":
            return f"**{name}** में आवेदन कैसे करें:\n{apply_text}"
        else:
            return f"**{name}** में आवेदन कइसे करीं:\n{apply_text}"

    return ""


def generate():
    with open(DATA_PATH, encoding="utf-8") as f:
        schemes = json.load(f)

    training_examples = []
    skipped = 0

    for scheme in schemes:
        name       = scheme["scheme"]
        name_hindi = scheme.get("scheme_hindi", name)

        for intent, lang_templates in TEMPLATES.items():
            for lang, questions in lang_templates.items():
                answer = build_answer(scheme, intent, lang)
                if not answer or len(answer) < 40:
                    skipped += 1
                    continue

                # Use each question template
                for q_template in questions:
                    question = q_template.format(
                        name=name,
                        name_hindi=name_hindi
                    )
                    training_examples.append({
                        "messages": [
                            {"role": "system", "content": SYSTEM_MSG},
                            {"role": "user",   "content": question},
                            {"role": "assistant", "content": answer},
                        ]
                    })

    # Shuffle for better training
    random.seed(42)
    random.shuffle(training_examples)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for ex in training_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"✅ Generated {len(training_examples)} training examples")
    print(f"   Skipped (empty answers): {skipped}")
    print(f"   Saved to: {OUTPUT_PATH}")
    print(f"\n📊 Breakdown by language:")
    for lang in ["english", "hindi", "bhojpuri"]:
        count = sum(1 for ex in training_examples
                    if lang in ex["messages"][1]["content"].lower()
                    or any(c > '\u0900' for c in ex["messages"][1]["content"]))
    print(f"\nNext: Upload finetune_dataset.jsonl to Google Colab and run finetune_colab.py")


if __name__ == "__main__":
    generate()
