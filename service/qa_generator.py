"""
Knowledge QA Dataset Generator — Extracts patient questions from the manifest.
"""

import json
from pathlib import Path

def main():
    manifest_path = Path("manifest_v1.json")
    if not manifest_path.exists():
        print("manifest_v1.json not found.")
        return
        
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    qa_dataset = []
    
    print("Extracting Q&A pairs from manifest...")
    for module in manifest.get("modules", []):
        for topic in module.get("topics", []):
            topic_id = topic.get("id")
            for q in topic.get("patient_questions", []):
                qa_dataset.append({
                    "question": q,
                    "topic_id": topic_id,
                    "ground_truth_answer": "", # To be filled later
                    "document_id": topic.get("document_id", "")
                })
                
    output_path = Path("qa_evaluation_dataset.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_dataset, f, indent=2)
        
    print(f"Generated {len(qa_dataset)} Q&A pairs at {output_path}")

if __name__ == "__main__":
    main()
