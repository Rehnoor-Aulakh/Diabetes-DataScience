import os
import glob
import re
from collections import defaultdict

def main():
    # Find the most recent log file
    log_files = glob.glob("knowledge_base/logs/scraper_*.log")
    if not log_files:
        print("No log files found.")
        return
        
    latest_log = max(log_files, key=os.path.getctime)
    print(f"Analyzing {latest_log}\n")
    
    categories = defaultdict(int)
    provider_failures = defaultdict(int)
    
    with open(latest_log, "r", encoding="utf-8") as f:
        for line in f:
            # Look for lines like: [INFO   ] [KB-000088] [niddk] FAILED — ...
            match = re.search(r'\[KB-\d+\] \[(\w+)\] (FAILED|SKIPPED) — (.*)', line)
            if match:
                provider = match.group(1)
                status = match.group(2)
                reason = match.group(3)
                
                provider_failures[provider] += 1
                
                if "BLOCKED_403" in reason:
                    categories["403_BLOCKED"] += 1
                elif "NOT_FOUND_404" in reason:
                    categories["404_NOT_FOUND"] += 1
                elif status == "SKIPPED" and "Search disabled" in reason:
                    categories["SEARCH_DISABLED"] += 1
                elif "Quality check failed" in reason:
                    categories["QUALITY_FAILED"] += 1
                elif "TIMEOUT" in reason:
                    categories["TIMEOUT"] += 1
                elif "Search returned no valid URLs" in reason:
                    categories["SEARCH_NO_RESULTS"] += 1
                else:
                    categories["UNKNOWN"] += 1
                    
    print("=================================")
    print("Failure Summary")
    print("=================================\n")
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"{cat+':':<20} {count}")
        
    print("\nTop failing providers\n")
    for prov, count in sorted(provider_failures.items(), key=lambda x: x[1], reverse=True):
        print(f"{prov.capitalize():<12} {count}")

if __name__ == "__main__":
    main()
