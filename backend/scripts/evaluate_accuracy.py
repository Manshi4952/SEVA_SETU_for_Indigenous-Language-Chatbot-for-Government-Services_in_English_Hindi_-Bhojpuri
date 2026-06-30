import os
import json
from groq import Groq
from app.core.config import settings
from app.services.llm.provider import get_provider

def ask_judge(prompt_payload: str) -> float:
    """Calls the cloud Groq model to act as an objective grading judge."""
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an objective AI evaluation judge. Respond ONLY with a single float value between 0.0 and 1.0 representing the score. Do not provide commentary or text headers."},
                {"role": "user", "content": prompt_payload}
            ],
            temperature=0.0,
            max_tokens=10
        )
        return float(response.choices[0].message.content.strip())
    except Exception:
        return 0.0

def run_accuracy_test():
    print("🎯 Initializing SevaSetu Accuracy Grading Suite...")
    
    dataset_path = "data/golden_evaluation_set.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    local_model = get_provider()
    results = []
    
    for idx, case in enumerate(test_cases, start=1):
        query = case["query"]
        ground_truth = case["ground_truth"]
        
        print(f"\n[Test {idx}/{len(test_cases)}] Query: '{query}'")
        
        # Ask your local fine-tuned model for an answer
        model_response = local_model.chat(
            messages=[{"role": "user", "content": query}],
            system="You are SevaSetu, a helpful government schemes assistant."
        )
        print(f"-> Bot Answer: {model_response}")
        
        # Check Groundedness (Did the model stick to the true facts or make things up?)
        groundedness_prompt = f"""
        Compare the Generated Response against the Ground Truth facts. 
        Does the response contradict or add unverified facts not found in the ground truth?
        Ground Truth: {ground_truth}
        Generated Response: {model_response}
        Score 1.0 if perfectly true to facts, 0.0 if it contains hallucinations or lies.
        """
        groundedness_score = ask_judge(groundedness_prompt)
        
        # Check Answer Relevance (Did it actually answer what the user asked?)
        relevance_prompt = f"""
        Evaluate if the Generated Response directly answers the specific user Question.
        User Question: {query}
        Generated Response: {model_response}
        Score 1.0 if perfectly relevant, 0.0 if completely off-topic.
        """
        relevance_score = ask_judge(relevance_prompt)
        
        results.append({"groundedness": groundedness_score, "relevance": relevance_score})
        print(f"   Grading Metrics -> Groundedness: {groundedness_score*100}% | Relevance: {relevance_score*100}%")

    avg_groundedness = sum(r["groundedness"] for r in results) / len(results)
    avg_relevance = sum(r["relevance"] for r in results) / len(results)
    
    print("\n============================================================")
    print("📊 SEVASETU ACCURACY SUMMARY REPORT")
    print("============================================================")
    print(f"✅ Groundedness (Factual Faithfulness): {avg_groundedness * 100:.2f}%")
    print(f"✅ Answer Relevance Score:             {avg_relevance * 100:.2f}%")
    print(f"🏆 Overall System Accuracy:             {((avg_groundedness + avg_relevance)/2)*100:.2f}%")
    print("============================================================")

if __name__ == "__main__":
    run_accuracy_test()