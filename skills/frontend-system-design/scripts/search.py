#!/usr/bin/env python3
"""Search the curated frontend design datasets (BM25 ranking).

Examples:
  python3 search.py --domain palettes "fintech trustworthy dark"
  python3 search.py --domain fonts "editorial elegant"
  python3 search.py --domain styles "playful kids education"
  python3 search.py --domain patterns "checkout"
  python3 search.py --domain stacks "charts large time series"
  python3 search.py --domain products "habit tracker offline"
"""

from __future__ import annotations

import argparse
import json
import sys

from fsd_core import DOMAINS, contrast_ratio, ensure_utf8_stdout, md_table, positive_int, search

SUMMARY_FIELDS = {
    "products": ("id", "name", "rendering"),
    "stacks": ("id", "name", "category", "best_for", "url"),
    "styles": ("id", "name", "best_for", "avoid_for", "a11y_notes"),
    "palettes": ("id", "name", "scheme", "bg", "text", "primary", "on_primary", "accent"),
    "fonts": ("id", "heading", "body", "mono", "best_for", "notes"),
    "patterns": ("id", "name", "use_when", "key_rules", "anti_patterns"),
}


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="free-text query, e.g. 'fintech dark trustworthy'")
    parser.add_argument("--domain", "-d", required=True, choices=sorted(DOMAINS))
    parser.add_argument("--limit", "-n", type=positive_int, default=5)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    results = search(args.domain, args.query, args.limit)

    if args.json:
        payload = [dict(row, _score=round(score, 3)) for score, row in results]
        if args.domain == "palettes":
            for row in payload:
                row["_contrast"] = {
                    "text_on_bg": round(contrast_ratio(row["text"], row["bg"]), 2),
                    "on_primary": round(contrast_ratio(row["on_primary"], row["primary"]), 2),
                }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if results else 1  # same exit code as the Markdown output

    if not results:
        print(f"No matches in '{args.domain}' for: {args.query}\nTry broader words (industry, mood, screen name).")
        return 1

    fields = SUMMARY_FIELDS[args.domain]
    rows = []
    for score, row in results:
        cells = [row.get(f, "") for f in fields]
        if args.domain == "palettes":
            cells.append(f"{contrast_ratio(row['text'], row['bg']):.1f}:1 / {contrast_ratio(row['on_primary'], row['primary']):.1f}:1")
        rows.append(cells + [f"{score:.2f}"])
    headers = list(fields) + (["contrast text/primary"] if args.domain == "palettes" else []) + ["score"]
    print(f"### {args.domain}: \"{args.query}\"\n")
    print(md_table(headers, rows))
    if args.domain == "palettes":
        top = results[0][1]
        print("\nCSS tokens for the top match:\n```css\n:root {")
        for key in ("bg", "surface", "text", "muted", "primary", "on_primary", "accent", "border", "success", "warning", "danger"):
            print(f"  --color-{key.replace('_', '-')}: {top[key]};")
        print("}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
