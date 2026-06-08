"""
scripts/audit_schemes.py
Approach 1 – Step 1: Audit the schemes JSON for data quality issues.
Run: python scripts/audit_schemes.py
"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/schemes_cleaned.json")

def audit():
    with open(DATA_PATH, encoding="utf-8") as f:
        schemes = json.load(f)

    print(f"Total schemes: {len(schemes)}\n")

    FIELDS = ["eligibility", "application_process", "documents_required", "benefits", "full_description"]
    LANGS  = ["english", "hindi", "bhojpuri"]

    report = {}
    for field in FIELDS:
        report[field] = {lang: [] for lang in LANGS}
        report[field]["thin"] = []

    for s in schemes:
        name = s["scheme"]
        for field in FIELDS:
            val = s.get(field, {})
            if not isinstance(val, dict):
                try:    val = json.loads(val)
                except: val = {"english": str(val)}
            for lang in LANGS:
                text = val.get(lang, "").strip()
                if not text:
                    report[field][lang].append(name)
                elif len(text) < 25:
                    report[field]["thin"].append(f"{name} [{lang}]: '{text}'")

    print("=" * 60)
    print("MISSING FIELDS REPORT")
    print("=" * 60)
    for field in FIELDS:
        print(f"\n📋 {field.upper()}")
        for lang in LANGS:
            missing = report[field][lang]
            print(f"  Missing {lang:10s}: {len(missing):3d} schemes")
            if missing:
                for n in missing[:5]:
                    print(f"    - {n[:70]}")
                if len(missing) > 5:
                    print(f"    ... and {len(missing)-5} more")
        thin = report[field]["thin"]
        if thin:
            print(f"  Thin content: {len(thin)} entries")
            for t in thin[:3]:
                print(f"    - {t[:90]}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_issues = sum(
        len(report[f][l]) for f in FIELDS for l in LANGS
    ) + sum(len(report[f]["thin"]) for f in FIELDS)
    print(f"Total data quality issues: {total_issues}")
    print(f"\nRun enrich_schemes.py to auto-fill missing Bhojpuri translations.")

if __name__ == "__main__":
    audit()
