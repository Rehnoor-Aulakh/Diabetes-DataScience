"""
Corpus Inspector — Scans the knowledge base and generates quality_report.json
for each scraped markdown document.
"""

import json
import os
import re
from pathlib import Path

def count_words(text: str) -> int:
    return len(text.split())

def count_paragraphs(text: str) -> int:
    return len([p for p in text.split('\n\n') if p.strip()])

def count_headings(text: str) -> int:
    return len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE))

def count_tables(text: str) -> int:
    # Basic markdown table detection
    return len(re.findall(r'\|.*\|.*\n\|[-:| ]+\|', text))

def count_images(text: str) -> int:
    # Basic markdown image detection
    return len(re.findall(r'!\[.*?\]\(.*?\)', text))

def estimate_reading_time(word_count: int, words_per_minute: int = 238) -> int:
    return max(1, round(word_count / words_per_minute))

def check_formatting_issues(text: str) -> list[str]:
    issues = []
    
    # Check for unclosed markdown links or images
    if text.count('[') != text.count(']'):
        issues.append("Unmatched brackets []")
    if text.count('(') != text.count(')'):
        issues.append("Unmatched parentheses ()")
        
    # Check for leaked navigation text (common in medical sites)
    nav_keywords = ["Skip to Main Content", "Skip to main content", "Navigation", "Menu", "Search Site"]
    for kw in nav_keywords:
        if kw in text:
            issues.append(f"Leaked navigation text: '{kw}'")
            
    return issues

def process_file(clean_md_path: Path):
    with open(clean_md_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Strip metadata header for word count
    text_content = re.sub(r'^---[\s\S]*?---\n', '', text)
    
    words = count_words(text_content)
    paragraphs = count_paragraphs(text_content)
    headings = count_headings(text_content)
    tables = count_tables(text_content)
    images = count_images(text_content)
    reading_time = estimate_reading_time(words)
    issues = check_formatting_issues(text_content)
    
    report = {
        "words": words,
        "paragraphs": paragraphs,
        "headings": headings,
        "tables": tables,
        "images": images,
        "reading_time_minutes": reading_time,
        "formatting_issues": issues,
        "status": "pass" if words > 300 and headings > 0 and len(issues) == 0 else "flagged"
    }
    
    report_path = clean_md_path.parent / "quality_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    return report

def main():
    kb_path = Path("knowledge_base")
    if not kb_path.exists():
        print("Knowledge base directory not found.")
        return
        
    print("Running Corpus Inspector...")
    total = 0
    passed = 0
    flagged = 0
    
    for clean_dir in kb_path.rglob("clean/*"):
        if clean_dir.is_dir():
            for md_file in clean_dir.glob("*.md"):
                report = process_file(md_file)
                total += 1
                if report["status"] == "pass":
                    passed += 1
                else:
                    flagged += 1
                    
    print(f"Inspected {total} documents.")
    print(f"Passed: {passed}")
    print(f"Flagged: {flagged}")

if __name__ == "__main__":
    main()
