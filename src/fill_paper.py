"""
fill_paper.py
-------------
Fills the {{placeholder}} tokens in paper/paper.md with the real numbers from
data/results.json (produced by the notebook), writing paper/paper_filled.md.

Run after the notebook finishes:  python src/fill_paper.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_path = os.path.join(ROOT, "data", "results.json")
paper_path = os.path.join(ROOT, "paper", "paper.md")
out_path = os.path.join(ROOT, "paper", "paper_filled.md")

if not os.path.exists(results_path):
    raise SystemExit(
        "data/results.json not found. Run the notebook first; it writes the "
        "results the paper cites."
    )

with open(results_path) as f:
    results = json.load(f)

with open(paper_path, encoding="utf-8") as f:
    text = f.read()

missing = set()


def repl(match):
    key = match.group(1)
    if key in results:
        return str(results[key])
    missing.add(key)
    return match.group(0)  # leave it visible so you can see what is unfilled


filled = re.sub(r"\{\{(\w+)\}\}", repl, text)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(filled)

print(f"Wrote {out_path}")
if missing:
    print("WARNING: no value for these placeholders (left as-is):")
    for k in sorted(missing):
        print("  -", k)
else:
    print("All placeholders filled.")
