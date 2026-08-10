"""
Corpus Statistics Dashboard — Aggregates metrics across the entire corpus.
"""

import json
from pathlib import Path

def main():
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        print("Knowledge base directory not found.")
        return
        
    total_articles = 0
    total_words = 0
    total_headings = 0
    total_duplicates = 0
    flagged_articles = 0
    
    source_counts = {}
    
    print("Aggregating Corpus Statistics...")
    
    for module_dir in kb_path.iterdir():
        if module_dir.is_dir() and module_dir.name != "logs":
            for topic_dir in module_dir.iterdir():
                if topic_dir.is_dir():
                    clean_dir = topic_dir / "clean"
                    if clean_dir.exists():
                        for source_dir in clean_dir.iterdir():
                            if source_dir.is_dir():
                                # Check Quality Report
                                qr_path = source_dir / "quality_report.json"
                                if qr_path.exists():
                                    with open(qr_path, 'r', encoding='utf-8') as f:
                                        qr = json.load(f)
                                        
                                    total_articles += 1
                                    total_words += qr.get("words", 0)
                                    total_headings += qr.get("headings", 0)
                                    
                                    if qr.get("status") != "pass":
                                        flagged_articles += 1
                                        
                                    src = source_dir.name
                                    source_counts[src] = source_counts.get(src, 0) + 1
                                    
                                # Check if duplicate
                                raw_meta_path = topic_dir / "raw" / source_dir.name / "metadata.json"
                                if raw_meta_path.exists():
                                    with open(raw_meta_path, 'r', encoding='utf-8') as f:
                                        meta = json.load(f)
                                    if "duplicate_of" in meta:
                                        total_duplicates += 1
                                        
    # Generate Dashboard
    dashboard_path = Path("corpus_dashboard.md")
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write("# Corpus Statistics Dashboard\n\n")
        f.write("## Overview\n")
        f.write(f"- **Total Articles:** {total_articles}\n")
        f.write(f"- **Average Words per Article:** {round(total_words / total_articles) if total_articles else 0}\n")
        f.write(f"- **Average Headings per Article:** {round(total_headings / total_articles) if total_articles else 0}\n")
        f.write(f"- **Duplicate Articles:** {total_duplicates} ({(total_duplicates/total_articles*100) if total_articles else 0:.1f}%)\n")
        f.write(f"- **Flagged by Inspector:** {flagged_articles}\n\n")
        
        f.write("## Source Breakdown\n")
        for src, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{src.upper()}:** {count} articles\n")
            
    print(f"Dashboard generated at {dashboard_path}")

if __name__ == "__main__":
    main()
