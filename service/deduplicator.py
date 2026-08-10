"""
Deduplicator — Flags exact syndicated overlap between sources.
"""

import json
from pathlib import Path
import re

def get_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts using token sets."""
    # Tokenize (simple alphanumeric words)
    set1 = set(re.findall(r'\b\w+\b', text1.lower()))
    set2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not set1 or not set2:
        return 0.0
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union)

def deduplicate_topic(topic_dir: Path, threshold: float = 0.90):
    clean_dir = topic_dir / "clean"
    if not clean_dir.exists():
        return
        
    # Collect all sources for this topic
    sources = []
    for source_dir in clean_dir.iterdir():
        if source_dir.is_dir():
            md_files = list(source_dir.glob("*.md"))
            if md_files:
                # Use the latest version (assuming v1.md, v2.md, etc.)
                latest_md = max(md_files, key=lambda p: int(re.search(r'v(\d+)', p.name).group(1)))
                with open(latest_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                    text_only = re.sub(r'^---[\s\S]*?---\n', '', content)
                    sources.append({
                        "source": source_dir.name,
                        "path": latest_md,
                        "content": text_only
                    })
                    
    # Compare all pairs
    duplicates_found = []
    for i in range(len(sources)):
        for j in range(i + 1, len(sources)):
            src1 = sources[i]
            src2 = sources[j]
            
            similarity = get_jaccard_similarity(src1["content"], src2["content"])
            
            if similarity > threshold:
                duplicates_found.append({
                    "source1": src1["source"],
                    "source2": src2["source"],
                    "similarity": round(similarity, 3)
                })
                
                # Flag the second source as duplicate in its metadata
                raw_meta_path = topic_dir / "raw" / src2["source"] / "metadata.json"
                if raw_meta_path.exists():
                    with open(raw_meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    meta["duplicate_of"] = src1["source"]
                    meta["similarity_score"] = similarity
                    
                    with open(raw_meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, indent=2)
                        
    return duplicates_found

def main():
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        print("Knowledge base directory not found.")
        return
        
    print("Running Deduplicator...")
    total_duplicates = 0
    
    # Iterate through all modules and topics
    for module_dir in kb_path.iterdir():
        if module_dir.is_dir() and module_dir.name != "logs":
            for topic_dir in module_dir.iterdir():
                if topic_dir.is_dir():
                    dupes = deduplicate_topic(topic_dir)
                    if dupes:
                        print(f"Topic {topic_dir.name}:")
                        for d in dupes:
                            print(f"  {d['source1']} overlaps {d['source2']} (Similarity: {d['similarity']})")
                            total_duplicates += 1
                            
    print(f"\nTotal duplicates flagged: {total_duplicates}")

if __name__ == "__main__":
    main()
