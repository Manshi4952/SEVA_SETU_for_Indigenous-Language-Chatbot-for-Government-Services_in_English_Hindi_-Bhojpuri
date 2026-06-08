"""
scripts/enrich_schemes.py
Approach 1 – Step 2: Auto-enrich missing Bhojpuri translations using Groq LLM.

This script:
  1. Finds all schemes missing Bhojpuri in eligibility/benefits/documents/application_process
  2. Calls Groq to translate from Hindi → Bhojpuri (authentic, not Romanized)
  3. Saves enriched data back to schemes_cleaned.json (backs up original first)

Run: python scripts/enrich_schemes.py
Requires: GROQ_API_KEY in backend/.env
"""
import json, os, sys, time, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DATA_PATH    = os.path.join(os.path.dirname(__file__), "../data/schemes_cleaned.json")
BACKUP_PATH  = DATA_PATH.replace(".json", "_backup.json")
FIELDS       = ["eligibility", "application_process", "benefits", "documents_required"]

TRANSLATE_SYSTEM = """You are an expert translator specializing in Bhojpuri language.
Translate the given Hindi government scheme text into authentic Bhojpuri (Devanagari script).
Rules:
- Use natural Bhojpuri words: बा (है), बाड़न (हैं), मिलेला (मिलता है), जाला (जाता है), खातिर (के लिए), करीं (करें), दीहल जाई (दिया जाएगा), लइका (बच्चा), बुजुर्ग (elderly)
- Keep numbers, scheme names, rupee amounts, and portal URLs in original form
- Do NOT use Hindi grammar — use Bhojpuri sentence structure
- Keep it simple and clear for rural citizens
- Return ONLY the translated text, nothing else"""


def translate_to_bhojpuri(hindi_text: str, scheme_name: str) -> str:
    if not GROQ_API_KEY:
        print("  [SKIP] No GROQ_API_KEY set")
        return ""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": TRANSLATE_SYSTEM},
                {"role": "user", "content": f"Scheme: {scheme_name}\nHindi text: {hindi_text}"}
            ],
            max_tokens=400,
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        return ""


def enrich():
    # Backup original
    if not os.path.exists(BACKUP_PATH):
        shutil.copy(DATA_PATH, BACKUP_PATH)
        print(f"✅ Backup saved to {BACKUP_PATH}")

    with open(DATA_PATH, encoding="utf-8") as f:
        schemes = json.load(f)

    total_enriched = 0
    total_schemes_updated = 0

    for i, scheme in enumerate(schemes):
        name = scheme["scheme"]
        scheme_updated = False

        for field in FIELDS:
            val = scheme.get(field, {})
            if not isinstance(val, dict):
                try:    val = json.loads(val)
                except: val = {"english": str(val)}

            bhojpuri = val.get("bhojpuri", "").strip()
            hindi    = val.get("hindi", "").strip()

            if bhojpuri or not hindi:
                continue  # Already has Bhojpuri or no Hindi to translate from

            print(f"\n[{i+1}/218] {name[:55]} | field: {field}")
            print(f"  Hindi: {hindi[:100]}...")

            translated = translate_to_bhojpuri(hindi, name)
            if translated:
                val["bhojpuri"] = translated
                scheme[field] = val
                scheme_updated = True
                total_enriched += 1
                print(f"  ✅ Bhojpuri: {translated[:100]}...")
                time.sleep(0.3)  # Rate limit buffer

        if scheme_updated:
            total_schemes_updated += 1

        # Save after every 10 schemes to avoid losing progress
        if (i + 1) % 10 == 0:
            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(schemes, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Progress saved ({i+1}/218 schemes processed)")

    # Final save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(schemes, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Enrichment complete!")
    print(f"   Schemes updated: {total_schemes_updated}")
    print(f"   Fields enriched: {total_enriched}")
    print(f"   Data saved to:   {DATA_PATH}")
    print(f"\nNext: Run rebuild_index.py to update the FAISS search index.")


if __name__ == "__main__":
    enrich()
