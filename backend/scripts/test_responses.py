"""
scripts/test_responses.py
Test the RAG pipeline and LLM responses locally without starting the full server.

Run: python scripts/test_responses.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.chdir(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(".env")

from app.core.config import settings
from app.services.rag_service import initialize_rag, process_chat

def run_tests():
    print("=" * 60)
    print("SevaSetu Response Quality Test")
    print("=" * 60)

    print("\nInitialising RAG...")
    initialize_rag(settings.KNOWLEDGE_BASE_PATH, settings.FAISS_INDEX_PATH)

    TEST_CASES = [
        # (query, language, mode, description)
        ("Tell me about PM Kisan scheme",          "english",  "beginner",  "English description"),
        ("How to apply for Bihar Student Credit Card?", "english", "beginner", "English apply"),
        ("PM किसान योजना के बारे में बताएं",         "hindi",    "beginner",  "Hindi description"),
        ("वृद्धजन पेंशन में कितना पैसा मिलता है?",   "hindi",    "beginner",  "Hindi benefits"),
        ("बिहार स्टूडेंट क्रेडिट कार्ड में कइसे आवेदन करीं?", "bhojpuri", "beginner", "Bhojpuri apply"),
        ("उमिर सीमा का बा?",                         "bhojpuri", "beginner",  "Bhojpuri age follow-up"),
        ("PMAY आवास योजना का बा?",                   "bhojpuri", "beginner",  "Bhojpuri PMAY"),
        ("age limit",                                "english",  "beginner",  "English follow-up"),
        ("what documents do I need?",               "english",  "beginner",  "English docs follow-up"),
        ("कन्या उत्थान योजना के लिए पात्रता क्या है?", "hindi", "advanced", "Hindi eligibility detailed"),
    ]

    history = []
    passed = 0

    for i, (query, lang, mode, desc) in enumerate(TEST_CASES, 1):
        print(f"\n{'─'*60}")
        print(f"Test {i}: {desc}")
        print(f"Query [{lang}/{mode}]: {query}")
        print("─" * 60)

        reply, snippets, detected_lang = process_chat(
            message=query,
            language=lang,
            mode=mode,
            conversation_history=history,
        )

        print(f"Response [{detected_lang}]:\n{reply[:500]}")
        if len(reply) > 500: print("  ...(truncated)")

        if snippets:
            print(f"\nMatched schemes:")
            for s in snippets:
                print(f"  • {s['name']} ({s['relevance_score']*100:.0f}%)")

        # Quality checks
        bad_phrases = [
            "here is the information", "as per the database",
            "eligibility details not available", "more details not available",
            "i am an ai", "feel free to ask", "i hope this helps",
        ]
        issues = [p for p in bad_phrases if p in reply.lower()]

        if issues:
            print(f"\n⚠️  QUALITY ISSUES: {issues}")
        else:
            print(f"\n✅ Pass")
            passed += 1

        # Add to history for follow-up tests
        history.append({"role": "user",      "content": query})
        history.append({"role": "assistant", "content": reply})

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(TEST_CASES)} tests passed")
    if passed < len(TEST_CASES):
        print("Review the ⚠️  warnings above and tune SYSTEM_PROMPT or data.")
    else:
        print("All tests passed! ✅")

if __name__ == "__main__":
    run_tests()
