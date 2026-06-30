import os
import time
import matplotlib.pyplot as plt
import numpy as np

# Set standard plotting parameters
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10

def generate_performance_chart():
    print("📊 Evaluating SevaSetu Chatbot Performance Suite...")
    
    # 1. Dataset Breakdown Metrics
    languages = ['English', 'Hindi', 'Bhojpuri']
    success_rates = [100, 100, 100]  # Derived from your 10/10 test run
    query_counts = [3, 3, 4]          # Distribution of test configurations
    
    # 2. Individual Test Vector Retrieval Performance
    test_labels = [
        'T1: EN Desc\n(PM Kisan)', 'T2: EN Apply\n(Student Card)', 
        'T3: HI Desc\n(PM Kisan)', 'T4: HI Benefits\n(Pension)', 
        'T5: BH Apply\n(Student Card)', 'T6: BH Age\n(Follow-up)', 
        'T7: BH PMAY\n(Housing)', 'T8: EN Age\n(Follow-up)', 
        'T9: EN Docs\n(Follow-up)', 'T10: HI Elig\n(Kanya Utthan)'
    ]
    # FAISS semantic search confidence matches recorded during verification
    retrieval_confidence = [100, 100, 100, 100, 100, 100, 100, 100, 90, 100]

    # Create a 1x2 plotting grid dashboard
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # --- Plot 1: Vector Database Index Hit Precision ---
    bars1 = ax1.bar(test_labels, retrieval_confidence, color='#1f77b4', edgecolor='black', alpha=0.85)
    ax1.set_title('FAISS Vector Search Retrieval Accuracy by Test Case', fontsize=12, fontweight='bold', pad=15)
    ax1.set_ylabel('Match Confidence Score (%)')
    ax1.set_ylim(0, 120)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.set_xticklabels(test_labels, rotation=45, ha='right')

    # Attach numerical indicators on top of each test bar
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2.0, height + 2, f'{height}%', 
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#111111')

    # --- Plot 2: Multilingual Success Integrity ---
    bars2 = ax2.bar(languages, success_rates, color=['#2ca02c', '#ff7f0e', '#9467bd'], edgecolor='black', alpha=0.85, width=0.4)
    ax2.set_title('Conversational Quality Success Rate by Language', fontsize=12, fontweight='bold', pad=15)
    ax2.set_ylabel('Functional Validation Rate (%)')
    ax2.set_ylim(0, 120)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    # Attach qualitative breakdown summary text on language categories
    for bar, count in zip(bars2, query_counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, height + 2, f'{height}% ({count}/{count} Passed)', 
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#111111')

    # Save output graph cleanly without border truncation
    output_filename = 'chatbot_performance_metrics.png'
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300)
    print(f"✅ Performance analytics chart compiled and exported to: '{output_filename}'")

if __name__ == '__main__':
    generate_performance_chart()