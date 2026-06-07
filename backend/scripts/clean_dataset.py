#!/usr/bin/env python3
"""
clean_dataset.py — Strip [cite: XX] artifacts and normalize whitespace.
Run once before starting the server:  python scripts/clean_dataset.py
"""
import json
import re
from pathlib import Path

INPUT  = Path(__file__).parent.parent / "data" / "schemes.json"
OUTPUT = Path(__file__).parent.parent / "data" / "schemes_cleaned.json"

CITE_PATTERN = re.compile(r'\[cite:\s*\d+\]')

def clean_value(v):
    if isinstance(v, str):
        # 1. Remove citations:
        v = CITE_PATTERN.sub('', v)
        
        # 2. NEW: Remove broken markdown images: ![image alt text](http://link...)
        v = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', v)
        
        # 3. Clean up extra spaces caused by deletions
        v = re.sub(r'\s{2,}', ' ', v).strip()
        return v
        
    if isinstance(v, dict):
        return {k: clean_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [clean_value(item) for item in v]
    return v

def clean_scheme(scheme):
    return {k: clean_value(v) for k, v in scheme.items()}


if __name__ == "__main__":
    with open(INPUT, encoding='utf-8') as f:
        schemes = json.load(f)

    cleaned = [clean_scheme(s) for s in schemes]

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    count = sum(
        1 for s in schemes
        for v in s.values()
        if isinstance(v, str) and '[cite:' in v
    )
    nested_count = 0
    for s in schemes:
        for v in s.values():
            if isinstance(v, dict):
                for vv in v.values():
                    if isinstance(vv, str) and '[cite:' in vv:
                        nested_count += 1

    print(f"✅ Cleaned {len(cleaned)} schemes.")
    print(f"   Found citations in {count} top-level + {nested_count} nested string fields.")
    print(f"   Output: {OUTPUT}")



