"""
scripts/rebuild_index.py
Approach 1 – Step 3: Rebuild the FAISS semantic search index after enriching data.

Run: python scripts/rebuild_index.py
"""
import json, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_PATH  = os.path.join(os.path.dirname(__file__), "../data/schemes_cleaned.json")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "../data/faiss.index")


def build_text_for_embedding(scheme: dict) -> str:
    """Build rich text for embedding — covers all languages and fields."""
    parts = [
        scheme.get("scheme", ""),
        scheme.get("scheme_hindi", ""),
        scheme.get("english", ""),
        scheme.get("hindi", ""),
        scheme.get("bhojpuri", ""),
    ]

    def g(val, lang):
        if isinstance(val, dict): return val.get(lang, val.get("english", ""))
        return str(val)

    for field in ["benefits", "eligibility", "application_process", "documents_required"]:
        val = scheme.get(field, {})
        for lang in ["english", "hindi", "bhojpuri"]:
            parts.append(g(val, lang))

    keywords = scheme.get("keywords", [])
    if isinstance(keywords, list):
        parts.extend(keywords)
    elif isinstance(keywords, str):
        try:    parts.extend(json.loads(keywords))
        except: parts.append(keywords)

    parts.append(scheme.get("official_category", ""))
    parts.append(scheme.get("state", ""))

    return " | ".join(p for p in parts if p and str(p).strip())


def rebuild():
    print("Loading schemes...")
    with open(DATA_PATH, encoding="utf-8") as f:
        schemes = json.load(f)
    print(f"Loaded {len(schemes)} schemes.")

    print("Loading sentence-transformers model...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("Run: pip install sentence-transformers")
        sys.exit(1)

    print("Building embeddings (this takes ~1-2 minutes)...")
    texts = [build_text_for_embedding(s) for s in schemes]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings = np.array(embeddings, dtype="float32")

    print("Building FAISS index...")
    import faiss
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity on normalized vectors
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    print(f"✅ FAISS index saved to {INDEX_PATH}")
    print(f"   Dimensions: {dim}")
    print(f"   Vectors: {index.ntotal}")
    print(f"\nRestart the backend server to use the new index.")


if __name__ == "__main__":
    rebuild()
