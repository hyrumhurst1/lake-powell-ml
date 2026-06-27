"""
fill_paper.py
-------------
Fills the {{placeholder}} tokens in paper/paper.md with the real numbers from
results.json["paper_tokens"] (written by the notebook's Step 7b), producing
paper/paper_filled.md.

Run after the notebook finishes:  python src/fill_paper.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_path = os.path.join(ROOT, "data", "results.json")
# The notebook may write results.json to the working dir; check both.
if not os.path.exists(results_path):
    alt = os.path.join(ROOT, "results.json")
    if os.path.exists(alt):
        results_path = alt

paper_path = os.path.join(ROOT, "paper", "paper.md")
out_path = os.path.join(ROOT, "paper", "paper_filled.md")

if not os.path.exists(results_path):
    raise SystemExit(
        "results.json not found. Run the notebook first (it writes results.json "
        "with a paper_tokens block in Step 7b), and put it under data/ or the "
        "repo root."
    )

with open(results_path) as f:
    results = json.load(f)

tokens = results.get("paper_tokens")
if tokens is None:
    raise SystemExit(
        "results.json has no 'paper_tokens'. Re-run the notebook including "
        "Step 7b, which writes that block."
    )

with open(paper_path, encoding="utf-8") as f:
    text = f.read()

missing = set()


def repl(match):
    key = match.group(1)
    if key in tokens and tokens[key] is not None:
        return str(tokens[key])
    missing.add(key)
    return match.group(0)  # leave visible so unfilled tokens are obvious


filled = re.sub(r"\{\{(\w+)\}\}", repl, text)

with open(out_path, "w", encoding="utf-8") as f:
    f.write(filled)

print(f"Wrote {out_path}")
if missing:
    print("WARNING: no value for these tokens (left as-is):")
    for k in sorted(missing):
        print("  -", k)
else:
    print("All placeholders filled.")
