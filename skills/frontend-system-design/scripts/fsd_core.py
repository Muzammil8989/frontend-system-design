"""Shared helpers for the frontend-system-design scripts.

Standard library only (Python 3.9+). No network access, nothing to install.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"

DOMAINS: Dict[str, Tuple[str, Sequence[str]]] = {
    # domain -> (csv file, columns used for search, most important first)
    "products": ("product-types.csv", ("name", "keywords", "description")),
    "stacks": ("stacks.csv", ("name", "keywords", "best_for", "category")),
    "styles": ("ui-styles.csv", ("name", "keywords", "best_for", "characteristics")),
    "palettes": ("palettes.csv", ("name", "tags", "mood", "scheme")),
    "fonts": ("font-pairings.csv", ("heading", "body", "tags", "mood", "best_for")),
    "patterns": ("ux-patterns.csv", ("name", "keywords", "use_when")),
}

_STOPWORDS = {
    "a", "an", "and", "app", "for", "i", "in", "is", "it", "my", "of", "on", "or",
    "that", "the", "to", "with", "want", "build", "building", "create", "make", "need",
    "we", "web", "website", "site", "like", "using", "new", "our", "some",
}


def ensure_utf8_stdout() -> None:
    """Windows consoles default to legacy code pages; force UTF-8 so · and — print."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def positive_int(value: str) -> int:
    """argparse type for counts such as --limit / --max (rejects 0 and negatives)."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from None
    if n < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return n


def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text.lower())
    out: List[str] = []
    for tok in tokens:
        if tok in _STOPWORDS:
            continue
        out.append(tok)
        if "-" in tok:  # "real-time" also matches "real" + "time"
            out.extend(p for p in tok.split("-") if p and p not in _STOPWORDS)
        if len(tok) > 4 and tok.endswith("s"):  # naive singular: "dashboards" -> "dashboard"
            out.append(tok[:-1])
    return out


def load_csv(name: str) -> List[Dict[str, str]]:
    path = DATA_DIR / name
    with path.open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def split_list(value: str) -> List[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


class BM25:
    """Okapi BM25 over CSV rows. Earlier fields are weighted higher."""

    def __init__(self, rows: List[Dict[str, str]], fields: Sequence[str], k1: float = 1.4, b: float = 0.75):
        self.rows = rows
        self.k1, self.b = k1, b
        self.docs: List[List[str]] = []
        for row in rows:
            doc: List[str] = []
            for rank, field in enumerate(fields):
                weight = max(1, len(fields) - rank)  # first field counts most
                doc.extend(tokenize(row.get(field, "")) * weight)
            # always make the id searchable
            doc.extend(tokenize(row.get("id", "")) * 2)
            self.docs.append(doc)
        self.avgdl = sum(len(d) for d in self.docs) / max(1, len(self.docs))
        df: Dict[str, int] = {}
        for doc in self.docs:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: str) -> List[Tuple[float, Dict[str, str]]]:
        terms = tokenize(query)
        results = []
        for doc, row in zip(self.docs, self.rows):
            if not doc:
                continue
            tf: Dict[str, int] = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1
            s = 0.0
            for t in terms:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(doc) / self.avgdl))
            if s > 0:
                results.append((s, row))
        results.sort(key=lambda r: r[0], reverse=True)
        return results


def search(domain: str, query: str, limit: int = 5) -> List[Tuple[float, Dict[str, str]]]:
    if domain not in DOMAINS:
        raise ValueError(f"unknown domain {domain!r}; choose from {', '.join(DOMAINS)}")
    file, fields = DOMAINS[domain]
    return BM25(load_csv(file), fields).score(query)[:limit]


def by_id(name: str) -> Dict[str, Dict[str, str]]:
    return {row["id"]: row for row in load_csv(name)}


# ---------------------------------------------------------------- color math

def _channel(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG 2.x contrast ratio between two hex colors."""
    l1, l2 = relative_luminance(fg), relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def md_table(headers: Iterable[str], rows: Iterable[Iterable[object]]) -> str:
    headers = list(headers)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(lines)
