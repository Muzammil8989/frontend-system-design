#!/usr/bin/env python3
"""Score website or app copy for human, specific writing (0-100).

Flags AI-sounding phrases (data/ai-tells.csv), filler and hedges, passive voice,
monotone rhythm, very long sentences, reading grade (Flesch-Kincaid), exclamation,
emoji and em-dash overuse, vague superlatives, "we" over "you", and stacked triads.
Reads .md, .txt and .html (tags, markdown syntax and code blocks are stripped).

Examples:
  python3 copy_check.py landing.md
  python3 copy_check.py index.html --json
  python3 copy_check.py onboarding.md --mode ui --min-score 80
  cat draft.txt | python3 copy_check.py -

Standard library only (Python 3.9+). Exit code 1 when --min-score or
--fail-on-high is not met, 2 on bad input (unreadable, or no copy found).
"""

from __future__ import annotations

import argparse
import bisect
import csv
import html as htmllib
import json
import re
import statistics
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
AI_TELLS_CSV = DATA_DIR / "ai-tells.csv"

CATEGORIES = ("buzzword", "filler", "hedge", "cliche", "transition", "hype", "structure")
SEVERITIES = ("high", "medium", "low")
TARGET_SCORE = 80
GRADE_LIMITS = {"marketing": 9.0, "ui": 7.0}

# points per finding, and the most a single check can take off the score
TELL_POINTS = {"high": 8, "medium": 4, "low": 2}
CAPS = {
    "ai-tell": 45, "filler-hedge": 15, "passive": 10, "long-sentence": 12, "rhythm": 10,
    "reading-grade": 15, "exclamation": 8, "emoji": 8, "em-dash": 8, "vague-claim": 12,
    "customer-focus": 8, "triad": 9,
}

VAGUE_HIGH = ("#1", "number one", "world-class", "best-in-class", "industry-leading",
              "market-leading", "award-winning", "most trusted", "unparalleled", "unmatched",
              "second to none")
VAGUE_MEDIUM = ("best", "leading", "fastest", "top-rated", "premier")

YOU_WORDS = {"you", "your", "yours", "you're", "you'll", "you've", "you'd", "yourself", "yourselves"}
WE_WORDS = {"we", "our", "ours", "us", "we're", "we'll", "we've", "we'd", "ourselves"}

IRREGULAR_PARTICIPLES = {
    "built", "made", "done", "given", "taken", "seen", "written", "shown", "sent", "paid",
    "kept", "found", "held", "told", "brought", "bought", "caught", "taught", "thought",
    "chosen", "driven", "grown", "drawn", "known", "spoken", "stolen", "broken", "forgotten",
    "hidden", "eaten", "fallen", "forgiven", "frozen", "worn", "torn", "sold", "lost", "meant",
    "set", "put", "cut", "run", "begun", "understood", "felt", "heard", "led", "fed", "met",
    "spent", "lent", "dealt", "left", "won", "shut", "hit", "read",
}
NOT_PARTICIPLES = {
    "need", "speed", "feed", "seed", "breed", "bleed", "heed", "deed", "bed", "red", "shed",
    "wed", "hundred", "sacred", "naked", "wicked", "rugged", "aged", "embed", "exceed",
    "proceed", "succeed", "indeed", "tired", "excited", "interested", "bored", "worried",
    "pleased", "married", "advanced", "detailed", "dedicated", "sophisticated", "limited",
    "talented", "experienced", "qualified", "skilled", "related", "concerned", "complicated",
    "crowded", "focused", "inspired", "motivated", "relaxed", "satisfied", "scared",
    "surprised", "supposed", "excited", "thrilled", "delighted", "allowed",
}
PASSIVE_RE = re.compile(
    r"\b(am|is|are|was|were|be|been|being)\s+(?:(?:not|never|also|still|just|\w+ly)\s+){0,2}"
    r"([a-z]+)\b",
    re.IGNORECASE,
)
ABBREVIATIONS = {"e.g", "i.e", "etc", "vs", "dr", "mr", "mrs", "ms", "st", "no", "approx", "inc", "ltd"}
ABBREV_WINDOW = 16  # chars before a period inspected for an abbreviation (longer than any entry above)
WORD_RE = re.compile(r"[A-Za-z0-9#]+(?:['-][A-Za-z0-9]+)*")
SENT_END_RE = re.compile(r"[.!?]+[\"')\]]*(?=\s|$)")
TRIAD_RE = re.compile(
    r"\b[\w'-]+(?:\s+[\w'-]+){0,2},\s+[\w'-]+(?:\s+[\w'-]+){0,2},?\s+(?:and|or)\s+[\w'-]+",
    re.IGNORECASE,
)
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002B50\U00002B55\U0000231A\U0000231B\U000023E9-\U000023FA]"
)
EM_DASH_RE = re.compile(r"—|\s--\s|\s–\s")
BLOCK_TAGS = {
    "p", "div", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "dl", "dt",
    "dd", "tr", "td", "th", "table", "section", "article", "header", "footer", "nav", "main",
    "aside", "blockquote", "figure", "figcaption", "button", "label", "option", "title",
    "form", "fieldset", "legend", "summary", "details", "caption", "pre",
}
ATTR_TEXT_RE = re.compile(r"""\b(alt|aria-label|title|placeholder)\s*=\s*("([^"]*)"|'([^']*)')""", re.IGNORECASE)


def ensure_utf8_stdout() -> None:
    """Windows consoles default to legacy code pages; force UTF-8 so arrows and dashes print."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


# ------------------------------------------------------------------ data

def load_tells(path: Path = AI_TELLS_CSV) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def phrase_pattern(phrase: str) -> "re.Pattern[str]":
    """Whole-word, case-insensitive match. Single words also match simple inflections."""
    words = phrase.lower().split()
    body = r"\s+".join(re.escape(w) for w in words)
    if len(words) == 1 and re.fullmatch(r"[a-z]+", words[0]):
        w = words[0]
        alts = [re.escape(w) + r"(?:s|es|d|ed|ing|ly)?"]
        if w.endswith("e"):
            alts.append(re.escape(w[:-1]) + "ing")
        if w.endswith("y"):
            alts.append(re.escape(w[:-1]) + "(?:ies|ied)")
        body = "(?:" + "|".join(alts) + ")"
    return re.compile(r"(?<![\w-])" + body + r"(?![\w-])", re.IGNORECASE)


@lru_cache(maxsize=4)
def _compiled_tells(path: str) -> Tuple[Tuple[Dict[str, str], "re.Pattern[str]"], ...]:
    rows = load_tells(Path(path))
    rows.sort(key=lambda r: len(r["phrase"]), reverse=True)  # longest first wins overlaps
    return tuple((r, phrase_pattern(r["phrase"])) for r in rows)


# ------------------------------------------------------------------ text extraction

Unit = Optional[Tuple[int, str, bool]]  # (line, text, standalone); None = paragraph break


def _clean_inline(s: str) -> str:
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<https?://[^>]+>", "", s)
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"(\*\*|__|~~)", "", s)
    s = re.sub(r"(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)", "", s)
    s = htmllib.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def markdown_units(text: str) -> List[Unit]:
    lines = text.split("\n")  # not splitlines(): form feeds and U+2028 must not shift line numbers
    out: List[Unit] = []
    start = 0
    if lines and lines[0].strip() == "---":  # YAML front matter
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                start = j + 1
                break
    fence = ""
    for idx in range(start, len(lines)):
        n, s = idx + 1, lines[idx].strip()
        m = re.match(r"(```|~~~)", s)
        if m:
            if not fence:
                fence = m.group(1)
            elif s.startswith(fence):
                fence = ""
            out.append(None)
            continue
        if fence:
            continue
        if not s or re.fullmatch(r"[-*_=]{3,}", s):
            out.append(None)
            continue
        if s.startswith("|"):
            if re.fullmatch(r"[\s:|-]+", s):
                continue
            out.append(None)
            for cell in s.strip("|").split("|"):
                c = _clean_inline(cell)
                if c:
                    out.append((n, c, True))
            continue
        standalone = False
        hm = re.match(r"#{1,6}\s+", s)
        if hm:
            s, standalone = s[hm.end():], True
        while s.startswith(">"):
            s = s[1:].lstrip()
        lm = re.match(r"([-*+]|\d+[.)])\s+", s)
        if lm:
            s, standalone = s[lm.end():], True
        s = re.sub(r"^\[[ xX]\]\s+", "", s)
        c = _clean_inline(s)
        if c:
            out.append((n, c, standalone))
    return out


def html_units(text: str) -> List[Unit]:
    blank = lambda m: "\n" * m.group(0).count("\n")  # noqa: E731  keep line numbers
    text = re.sub(r"(?is)<(script|style|noscript|template|svg|code)\b.*?</\1\s*>", blank, text)
    text = re.sub(r"(?s)<!--.*?-->", blank, text)
    out: List[Unit] = []
    newlines = [m.start() for m in re.finditer("\n", text)]

    def line_of(pos: int) -> int:
        return bisect.bisect_left(newlines, pos) + 1  # newlines before pos, + 1

    def emit(segment: str, pos: int) -> None:
        line = line_of(pos)
        for i, piece in enumerate(segment.split("\n")):
            c = re.sub(r"\s+", " ", htmllib.unescape(piece)).strip()
            if c:
                out.append((line + i, c, False))

    pos = 0
    for m in re.finditer(r"<[^>]*>", text):
        emit(text[pos:m.start()], pos)
        tag = re.match(r"<\s*/?\s*([a-zA-Z0-9]+)", m.group(0))
        name = tag.group(1).lower() if tag else ""
        if name in BLOCK_TAGS:
            out.append(None)
        for a in ATTR_TEXT_RE.finditer(m.group(0)):
            value = htmllib.unescape(a.group(3) if a.group(3) is not None else a.group(4) or "").strip()
            if value and name != "meta":
                out.extend([None, (line_of(m.start()), value, True), None])
        pos = m.end()
    emit(text[pos:], pos)
    return out


class Paragraph:
    """Joined text of consecutive units, with offset -> source line mapping."""

    def __init__(self, standalone: bool = False):
        self.text = ""
        self.offsets: List[int] = []
        self.lines: List[int] = []
        self.standalone = standalone

    def add(self, line: int, piece: str) -> None:
        if self.text:
            self.text += "" if re.match(r"[,.;:!?)]", piece) else " "
        self.offsets.append(len(self.text))
        self.lines.append(line)
        self.text += piece

    def line_at(self, offset: int) -> int:
        i = bisect.bisect_right(self.offsets, offset) - 1
        return self.lines[max(i, 0)] if self.lines else 0


def build_paragraphs(units: Sequence[Unit], soft_breaks: bool = True) -> List[Paragraph]:
    paras: List[Paragraph] = []
    cur: Optional[Paragraph] = None
    for u in units:
        if u is None:
            cur = None
            continue
        line, text, standalone = u
        if standalone:
            p = Paragraph(standalone=True)
            p.add(line, text)
            paras.append(p)
            cur = None
            continue
        # a short line without end punctuation followed by a capitalised line is a heading/label
        if cur is not None and soft_breaks and not re.search(r"[.!?,;:—-]$", cur.text) \
                and re.match(r"[A-Z0-9\"']", text):
            cur = None
        if cur is None:
            cur = Paragraph()
            paras.append(cur)
        cur.add(line, text)
    return paras


def extract(text: str, fmt: str = "auto") -> List[Paragraph]:
    if text.startswith("\ufeff"):  # BOM would hide front matter and the first heading
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    if fmt == "auto":
        fmt = "html" if re.search(r"<(html|body|p|div|h[1-6]|section|button)\b", text, re.I) else "md"
    if fmt == "html":
        return build_paragraphs(html_units(text), soft_breaks=False)
    return build_paragraphs(markdown_units(text), soft_breaks=True)


# ------------------------------------------------------------------ sentences & metrics

def split_sentences(para: Paragraph) -> List[Dict[str, object]]:
    sentences, start = [], 0
    text = para.text
    for m in SENT_END_RE.finditer(text):
        # only the word right before the period matters: look at a bounded window, not the whole
        # sentence so far (which grows without limit through runs of abbreviations like "e.g. e.g.")
        lo = max(start, m.start() - ABBREV_WINDOW)
        prev = re.search(r"([A-Za-z.]+)$", text[lo:m.start()])
        if m.group(0).startswith(".") and prev and prev.group(1).lower().rstrip(".") in ABBREVIATIONS:
            continue
        sentences.append((start, m.end()))
        start = m.end()
    if start < len(text):
        sentences.append((start, len(text)))
    out = []
    for a, b in sentences:
        chunk = text[a:b]
        lead = len(chunk) - len(chunk.lstrip())
        s = chunk.strip()
        words = WORD_RE.findall(s)
        if words:
            out.append({"text": s, "start": a + lead, "line": para.line_at(a + lead),
                        "words": words, "standalone": para.standalone})
    return out


def count_syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def flesch_kincaid_grade(words: int, sentences: int, syllables: int) -> float:
    if not words or not sentences:
        return 0.0
    return round(0.39 * words / sentences + 11.8 * syllables / words - 15.59, 1)


def _finding(findings: List[Dict[str, object]], line, check, severity, match, suggestion, category=""):
    findings.append({"line": line, "check": check, "severity": severity, "match": match,
                     "suggestion": suggestion, "category": category or check})


# ------------------------------------------------------------------ analysis

def analyze(text: str, fmt: str = "auto", mode: str = "marketing",
            max_grade: Optional[float] = None, tells_path: Path = AI_TELLS_CSV) -> Dict[str, object]:
    """Analyze copy and return score, stats, deductions and line-level findings."""
    paras = extract(text, fmt)
    max_grade = GRADE_LIMITS.get(mode, 9.0) if max_grade is None else max_grade
    findings: List[Dict[str, object]] = []
    points: Dict[str, float] = {k: 0.0 for k in CAPS}
    details: Dict[str, str] = {}

    sentences = [s for p in paras for s in split_sentences(p)]
    all_words = [w for s in sentences for w in s["words"]]  # type: ignore[union-attr]
    n_words, n_sent = len(all_words), len(sentences)

    # 1. AI tells, filler and hedges (longest phrase wins overlapping spans)
    tell_counts = {"ai-tell": 0, "filler-hedge": 0}
    for p in paras:
        taken: List[Tuple[int, int]] = []
        for row, pat in _compiled_tells(str(tells_path)):
            for m in pat.finditer(p.text):
                if any(m.start() < b and a < m.end() for a, b in taken):
                    continue
                taken.append((m.start(), m.end()))
                bucket = "filler-hedge" if row["category"] in ("filler", "hedge") else "ai-tell"
                tell_counts[bucket] += 1
                points[bucket] += TELL_POINTS.get(row["severity"], 2)
                _finding(findings, p.line_at(m.start()), bucket, row["severity"], m.group(0),
                         row["suggestion"], row["category"])
    details["ai-tell"] = f"{tell_counts['ai-tell']} AI-sounding phrase(s)"
    details["filler-hedge"] = f"{tell_counts['filler-hedge']} filler/hedge phrase(s)"

    # 2. passive voice
    passive = 0
    for s in sentences:
        for m in PASSIVE_RE.finditer(str(s["text"])):
            verb = m.group(2).lower()
            if verb in NOT_PARTICIPLES:
                continue
            if (verb.endswith("ed") and len(verb) > 3) or verb in IRREGULAR_PARTICIPLES:
                passive += 1
                _finding(findings, s["line"], "passive", "low", m.group(0),
                         "Name who does it: \"We send the report\" instead of \"The report is sent\".")
                break
    allowed = max(1, round(n_sent * 0.1))
    points["passive"] = max(0, passive - allowed) * 2
    details["passive"] = f"{passive} passive sentence(s), {allowed} allowed"

    # 3. sentence length and rhythm
    lengths = [len(s["words"]) for s in sentences]  # type: ignore[arg-type]
    long_count = 0
    for s, n in zip(sentences, lengths):
        if n > 30:
            long_count += 1
            points["long-sentence"] += 3
            _finding(findings, s["line"], "long-sentence", "medium", f"{n} words",
                     "Split it. One idea per sentence; aim for 8-20 words.")
    details["long-sentence"] = f"{long_count} sentence(s) over 30 words"

    prose = [len(s["words"]) for s in sentences if not s["standalone"] and len(s["words"]) >= 3]  # type: ignore[arg-type]
    stdev = round(statistics.pstdev(prose), 1) if len(prose) >= 2 else 0.0
    avg = round(sum(lengths) / n_sent, 1) if n_sent else 0.0
    rhythm_notes = []
    if len(prose) >= 5 and stdev < 3.5:
        points["rhythm"] += 6
        rhythm_notes.append(f"monotone rhythm (sentence-length spread {stdev} words)")
        _finding(findings, None, "rhythm", "medium", f"stdev {stdev}",
                 "Mix lengths: follow a long sentence with a short one. Like this.")
    prose_avg = sum(prose) / len(prose) if prose else 0
    if len(prose) >= 3 and prose_avg > 22:
        points["rhythm"] += 4
        rhythm_notes.append(f"long average sentence ({prose_avg:.1f} words)")
        _finding(findings, None, "rhythm", "medium", f"avg {prose_avg:.1f} words",
                 "Shorten: aim for an average of 12-18 words in marketing copy.")
    details["rhythm"] = "; ".join(rhythm_notes) or "varied"

    # 4. reading grade
    syllables = sum(count_syllables(w) for w in all_words)
    grade = flesch_kincaid_grade(n_words, n_sent, syllables)
    if n_words >= 40 and grade > max_grade:
        points["reading-grade"] = round((grade - max_grade) * 3)
        _finding(findings, None, "reading-grade", "medium", f"grade {grade}",
                 f"Aim for grade {max_grade:g} or lower: shorter sentences, shorter words.")
    details["reading-grade"] = f"Flesch-Kincaid grade {grade} (target <= {max_grade:g})"

    # 5. punctuation & symbols
    excl = emoji = dashes = 0
    excl_allowed = max(1, n_sent // 10)
    emoji_allowed = max(1, n_words // 200)
    dash_allowed = max(1, n_words // 120)
    for p in paras:
        for m in re.finditer(r"!", p.text):
            excl += 1
            if excl > excl_allowed:
                _finding(findings, p.line_at(m.start()), "exclamation", "low", "!",
                         "Let the words carry the energy. Keep at most one per page.")
        for m in EMOJI_RE.finditer(p.text):
            emoji += 1
            if emoji > emoji_allowed:
                _finding(findings, p.line_at(m.start()), "emoji", "low", m.group(0),
                         "Drop decorative emoji; keep one only where it adds meaning.")
        for m in EM_DASH_RE.finditer(p.text):
            dashes += 1
            if dashes > dash_allowed:
                _finding(findings, p.line_at(m.start()), "em-dash", "low", m.group(0).strip(),
                         "Use a period, comma or parentheses instead.")
    points["exclamation"] = max(0, excl - excl_allowed) * 2
    points["emoji"] = max(0, emoji - emoji_allowed) * 2
    points["em-dash"] = max(0, dashes - dash_allowed) * 2
    details["exclamation"] = f"{excl} exclamation mark(s), {excl_allowed} allowed"
    details["emoji"] = f"{emoji} emoji, {emoji_allowed} allowed"
    details["em-dash"] = f"{dashes} em-dash(es), {dash_allowed} allowed"

    # 6. vague superlatives without a number in the same sentence
    vague = 0
    for s in sentences:
        st = str(s["text"])
        for phrase, sev in [(v, "high") for v in VAGUE_HIGH] + [(v, "medium") for v in VAGUE_MEDIUM]:
            for m in re.finditer(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", st, re.IGNORECASE):
                rest = st[:m.start()] + st[m.end():]
                if phrase == "best" and re.match(r"\s+practices?", st[m.end():], re.I):
                    continue
                if re.search(r"\d", rest):
                    continue
                vague += 1
                points["vague-claim"] += 5 if sev == "high" else 3
                _finding(findings, s["line"], "vague-claim", sev, m.group(0),
                         "Back it with a sourced number or name, or describe what it does instead.")
    details["vague-claim"] = f"{vague} unsupported superlative(s)"

    # 7. customer focus
    you = sum(1 for w in all_words if w.lower() in YOU_WORDS)
    we = sum(1 for w in all_words if w.lower() in WE_WORDS and w != "US")
    if you + we >= 6 and we > you:
        points["customer-focus"] = 6
        _finding(findings, None, "customer-focus", "medium", f"we {we} : you {you}",
                 "Rewrite we-sentences around the reader: \"You get...\" instead of \"We offer...\".")
    details["customer-focus"] = f"you {you} : we {we}"

    # 8. triads ("fast, simple, and secure" / "Fast. Simple. Secure.")
    triads = 0
    triad_allowed = max(1, n_words // 120)
    for s in sentences:
        m = TRIAD_RE.search(str(s["text"]))
        if m:
            triads += 1
            sev = "medium" if triads > triad_allowed else "low"
            _finding(findings, s["line"], "triad", sev, m.group(0),
                     "Rule-of-three lists read as machine-made when repeated. Keep the strongest item or use two.")
    for p in paras:
        ps = split_sentences(p)
        for i in range(len(ps) - 2):
            trio = ps[i:i + 3]
            if all(len(t["words"]) <= 2 and str(t["text"]).endswith(".") for t in trio):  # type: ignore[arg-type]
                triads += 1
                _finding(findings, trio[0]["line"], "triad", "medium",
                         " ".join(str(t["text"]) for t in trio),
                         "Three one-word sentences is a template. Say one concrete thing instead.")
    points["triad"] = max(0, triads - triad_allowed) * 3
    details["triad"] = f"{triads} triad(s), {triad_allowed} allowed"

    deductions = []
    for check, cap in CAPS.items():
        pts = min(cap, round(points[check]))
        if pts > 0:
            deductions.append({"check": check, "points": pts, "detail": details.get(check, "")})
    score = max(0, 100 - sum(int(d["points"]) for d in deductions))
    counts = {sev: sum(1 for f in findings if f["severity"] == sev) for sev in SEVERITIES}
    findings.sort(key=lambda f: (f["line"] is None, f["line"] or 0, SEVERITIES.index(str(f["severity"]))))

    if n_words == 0:
        score, verdict = 0, "no copy found: nothing to score"
    elif score >= TARGET_SCORE and counts["high"] == 0:
        verdict = "ready: reads human; give it a final read-aloud"
    elif score >= 60:
        verdict = "needs a pass: fix the flagged lines"
    else:
        verdict = "rewrite: start from the reader's problem and cut the tells"

    return {
        "score": score,
        "target": TARGET_SCORE,
        "passed": n_words > 0 and score >= TARGET_SCORE and counts["high"] == 0,
        "verdict": verdict,
        "mode": mode,
        "counts": counts,
        "stats": {
            "words": n_words,
            "sentences": n_sent,
            "avg_sentence_words": avg,
            "sentence_length_stdev": stdev,
            "long_sentences": long_count,
            "fk_grade": grade,
            "max_grade": max_grade,
            "passive_sentences": passive,
            "ai_tells": tell_counts["ai-tell"],
            "filler_hedges": tell_counts["filler-hedge"],
            "exclamations": excl,
            "emoji": emoji,
            "em_dashes": dashes,
            "vague_claims": vague,
            "you": you,
            "we": we,
            "triads": triads,
        },
        "deductions": deductions,
        "findings": findings,
    }


# ------------------------------------------------------------------ output

def md_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(lines)


def to_markdown(result: Dict[str, object], source: str, limit: int = 50) -> str:
    st = result["stats"]  # type: ignore[assignment]
    c = result["counts"]  # type: ignore[assignment]
    out = [f"# Copy check: {source}", "",
           f"**Score: {result['score']}/100** (pass = {result['target']}+ and no high flags) - {result['verdict']}",
           f"Flags: {c['high']} high, {c['medium']} medium, {c['low']} low", ""]
    out += ["## Summary", "", md_table(("Metric", "Value"), [
        ("Words / sentences", f"{st['words']} / {st['sentences']}"),
        ("Avg sentence length (spread)", f"{st['avg_sentence_words']} words (stdev {st['sentence_length_stdev']})"),
        ("Reading grade (Flesch-Kincaid)", f"{st['fk_grade']} (target <= {st['max_grade']:g})"),
        ("AI tells / filler & hedges", f"{st['ai_tells']} / {st['filler_hedges']}"),
        ("Passive sentences", st["passive_sentences"]),
        ("Long sentences (>30 words)", st["long_sentences"]),
        ("Vague superlatives", st["vague_claims"]),
        ("You : we", f"{st['you']} : {st['we']}"),
        ("Exclamations / emoji / em-dashes", f"{st['exclamations']} / {st['emoji']} / {st['em_dashes']}"),
        ("Triads", st["triads"]),
    ]), ""]
    deds = result["deductions"]
    if deds:
        out += ["## Deductions", "", md_table(("Check", "Points", "Detail"),
                                              [(d["check"], f"-{d['points']}", d["detail"]) for d in deds]), ""]  # type: ignore[union-attr]
    findings = result["findings"]
    if findings:
        shown = findings[:limit]  # type: ignore[index]
        out += ["## Findings", "", md_table(("Line", "Severity", "Check", "Match", "Suggestion"), [
            (f["line"] if f["line"] is not None else "-", f["severity"],
             f["category"] if f["check"] in ("ai-tell", "filler-hedge") else f["check"],
             f"`{f['match']}`", f["suggestion"]) for f in shown])]
        if len(findings) > limit:  # type: ignore[arg-type]
            out.append(f"\n... {len(findings) - limit} more (use --limit or --json)")  # type: ignore[arg-type]
    else:
        out.append("No findings. Read it aloud once more, then ship.")
    return "\n".join(out)


def _read_input(name: str) -> Tuple[str, str]:
    if name == "-":
        data = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read()
        text = data.decode("utf-8-sig", "replace") if isinstance(data, bytes) else data
        return text, "auto"
    path = Path(name)
    suffix = path.suffix.lower()
    fmt = "html" if suffix in (".html", ".htm") else "txt" if suffix == ".txt" else "md"
    return path.read_text(encoding="utf-8-sig", errors="replace"), fmt


def positive_int(value: str) -> int:
    """argparse type for --limit (rejects 0 and negatives)."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from None
    if n < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return n


def main(argv: Optional[Sequence[str]] = None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="file path(s) (.md, .txt, .html) or - for stdin")
    parser.add_argument("--format", choices=("auto", "md", "txt", "html"), default="auto",
                        help="override format detection (default: from extension)")
    parser.add_argument("--mode", choices=sorted(GRADE_LIMITS), default="marketing",
                        help="marketing (grade <= 9) or ui (grade <= 7)")
    parser.add_argument("--max-grade", type=float, help="override the reading-grade target")
    parser.add_argument("--min-score", type=int, help="exit 1 if any input scores below N")
    parser.add_argument("--fail-on-high", action="store_true", help="exit 1 on any high-severity flag")
    parser.add_argument("--limit", type=positive_int, default=50, help="max findings listed in Markdown output")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    results = []
    for name in args.inputs:
        try:
            text, fmt = _read_input(name)
        except OSError as exc:
            print(f"copy_check: cannot read {name}: {exc}", file=sys.stderr)
            return 2
        if args.format != "auto":
            fmt = args.format
        result = analyze(text, fmt=fmt, mode=args.mode, max_grade=args.max_grade)
        if not result["stats"]["words"]:  # type: ignore[index]
            print(f"copy_check: no copy found in {name}", file=sys.stderr)
            return 2
        result["source"] = "stdin" if name == "-" else name
        results.append(result)

    if args.json:
        payload: object = results[0] if len(results) == 1 else {"results": results}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("\n\n".join(to_markdown(r, str(r["source"]), args.limit) for r in results))

    failed = False
    if args.min_score is not None and any(int(r["score"]) < args.min_score for r in results):  # type: ignore[arg-type]
        failed = True
    if args.fail_on_high and any(r["counts"]["high"] for r in results):  # type: ignore[index]
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
