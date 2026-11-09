#!/usr/bin/env python3
"""Static scan of a frontend codebase for accessibility, security and performance smells.

Produces *facts* (file:line + rule) for the auditor to judge — not a score.
Heuristic and regex-based: expect some false positives; always read the code.

Examples:
  python3 audit_scan.py ./src
  python3 audit_scan.py . --format json > scan.json
  python3 audit_scan.py . --format md --max 200
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from fsd_core import ensure_utf8_stdout, md_table, positive_int

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt", ".svelte-kit", ".output", "out",
    "coverage", ".turbo", ".vercel", ".cache", "vendor", "storybook-static", "__pycache__",
    "Pods", ".dart_tool", ".gradle", "DerivedData", "obj", "bin", "target", ".expo", "android/app/build",
}
CODE_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".html", ".htm"}
STYLE_EXT = {".css", ".scss", ".sass", ".less"}
DART, SWIFT, KOTLIN, XAML = {".dart"}, {".swift"}, {".kt"}, {".xaml"}
NATIVE_EXT = DART | SWIFT | KOTLIN | XAML | {".cs"}
ALL_EXT = CODE_EXT | STYLE_EXT | NATIVE_EXT
MAX_FILE_BYTES = 1_000_000
MAX_LINE_CHARS = 2000  # longer lines (minified/generated code) are not regex-scanned
MINIFIED_NAME = re.compile(r"\.(min|bundle|chunk)\.|^chunk-", re.IGNORECASE)
TEST_PATH = re.compile(r"\.test\.|\.spec\.|__tests__|(^|/)tests?/")
BLOCK_COMMENT_EXT = CODE_EXT | STYLE_EXT | DART | SWIFT | KOTLIN | {".cs"}  # languages with /* */ comments
# quoted token-like literals in security findings are masked before they reach the report
SECRET_LITERAL = re.compile(r"""(['"`])([A-Za-z0-9_\-+/=.]{20,})\1""")


@dataclass
class Finding:
    rule: str
    category: str
    severity: str  # high | medium | low
    file: str
    line: int
    message: str
    snippet: str


@dataclass
class Rule:
    id: str
    category: str
    severity: str
    pattern: "re.Pattern[str]"
    message: str
    exts: frozenset


def R(id, category, severity, regex, message, exts=CODE_EXT, flags=re.IGNORECASE):
    return Rule(id, category, severity, re.compile(regex, flags), message, frozenset(exts))


RULES: List[Rule] = [
    # --- security
    R("dangerous-html", "security", "high", r"dangerouslySetInnerHTML|v-html\s*=|\{@html\s|\.innerHTML\s*=(?!=)|\.outerHTML\s*=(?!=)|insertAdjacentHTML\(",
      "HTML injection sink — make sure input is trusted or sanitized (DOMPurify)"),
    R("eval", "security", "high", r"\beval\s*\(|new\s+Function\s*\(|setTimeout\s*\(\s*['\"`]",
      "Dynamic code execution — avoid eval/new Function/string timers"),
    R("token-in-web-storage", "security", "high", r"(localStorage|sessionStorage)\s*\.\s*setItem\s*\(\s*['\"`][^'\"`]{0,200}(token|jwt|auth|session|secret|password)",
      "Auth token in Web Storage is readable by any XSS — use httpOnly Secure SameSite cookies"),
    R("hardcoded-secret", "security", "high", r"(api[_-]?key|secret|private[_-]?key|access[_-]?token)\s*[:=]\s*['\"`][A-Za-z0-9_\-]{20,500}['\"`]",
      "Possible hard-coded secret in client code (anything shipped in an app binary is extractable)", exts=CODE_EXT | NATIVE_EXT),
    R("target-blank", "security", "low", r"target\s*=\s*['\"{]_blank(?![^<>]{0,500}rel\s*=)",
      "target=_blank without rel — add rel=\"noopener noreferrer\" (modern browsers imply noopener, but be explicit for older ones)"),
    R("javascript-url", "security", "medium", r"href\s*=\s*['\"`]javascript:",
      "javascript: URL — use a button with a handler"),
    # --- accessibility
    R("img-no-alt", "a11y", "medium", r"<img\b(?![^<>]{0,500}\balt\s*=)[^<>]{0,500}>",
      "<img> without alt — add meaningful alt, or alt=\"\" if decorative"),
    R("click-on-non-interactive", "a11y", "medium", r"<(div|span|li|td|p)\b[^<>]{0,500}\s(onClick|@click|on:click|v-on:click)\s*=",
      "Click handler on non-interactive element — use <button>/<a> (keyboard + role for free)"),
    R("positive-tabindex", "a11y", "medium", r"tabIndex\s*=\s*\{?\s*['\"]?[1-9]|tabindex\s*=\s*['\"][1-9]",
      "Positive tabindex breaks natural focus order"),
    R("outline-none", "a11y", "medium", r"outline\s*:\s*(none|0)\b|\boutline-none\b",
      "Focus outline removed — ensure a visible :focus-visible replacement", exts=CODE_EXT | STYLE_EXT),
    R("autofocus", "a11y", "low", r"\bautoFocus\b|\bautofocus\b",
      "autofocus can disorient screen-reader and mobile users — use deliberately"),
    R("aria-hidden-focusable", "a11y", "high", r"aria-hidden\s*=\s*['\"{]?true[^<>]{0,500}(href=|<button|tabindex=['\"]?0)",
      "aria-hidden on focusable content hides it from AT but not from keyboard"),
    R("placeholder-as-label", "a11y", "low", r"<input\b(?![^<>]{0,500}(aria-label|aria-labelledby|id\s*=))[^<>]{0,500}placeholder\s*=",
      "Input with placeholder but no label/id/aria-label — placeholders are not labels"),
    R("user-scalable-no", "a11y", "high", r"user-scalable\s*=\s*(no|0)|maximum-scale\s*=\s*1(\.0)?\b",
      "Viewport blocks zoom — remove user-scalable=no / maximum-scale=1"),
    # --- performance
    R("heavy-import-moment", "performance", "medium", r"from\s+['\"]moment['\"]|require\(\s*['\"]moment['\"]\s*\)",
      "moment is large and legacy — use Intl, date-fns or Temporal"),
    R("full-lodash-import", "performance", "medium", r"import\s+(\*\s+as\s+)?_\s+from\s+['\"]lodash['\"]|require\(\s*['\"]lodash['\"]\s*\)",
      "Whole-lodash import — import per function or use lodash-es"),
    R("sync-xhr-or-docwrite", "performance", "high", r"document\.write\s*\(|\.open\([^)]{0,300},\s*false\s*\)",
      "document.write / synchronous XHR block the main thread"),
    R("unload-listener", "performance", "medium", r"addEventListener\(\s*['\"]unload['\"]|onunload\s*=",
      "unload handler blocks bfcache — use pagehide/visibilitychange"),
    R("img-no-dimensions", "performance", "low", r"<img\b(?![^<>]{0,500}(width|height|fill|aspect))[^<>]{0,500}>",
      "<img> without width/height — risk of layout shift (CLS)"),
    # --- mobile / native (heuristic, line-based)
    R("rn-asyncstorage-token", "security", "high", r"AsyncStorage\s*\.\s*setItem\s*\(\s*['\"`][^'\"`]{0,200}(token|jwt|auth|session|password)",
      "Token in AsyncStorage (unencrypted) — use expo-secure-store / Keychain / Keystore"),
    R("android-prefs-token", "security", "high", r"(SharedPreferences|putString)\b(?:(?!SharedPreferences|putString).){0,300}?(token|jwt|password|secret)",
      "Secret in SharedPreferences — use Keystore-backed encryption", exts=KOTLIN),
    R("ios-userdefaults-token", "security", "high", r"UserDefaults(?:(?!UserDefaults).){0,300}?(token|jwt|password|secret)",
      "Secret in UserDefaults — store it in the Keychain", exts=SWIFT),
    R("flutter-prefs-token", "security", "high", r"SharedPreferences(?:(?!SharedPreferences).){0,300}?(token|jwt|password|secret)|setString\(\s*['\"][^'\"]{0,200}(token|jwt|password)",
      "Secret in shared_preferences — use flutter_secure_storage", exts=DART),
    R("flutter-image-no-semantics", "a11y", "low", r"Image\.(asset|network|file)\((?![^)]{0,500}semanticLabel)",
      "Image without semanticLabel — add one, or wrap in ExcludeSemantics if decorative", exts=DART),
    R("swift-tap-gesture", "a11y", "medium", r"\.onTapGesture\s*\{",
      "onTapGesture on a view — prefer Button (VoiceOver traits, focus, hit area) or add .accessibilityAddTraits(.isButton)", exts=SWIFT),
    R("compose-null-description", "a11y", "low", r"contentDescription\s*=\s*null",
      "contentDescription = null — fine only for decorative images/icons", exts=KOTLIN),
    R("kotlin-runblocking", "performance", "medium", r"\brunBlocking\s*[({]",
      "runBlocking can freeze the UI thread (ANR risk) — use coroutines with lifecycle scopes", exts=KOTLIN),
    R("maui-image-no-description", "a11y", "medium", r"<(Image|ImageButton)\b(?![^<>]{0,500}SemanticProperties\.Description)",
      "Image/ImageButton without SemanticProperties.Description", exts=XAML),
    R("debug-print", "quality", "low", r"^\s*(print|debugPrint|NSLog|Log\.[dv])\s*\(", "Debug logging left in code", exts=DART | SWIFT | KOTLIN),
    R("console-log", "quality", "low", r"\bconsole\.log\s*\(", "console.log left in code"),
    R("ts-any", "quality", "low", r":\s*any\b|as\s+any\b", "TypeScript `any` weakens type safety", exts={".ts", ".tsx"}),
]

HEAVY_DEPS = {
    "moment": "Large, legacy date library — prefer Intl / date-fns / Temporal",
    "jquery": "Usually unnecessary in modern frameworks",
    "lodash": "Prefer per-function imports or lodash-es",
    "core-js": "Check polyfills target only browsers you support",
    "axios": "fetch is built in; keep axios only if you need its features",
    "@mui/icons-material": "Import icons per path to avoid huge bundles",
    "chart.js": "Fine — but lazy-load chart routes",
    "three": "Large — lazy-load 3D scenes",
}


def iter_files(root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() not in ALL_EXT or p.is_symlink():
                continue
            if MINIFIED_NAME.search(name) or name.endswith((".d.ts", ".g.dart", ".freezed.dart", ".Designer.cs")):
                continue
            yield p


def read_capped(path: Path) -> Optional[str]:
    """Text of a regular (non-symlink) file of at most MAX_FILE_BYTES, else None. A UTF-8 BOM is dropped."""
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE_BYTES:
            return None
        with open(path, "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None
    if len(data) > MAX_FILE_BYTES:
        return None
    return data.decode("utf-8-sig", errors="replace")


def mask_secrets(text: str) -> str:
    """Keep the first 4 characters of long quoted token-like literals: 'sk_live_abcdef…' -> 'sk_l****'."""
    return SECRET_LITERAL.sub(lambda m: f"{m.group(1)}{m.group(2)[:4]}****{m.group(1)}", text)


def scan_file(path: Path, root: Path) -> List[Finding]:
    text = read_capped(path)
    if text is None:
        return []
    rel = path.relative_to(root).as_posix()
    ext = path.suffix.lower()
    # split on \n only (after normalizing CR/CRLF) so form feeds or U+2028 don't shift line numbers
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(text) / len(lines) > MAX_LINE_CHARS:
        return []  # minified / generated bundle
    is_test = bool(TEST_PATH.search(rel))
    block_comments = ext in BLOCK_COMMENT_EXT
    in_block = False
    findings: List[Finding] = []
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if in_block:  # inside /* ... */
            in_block = "*/" not in stripped
            continue
        if stripped.startswith("//"):
            continue
        if block_comments and stripped.startswith("/*"):
            in_block = "*/" not in stripped[2:]
            continue
        # " * text" / " */" doc-comment continuation; not in CSS, where `* {` and `*:focus` are selectors
        if block_comments and ext not in STYLE_EXT and re.match(r"\*(\s|/|$)", stripped):
            continue
        if len(line) > MAX_LINE_CHARS:
            continue
        for rule in RULES:
            if ext not in rule.exts:
                continue
            if is_test and rule.category in ("quality", "performance"):
                continue
            if rule.pattern.search(line):
                snippet = mask_secrets(stripped) if rule.category == "security" else stripped
                findings.append(Finding(rule.id, rule.category, rule.severity, rel, lineno, rule.message, snippet[:160]))
    if ext in {".html", ".htm"} and "<html" in text.lower() and not re.search(r"<html\b[^>]{0,1000}\blang\s*=", text, re.I):
        findings.append(Finding("html-lang", "a11y", "high", rel, 1, "<html> without lang attribute", "<html>"))
    return findings


def _dict(value) -> Dict:
    return value if isinstance(value, dict) else {}


def scan_package(root: Path) -> Dict:
    pkg = root / "package.json"
    if not pkg.exists():
        return {}
    text = read_capped(pkg)
    try:
        data = json.loads(text) if text is not None else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return {"error": "package.json could not be parsed"}
    prod = _dict(data.get("dependencies"))
    dev = _dict(data.get("devDependencies"))
    deps = {**prod, **dev}
    frameworks = [d for d in ("next", "nuxt", "astro", "@sveltejs/kit", "svelte", "vue", "react", "@angular/core", "solid-js", "preact", "lit") if d in deps]
    flags = {k: v for k, v in HEAVY_DEPS.items() if k in prod}
    tooling = {
        "typescript": "typescript" in deps,
        "eslint": any(d.startswith("eslint") for d in deps),
        "a11y_lint": any("jsx-a11y" in d or "vuejs-accessibility" in d for d in deps),
        "unit_tests": any(d in deps for d in ("vitest", "jest")),
        "testing_library": any(d.startswith("@testing-library/") for d in deps),
        "e2e": any(d in deps for d in ("@playwright/test", "cypress")),
        "axe": any("axe" in d for d in deps),
        "error_tracking": any(d.startswith("@sentry/") or d in ("@datadog/browser-rum", "@bugsnag/js") for d in deps),
        "web_vitals_rum": "web-vitals" in deps,
        "bundle_budget": any(d in deps for d in ("size-limit", "@size-limit/preset-app", "bundlesize", "@lhci/cli")),
    }
    return {
        "name": data.get("name"),
        "frameworks": frameworks,
        "dependency_count": {"prod": len(prod), "dev": len(dev)},
        "heavy_dependencies": flags,
        "tooling": tooling,
        "missing_tooling": [k for k, v in tooling.items() if not v],
    }


def run(root: Path, max_findings: int) -> Dict:
    findings: List[Finding] = []
    files = 0
    for f in iter_files(root):
        files += 1
        findings.extend(scan_file(f, root))
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda x: (order[x.severity], x.category, x.file, x.line))
    by_rule: Dict[str, int] = {}
    for f in findings:
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
    summary = {
        "files_scanned": files,
        "findings": len(findings),
        "by_severity": {s: sum(1 for f in findings if f.severity == s) for s in order},
        "by_category": {c: sum(1 for f in findings if f.category == c) for c in sorted({f.category for f in findings})},
        "by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
    }
    return {"root": str(root), "summary": summary, "package": scan_package(root), "findings": [asdict(f) for f in findings[:max_findings]], "truncated": len(findings) > max_findings}


def to_markdown(report: Dict) -> str:
    s = report["summary"]
    out = [f"## Static scan — `{report['root']}`", "",
           f"Files scanned: **{s['files_scanned']}** · Findings: **{s['findings']}** "
           f"(high {s['by_severity']['high']}, medium {s['by_severity']['medium']}, low {s['by_severity']['low']})", ""]
    pkg = report["package"]
    if pkg:
        out += ["### package.json",
                f"- Frameworks: {', '.join(pkg.get('frameworks') or []) or '—'}",
                f"- Dependencies: {pkg.get('dependency_count', {}).get('prod', '?')} prod / {pkg.get('dependency_count', {}).get('dev', '?')} dev",
                f"- Missing tooling: {', '.join(pkg.get('missing_tooling') or []) or 'none'}"]
        for dep, why in (pkg.get("heavy_dependencies") or {}).items():
            out.append(f"- Heavy dependency `{dep}`: {why}")
        out.append("")
    if s["by_rule"]:
        out += ["### Findings by rule", md_table(["Rule", "Count"], s["by_rule"].items()), ""]
    if report["findings"]:
        out += ["### Findings (most severe first)",
                md_table(["Severity", "Category", "Location", "Issue"],
                         [(f["severity"], f["category"], f"`{f['file']}:{f['line']}`", f["message"]) for f in report["findings"]])]
    if report["truncated"]:
        out.append("\n_Output truncated — re-run with a higher --max or --format json._")
    out.append("\n> Heuristic scan: confirm each finding in context before reporting it.")
    return "\n".join(out)


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--max", type=positive_int, default=150, help="max findings to list (default 150)")
    args = parser.parse_args(argv)

    root = Path(args.path).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    report = run(root, args.max)
    print(json.dumps(report, indent=2) if args.format == "json" else to_markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
