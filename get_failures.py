import glob, os, re

log_files = glob.glob("knowledge_base/logs/scraper_*.log")
latest_log = max(log_files, key=os.path.getctime)

qf = []
http_errs = []

with open(latest_log, "r", encoding="utf-8") as f:
    for line in f:
        match = re.search(r'\[(KB-\d+)\] \[(\w+)\] FAILED — (.*)', line)
        if match:
            doc_id, provider, reason = match.groups()
            if "Quality check failed" in reason:
                qf.append(f"{doc_id} {provider}: {reason}")
            elif "403" in reason or "404" in reason:
                http_errs.append(f"{doc_id} {provider}: {reason}")

print("=== QUALITY FAILED ===")
for q in qf: print(q)
print("\n=== HTTP ERRORS ===")
for h in http_errs: print(h)
