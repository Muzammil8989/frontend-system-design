#!/usr/bin/env python3
"""Lint git commit messages against Conventional Commits and good-history rules (0-100).

Checks the header format (type(scope)!: subject), known types (data/commit-types.csv),
header length, imperative mood, trailing period, vague or WIP subjects, the blank
line before the body, body line length and BREAKING CHANGE footers. With --range it
checks every commit in a git range and can suggest the next semantic version.

Examples:
  python3 commit_check.py "feat(cli): add --companions all"
  python3 commit_check.py --file .git/COMMIT_EDITMSG --json
  git log -1 --format=%B | python3 commit_check.py -
  python3 commit_check.py --range origin/main..HEAD
  python3 commit_check.py --range v1.2.0..HEAD --suggest-bump

Standard library only (Python 3.9+). Exit code 0 when every message passes,
1 when one fails (a high-severity issue or a score under --min-score),
2 on bad input (empty message, unreadable file, git error).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence

SKILL_DIR = Path(__file__).resolve().parent.parent
TYPES_CSV = SKILL_DIR / "data" / "commit-types.csv"

DEFAULT_MIN_SCORE = 80
HEADER_SOFT_LIMIT = 72
HEADER_HARD_LIMIT = 100
BODY_LINE_LIMIT = 100

POINTS = {"high": 40, "medium": 12, "low": 4}
BUMP_ORDER = {"none": 0, "patch": 1, "minor": 2, "major": 3}

HEADER_RE = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()\r\n]*)\))?(?P<bang>!)?(?P<colon>:)(?P<space> ?)(?P<subject>.*)$")
BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]CHANGE: \S")
BREAKING_LOOSE_RE = re.compile(r"^breaking[ -_]?changes?\s*:", re.IGNORECASE)
GIT_GENERATED_RE = re.compile(r"^(Merge (branch|pull request|remote-tracking branch|tag) |Merge [0-9a-f]{7,} into |Revert \")")
AUTOSQUASH_RE = re.compile(r"^(fixup|squash|amend)! ")
WIP_RE = re.compile(r"^\s*(wip|work in progress|do not merge|dnm|tmp|temp)\b", re.IGNORECASE)
SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")

# First words that are not imperative. Imperative: "add", "fix", "remove".
NON_IMPERATIVE = {
    "added", "adds", "adding", "fixed", "fixes", "fixing", "updated", "updates", "updating",
    "removed", "removes", "removing", "changed", "changes", "changing", "created", "creates",
    "creating", "implemented", "implements", "implementing", "improved", "improves", "improving",
    "refactored", "refactors", "refactoring", "renamed", "renames", "renaming", "moved", "moves",
    "moving", "deleted", "deletes", "deleting", "bumped", "bumps", "bumping", "upgraded",
    "upgrades", "upgrading", "made", "makes", "making", "used", "uses", "using", "wrote",
    "writes", "writing", "tweaked", "tweaks", "tweaking", "cleaned", "cleans", "cleaning",
    "merged", "merges", "merging", "reverted", "reverts", "reverting", "introduced",
    "introduces", "introducing", "replaced", "replaces", "replacing", "corrected", "corrects",
    "correcting", "allowed", "allows", "allowing", "enabled", "enables", "enabling",
    "disabled", "disables", "disabling", "handled", "handles", "handling", "supported",
    "supports", "supporting", "ensured", "ensures", "ensuring", "prevented", "prevents",
    "preventing", "resolved", "resolves", "resolving", "optimized", "optimizes", "optimizing",
    "documented", "documents", "documenting", "tested", "tests", "testing", "started", "starts",
    "starting", "finished", "finishes", "finishing", "trying", "tried", "tries",
}
# Words ending in -ed / -ing that are fine as an imperative first word.
ED_ING_OK = {"embed", "feed", "need", "seed", "speed", "shed", "proceed", "exceed", "succeed",
             "breed", "bring", "string", "ping", "ring", "sing", "swing", "wing", "spring", "log"}
VAGUE_SUBJECTS = {
    "update", "updates", "fix", "fixes", "fix bug", "fix bugs", "bug fix", "bugfix", "changes",
    "change", "misc", "stuff", "minor", "minor fix", "minor fixes", "minor changes", "small fix",
    "small fixes", "cleanup", "clean up", "refactor", "wip", "tweaks", "tweak", "improvements",
    "more", "temp", "test", "testing", "asdf", "initial", "update code", "fix stuff",
    "address review comments", "address feedback", "pr feedback", "review fixes",
}


# --------------------------------------------------------------------------- data


@lru_cache(maxsize=1)
def load_types() -> Dict[str, Dict[str, str]]:
    """type → row from data/commit-types.csv (the `breaking` pseudo-type is excluded)."""
    with TYPES_CSV.open(encoding="utf-8", newline="") as fh:
        rows = {row["type"].strip(): row for row in csv.DictReader(fh)}
    rows.pop("breaking", None)
    return rows


# --------------------------------------------------------------------------- linting


def clean_message(raw: str) -> str:
    """Drop git comment lines and everything below the scissors line; trim trailing blanks."""
    lines: List[str] = []
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith("# ------------------------ >8 ------------------------"):
            break
        if line.startswith("#"):
            continue
        lines.append(line.rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _issue(issues: List[dict], check: str, severity: str, message: str, suggestion: str = "", line: int = 1) -> None:
    issues.append({"check": check, "severity": severity, "message": message, "suggestion": suggestion, "line": line})


def lint_message(raw: str, min_score: int = DEFAULT_MIN_SCORE, extra_types: Sequence[str] = (), allow_wip: bool = False) -> dict:
    """Lint one commit message. Returns score, pass/fail, parsed header fields, bump and issues."""
    message = clean_message(raw)
    issues: List[dict] = []
    result = {"header": "", "type": None, "scope": None, "breaking": False, "bump": "none",
              "skipped": None, "score": 0, "pass": False, "issues": issues}
    if not message:
        _issue(issues, "empty", "high", "The commit message is empty.", "Write a header like `fix(scope): describe the change`.")
        return result

    lines = message.split("\n")
    header = lines[0].strip()
    result["header"] = header

    if GIT_GENERATED_RE.match(header):
        result.update(skipped="git-generated merge or revert message", score=100, **{"pass": True})
        return result
    if AUTOSQUASH_RE.match(header):
        _issue(issues, "autosquash", "low" if allow_wip else "high", "This is a fixup!/squash! commit.",
               "Fold it in before merging: `git rebase -i --autosquash <base>`.")
    if WIP_RE.match(header):
        _issue(issues, "wip", "low" if allow_wip else "high", "The header marks this as work in progress.",
               "Finish the change, or squash it into a real commit before merging.")

    known_types = set(load_types()) | {t.strip().lower() for t in extra_types if t.strip()}
    m = HEADER_RE.match(re.sub(r"^(fixup|squash|amend)! ", "", header))
    if not m:
        _issue(issues, "format", "high", "The header doesn't follow `type(scope): subject`.",
               "Example: `feat(auth): add passkey sign-in`. Types: " + ", ".join(sorted(known_types)) + ".")
        subject = header
    else:
        ctype, scope, subject = m.group("type"), m.group("scope"), m.group("subject")
        result.update(type=ctype.lower(), scope=scope, breaking=bool(m.group("bang")))
        if ctype != ctype.lower():
            _issue(issues, "type-case", "medium", f"Type `{ctype}` should be lower case.", f"Use `{ctype.lower()}`.")
        if ctype.lower() not in known_types:
            _issue(issues, "type-unknown", "medium", f"`{ctype}` is not a known commit type.",
                   "Use one of: " + ", ".join(sorted(known_types)) + ", or pass --types to allow the repo's own.")
        if scope is not None and not scope.strip():
            _issue(issues, "scope-empty", "medium", "The scope parentheses are empty.", "Remove `()` or name the area, e.g. `(cli)`.")
        elif scope and (scope != scope.strip() or " " in scope.strip()):
            _issue(issues, "scope-format", "low", f"Scope `{scope}` has spaces.", "Use one short word or kebab-case, e.g. `(auth-api)`.")
        if not m.group("space"):
            _issue(issues, "colon-space", "medium", "There is no space after the colon.", "Write `type: subject`.")
        elif m.group("space") and subject.startswith(" "):
            _issue(issues, "colon-space", "low", "There is more than one space after the colon.", "Use exactly one space.")
        subject = subject.strip()

    if m and not subject:
        _issue(issues, "subject-empty", "high", "The subject is empty.", "Say what the commit does, in the imperative: `add …`, `fix …`.")
    elif subject:
        first = re.split(r"[\s:,(]", subject, maxsplit=1)[0]
        word = first.lower().strip("`'\"")
        if word in NON_IMPERATIVE or (re.fullmatch(r"[a-z]{4,}(ed|ing)", word) and word not in ED_ING_OK):
            _issue(issues, "imperative", "medium", f"Start with an imperative verb, not `{first}`.",
                   "Read it as \"If applied, this commit will …\": `add`, `fix`, `remove`, `update`.")
        if subject.endswith("."):
            _issue(issues, "trailing-period", "low", "The subject ends with a period.", "Drop the period.")
        if subject.lower().rstrip(".!") in VAGUE_SUBJECTS:
            _issue(issues, "vague", "medium", f"`{subject}` doesn't say what changed.",
                   "Name the behaviour: `fix(cart): keep items after sign-in`, not `fix bug`.")
        if subject[:1].isupper() and not re.match(r"^[A-Z0-9_]{2,}\b", subject) and m:
            _issue(issues, "subject-case", "low", "Most Conventional Commit setups expect a lower-case subject.",
                   "Lower-case the first letter unless it's a name or acronym, or the repo's log does otherwise.")

    if len(header) > HEADER_HARD_LIMIT:
        _issue(issues, "header-length", "high", f"The header is {len(header)} characters (limit {HEADER_SOFT_LIMIT}).",
               "Shorten it and move detail into the body.")
    elif len(header) > HEADER_SOFT_LIMIT:
        _issue(issues, "header-length", "medium", f"The header is {len(header)} characters (aim for {HEADER_SOFT_LIMIT} or fewer).",
               "Shorten it and move detail into the body.")

    if len(lines) > 1 and lines[1].strip():
        _issue(issues, "blank-line", "medium", "There is no blank line between the header and the body.",
               "Leave line 2 empty; tools read line 1 as the title.", line=2)

    in_code = False
    long_lines = 0
    for n, line in enumerate(lines[1:], start=2):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if BREAKING_FOOTER_RE.match(line):
            result["breaking"] = True
        elif BREAKING_LOOSE_RE.match(line.strip()):
            _issue(issues, "breaking-footer", "medium", f"`{line.strip()[:30]}` isn't recognised by release tools.",
                   "Write the footer exactly as `BREAKING CHANGE: <what breaks and how to migrate>`.", line=n)
        if (not in_code and len(line) > BODY_LINE_LIMIT and not line.startswith("    ")
                and not re.search(r"https?://\S{40,}", line)):
            long_lines += 1
            if long_lines <= 3:
                _issue(issues, "body-length", "low", f"Line {n} is {len(line)} characters.",
                       f"Wrap the body at {HEADER_SOFT_LIMIT}-{BODY_LINE_LIMIT} characters.", line=n)

    if m and m.group("bang") and len([x for x in lines[1:] if x.strip()]) == 0:
        _issue(issues, "breaking-explain", "low", "Breaking change with no body.",
               "Add a `BREAKING CHANGE:` footer that says what breaks and how to migrate.")

    result["bump"] = bump_for(result["type"], result["breaking"])
    result["score"] = score(issues)
    result["pass"] = result["score"] >= min_score and not any(i["severity"] == "high" for i in issues)
    return result


def score(issues: Sequence[dict]) -> int:
    return max(0, 100 - sum(POINTS[i["severity"]] for i in issues))


def bump_for(ctype: Optional[str], breaking: bool) -> str:
    if breaking:
        return "major"
    if not ctype:
        return "none"
    row = load_types().get(ctype)
    return (row["semver_bump"].strip() or "none") if row else "none"


def next_version(current: str, bump: str) -> Optional[str]:
    """Next semver after `current` for `bump`. Before 1.0.0 a breaking change bumps the minor."""
    m = SEMVER_RE.match(current.strip())
    if not m:
        return None
    major, minor, patch = (int(x) for x in m.groups())
    prefix = "v" if current.strip().startswith("v") else ""
    if bump == "major" and major == 0:
        bump = "minor"
    if bump == "major":
        return f"{prefix}{major + 1}.0.0"
    if bump == "minor":
        return f"{prefix}{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{prefix}{major}.{minor}.{patch + 1}"
    return f"{prefix}{major}.{minor}.{patch}"


# --------------------------------------------------------------------------- git


def git_log(rev_range: str, cwd: Optional[str] = None) -> List[Dict[str, str]]:
    """Commits in `rev_range` (oldest first) as {sha, message}. Raises ValueError on git errors."""
    if rev_range.startswith("-"):
        raise ValueError(f"not a revision range: {rev_range}")
    try:
        proc = subprocess.run(
            ["git", "log", "--reverse", "--format=%H%x1f%B%x1e", rev_range, "--"],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError("git is not installed or not on PATH") from exc
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or f"git log failed for {rev_range}")
    commits = []
    for record in proc.stdout.split("\x1e"):
        record = record.strip("\n")
        if "\x1f" in record:
            sha, body = record.split("\x1f", 1)
            commits.append({"sha": sha.strip(), "message": body})
    return commits


def range_start(rev_range: str) -> Optional[str]:
    left = rev_range.split("..", 1)[0] if ".." in rev_range else ""
    return left if SEMVER_RE.match(left) else None


# --------------------------------------------------------------------------- output


def ensure_utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def format_result(res: dict, label: str = "") -> str:
    status = "PASS" if res["pass"] else "FAIL"
    head = f"{label}{res['score']}/100 {status}  {res['header'] or '(empty)'}"
    if res["skipped"]:
        return f"{label}skip  {res['header']}  ({res['skipped']})"
    out = [head]
    for i in res["issues"]:
        out.append(f"    [{i['severity']}] {i['message']}" + (f"\n           → {i['suggestion']}" if i["suggestion"] else ""))
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group()
    src.add_argument("message", nargs="?", help="the commit message, or - to read stdin")
    src.add_argument("--file", help="read the message from a file (e.g. .git/COMMIT_EDITMSG)")
    src.add_argument("--range", dest="rev_range", help="check every commit in a git range, e.g. origin/main..HEAD")
    parser.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE, help=f"fail below this score (default {DEFAULT_MIN_SCORE})")
    parser.add_argument("--types", default="", help="extra allowed types, comma-separated (the repo's own convention)")
    parser.add_argument("--suggest-bump", action="store_true", help="with --range: print the semver bump the commits imply")
    parser.add_argument("--current", help="current version for --suggest-bump (default: the range start if it is a tag like v1.2.0)")
    parser.add_argument("--repo", help="run git in this directory (default: current directory)")
    parser.add_argument("--json", action="store_true", help="compact machine-readable output")
    parser.add_argument("--verbose", action="store_true", help="with --range: also list clean and skipped commits")
    parser.add_argument("--allow-wip", action="store_true", help="treat WIP and fixup!/squash! commits as low severity (for a local commit-msg hook)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    ensure_utf8_stdout()
    args = build_parser().parse_args(argv)
    extra = args.types.split(",") if args.types else []

    if args.rev_range:
        try:
            commits = git_log(args.rev_range, cwd=args.repo)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        results = []
        for cm in commits:
            res = lint_message(cm["message"], args.min_score, extra, args.allow_wip)
            res["sha"] = cm["sha"]
            results.append(res)
        checked = [r for r in results if not r["skipped"]]
        bump = max((r["bump"] for r in checked), key=BUMP_ORDER.__getitem__, default="none")
        current = args.current or range_start(args.rev_range)
        report = {
            "range": args.rev_range, "commits": results, "checked": len(checked),
            "failed": sum(1 for r in checked if not r["pass"]),
            "pass": all(r["pass"] for r in checked),
            "bump": bump, "current": current,
            "next_version": next_version(current, bump) if current else None,
        }
        if args.json:
            print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
        else:
            if not results:
                print(f"No commits in {args.rev_range}.")
            # Only commits with something to fix unless --verbose, so long branches stay short.
            shown = results if args.verbose else [r for r in checked if r["issues"]]
            for r in shown:
                print(format_result(r, label=f"{r['sha'][:8]}  "))
            hidden = len(results) - len(shown)
            print(f"{report['checked']} commit(s) checked, {report['failed']} failed."
                  + (f" {hidden} clean or skipped not shown (--verbose lists them)." if hidden else ""))
            if args.suggest_bump:
                drivers = [r for r in checked if r["bump"] == bump and bump != "none"]
                print(f"Suggested bump: {bump}" + (f" ({current} → {report['next_version']})" if report["next_version"] else ""))
                for r in drivers[:5]:
                    print(f"  because: {r['sha'][:8]} {r['header']}")
        return 0 if report["pass"] else 1

    if args.suggest_bump:
        print("error: --suggest-bump needs --range", file=sys.stderr)
        return 2
    if args.file:
        try:
            raw = Path(args.file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
    elif args.message in (None, "-"):
        if args.message is None and sys.stdin.isatty():
            build_parser().print_usage(sys.stderr)
            print("error: give a message, --file, --range, or pipe a message on stdin", file=sys.stderr)
            return 2
        raw = sys.stdin.read()
    else:
        raw = args.message

    if not clean_message(raw):
        print("error: the commit message is empty", file=sys.stderr)
        return 2
    res = lint_message(raw, args.min_score, extra, args.allow_wip)
    print(json.dumps(res, ensure_ascii=False, separators=(",", ":")) if args.json else format_result(res))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
