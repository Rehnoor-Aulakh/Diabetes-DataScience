import os
import glob
import re
import hashlib

def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    if not word:
        return 0
    if word[0] in vowels:
        count += 1
    for index in range(1, len(word)):
        if word[index] in vowels and word[index - 1] not in vowels:
            count += 1
    if word.endswith("e"):
        count -= 1
    if count == 0:
        count += 1
    return count

def flesch_reading_ease(text):
    sentences = max(1, len(re.split(r'[.!?]+', text)) - 1)
    words = max(1, len(text.split()))
    syllables = sum(count_syllables(w) for w in text.split())
    
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return score

def main():
    md_files = glob.glob("knowledge_base/*/*/clean/*/*.md")
    
    if not md_files:
        print("No cleaned corpus files found.")
        return
        
    total_docs = len(md_files)
    total_words = 0
    word_counts = []
    heading_counts = []
    
    docs_with_citations = 0
    docs_with_metadata = 0
    
    hashes = {}
    duplicates = []
    
    readability_scores = []
    
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        text_only = re.sub(r'^---[\s\S]*?---\n', '', text)
        
        words = len(text_only.split())
        if words == 0:
            continue
            
        word_counts.append(words)
        total_words += words
        
        headings = len(re.findall(r'^#+ ', text_only, re.MULTILINE))
        heading_counts.append(headings)
        
        readability_scores.append(flesch_reading_ease(text_only))
        
        if re.search(r'\[\d+\]|\(\d+\)|References|Sources', text_only, re.IGNORECASE):
            docs_with_citations += 1
            
        h = hashlib.md5(text_only.encode('utf-8')).hexdigest()
        if h in hashes:
            duplicates.append((md_path, hashes[h]))
        else:
            hashes[h] = md_path
            
        parts = md_path.split(os.sep)
        if "clean" in parts:
            clean_idx = parts.index("clean")
            raw_parts = parts[:clean_idx] + ["raw"] + [parts[clean_idx+1], "metadata.json"]
            meta_path = os.sep.join(raw_parts)
            if os.path.exists(meta_path):
                docs_with_metadata += 1
                
    if not word_counts:
        return
        
    word_counts.sort()
    heading_counts.sort()
    
    avg_words = total_words / total_docs
    med_words = word_counts[len(word_counts)//2]
    avg_headings = sum(heading_counts) / total_docs
    avg_readability = sum(readability_scores) / total_docs
    
    print("=================================")
    print("Corpus Quality Audit")
    print("=================================")
    print(f"Total Documents:       {total_docs}")
    print(f"Total Words:           {total_words:,}")
    print("\n--- Distribution ---")
    print(f"Words per Doc (Avg):   {avg_words:.0f}")
    print(f"Words per Doc (Med):   {med_words}")
    print(f"Words per Doc (Min):   {word_counts[0]}")
    print(f"Words per Doc (Max):   {word_counts[-1]}")
    print(f"Headings per Doc (Avg):{avg_headings:.1f}")
    print("\n--- Integrity ---")
    print(f"Docs with Metadata:    {docs_with_metadata} / {total_docs} ({docs_with_metadata/total_docs*100:.1f}%)")
    print(f"Docs with Citations:   {docs_with_citations} / {total_docs} ({docs_with_citations/total_docs*100:.1f}%)")
    print(f"Exact Duplicates:      {len(duplicates)}")
    if duplicates:
        for dup in duplicates:
            print(f"  - {dup[0]} matches {dup[1]}")
    print("\n--- Readability ---")
    print(f"Avg Flesch Score:      {avg_readability:.1f} (0=Hard, 100=Easy)")

if __name__ == "__main__":
    main()
