import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config

def build_ontology():
    ontology = {}
    
    # 1. Parse config.py for laboratory parameters
    categories = {
        "glycemic": config.GLYCEMIC,
        "renal": config.RENAL,
        "lipid": config.LIPID,
        "liver": config.LIVER,
        "thyroid": config.THYROID,
        "vitamins": config.VITAMINS,
        "inflammation": config.INFLAMMATION,
        "cbc": config.CBC
    }
    
    for category, params in categories.items():
        for display_name, param_id in params.items():
            canonical = param_id.upper()
            
            # Generate aliases
            aliases = [display_name, param_id]
            # Clean up display name for aliases
            clean_name = display_name.replace(" - ", " ").replace("(", "").replace(")", "").strip()
            if clean_name not in aliases:
                aliases.append(clean_name)
                
            # Add specific known aliases for demo
            if canonical == "HBA1C":
                aliases.extend(["A1C", "Hemoglobin A1c", "Glycated Hemoglobin"])
                
            ontology[canonical] = {
                "id": f"TEST_{category.upper()}_{len(ontology)}",
                "canonical": canonical,
                "type": "lab_test",
                "aliases": list(set(aliases)),
                "category": category,
                "unit": "", # To be filled manually or by NLP later
                "related_organs": [],
                "related_conditions": []
            }
            
    # 2. Parse manifest_v1.json for conditions and concepts
    manifest_path = ROOT / 'manifest_v1.json'
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            
        for module in manifest.get("modules", []):
            module_name = module.get("name", "")
            for topic in module.get("topics", []):
                topic_id = topic.get("id").upper()
                title = topic.get("title")
                aliases = topic.get("keywords", [])
                aliases.extend([title, topic.get("id")])
                
                ontology[topic_id] = {
                    "id": f"CONCEPT_{module_name.upper()}_{topic_id}",
                    "canonical": topic_id,
                    "type": "medical_concept",
                    "aliases": list(set(aliases)),
                    "category": module_name,
                    "related_tests": topic.get("related_tests", []),
                    "related_topics": topic.get("related_topics", [])
                }
                
    # Save Ontology
    output_path = Path(__file__).resolve().parent / 'medical_ontology.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ontology, f, indent=2)
        
    print(f"Ontology built successfully! Extracted {len(ontology)} entities.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    build_ontology()
