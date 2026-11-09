#!/usr/bin/env python3
"""Validate a design-token file and print the tables the project docs need.

Reads a W3C Design Tokens (DTCG) JSON file, the format of
`references/templates/tokens.example.json`, and checks that:
  - every token has a $type (its own or inherited from a group) and a well-formed $value
  - every alias such as "{color.light.primary}" points at a real token (no cycles)
  - color pairs meet WCAG 2.2 contrast in every mode (a group that holds a `bg` token is a mode):
      text* on bg/surface*   >= 4.5:1        on-<x> on <x>   >= 4.5:1
      focus-ring on bg       >= 3:1          border on bg    >= 3:1 (warning only: needed when
                                                             the border is a control's only edge)

Prints Markdown (default) or JSON: the problems, a contrast table per mode and the type scale.
Exit code 1 when there are errors or failed contrast pairs, so it can run in CI.

Examples:
  python3 tokens_check.py docs/design-system/tokens.json
  python3 tokens_check.py docs/design-system/tokens.json --format json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fsd_core import contrast_ratio, ensure_utf8_stdout, md_table

TYPES = {"color", "dimension", "fontFamily", "fontWeight", "duration", "cubicBezier", "number",
         "shadow", "typography", "border", "transition", "gradient", "strokeStyle"}
ALIAS = re.compile(r"^\{([^{}]+)\}$")
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
DIMENSION = re.compile(r"^-?\d+(?:\.\d+)?(px|rem)$|^0$")
DURATION = re.compile(r"^\d+(?:\.\d+)?(ms|s)$")
TYPOGRAPHY_KEYS = ("fontFamily", "fontSize", "fontWeight", "lineHeight")
ROOT_PX = 16  # rem → px for the type-scale table


def collect(node: Dict[str, Any], path: Tuple[str, ...] = (), inherited: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Flattens groups into {"a.b.c": {"type", "value"}}; $type is inherited from the nearest group."""
    out: Dict[str, Dict[str, Any]] = {}
    group_type = node.get("$type", inherited)
    for key, child in node.items():
        if key.startswith("$") or not isinstance(child, dict):
            continue
        name = path + (key,)
        if "$value" in child:
            out[".".join(name)] = {"type": child.get("$type", group_type), "value": child["$value"]}
        else:
            out.update(collect(child, name, group_type))
    return out


def resolve(value: Any, tokens: Dict[str, Dict[str, Any]], seen: Tuple[str, ...] = ()) -> Any:
    """Replaces aliases (recursively inside composite values). Raises ValueError on a missing target or a cycle."""
    if isinstance(value, str):
        m = ALIAS.match(value)
        if not m:
            return value
        target = m.group(1)
        if target in seen:
            raise ValueError(f"alias cycle: {' → '.join(seen + (target,))}")
        if target not in tokens:
            raise ValueError(f"alias {value} points at no token")
        return resolve(tokens[target]["value"], tokens, seen + (target,))
    if isinstance(value, dict):
        return {k: resolve(v, tokens, seen) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, tokens, seen) for v in value]
    return value


def as_hex(value: Any) -> Optional[str]:
    """Hex string for a color value: "#rrggbb" or a DTCG color object with a "hex" field. None if not checkable."""
    if isinstance(value, dict):
        value = value.get("hex")
    if isinstance(value, str) and HEX.match(value):
        return value
    return None


def is_dimension(value: Any) -> bool:
    if isinstance(value, dict):
        return isinstance(value.get("value"), (int, float)) and value.get("unit") in ("px", "rem")
    return isinstance(value, str) and bool(DIMENSION.match(value))


def to_px(value: Any) -> Optional[float]:
    if isinstance(value, dict) and is_dimension(value):
        return float(value["value"]) * (ROOT_PX if value["unit"] == "rem" else 1)
    if isinstance(value, str) and is_dimension(value):
        if value == "0":
            return 0.0
        number = float(value[:-3] if value.endswith("rem") else value[:-2])
        return number * ROOT_PX if value.endswith("rem") else number
    return None


def validate(tokens: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Returns (resolved values, errors, warnings)."""
    resolved: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    for name, tok in tokens.items():
        ttype = tok["type"]
        if not ttype:
            errors.append(f"{name}: no $type (set it on the token or a parent group)")
            continue
        if ttype not in TYPES:
            errors.append(f"{name}: unknown $type \"{ttype}\"")
            continue
        try:
            value = resolve(tok["value"], tokens)
        except ValueError as exc:
            errors.append(f"{name}: {exc}")
            continue
        resolved[name] = value
        if ttype == "color" and as_hex(value) is None:
            warnings.append(f"{name}: color {json.dumps(value)} is not a hex value; contrast not checked")
        elif ttype == "color" and len(as_hex(value).lstrip("#")) == 8:
            warnings.append(f"{name}: color has an alpha channel; contrast depends on what is behind it")
        elif ttype == "dimension" and not is_dimension(value):
            errors.append(f"{name}: dimension {json.dumps(value)} should look like \"16px\" or \"1rem\"")
        elif ttype == "duration" and not (isinstance(value, str) and DURATION.match(value)) \
                and not (isinstance(value, dict) and value.get("unit") in ("ms", "s")):
            errors.append(f"{name}: duration {json.dumps(value)} should look like \"200ms\"")
        elif ttype == "typography":
            missing = [k for k in TYPOGRAPHY_KEYS if not isinstance(value, dict) or k not in value]
            if missing:
                errors.append(f"{name}: typography is missing {', '.join(missing)}")
    return resolved, errors, warnings


def contrast_pairs(tokens: Dict[str, Dict[str, Any]], resolved: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Checks the role pairs inside every color mode (a group with a `bg` token)."""
    colors = {n: as_hex(resolved[n]) for n, t in tokens.items() if t["type"] == "color" and n in resolved}
    modes = sorted({n.rsplit(".", 1)[0] if "." in n else "" for n in colors if n.rsplit(".", 1)[-1] == "bg"})
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        prefix = f"{mode}." if mode else ""
        roles = {n[len(prefix):]: hx for n, hx in colors.items() if n.startswith(prefix) and "." not in n[len(prefix):] and hx}
        backgrounds = [r for r in roles if r == "bg" or r.startswith("surface")]
        checks: List[Tuple[str, str, float, str]] = []
        checks += [(fg, bg, 4.5, "fail") for fg in roles if fg.startswith("text") for bg in backgrounds]
        checks += [(fg, fg[3:], 4.5, "fail") for fg in roles if fg.startswith("on-") and fg[3:] in roles]
        checks += [(fg, "bg", 3.0, "fail") for fg in roles if fg == "focus-ring"]
        checks += [(fg, "bg", 3.0, "warn") for fg in roles if fg == "border"]
        for fg, bg, need, level in checks:
            ratio = round(contrast_ratio(roles[fg][:7], roles[bg][:7]), 2)
            status = "pass" if ratio >= need else level
            rows.append({"mode": mode or "default", "fg": fg, "bg": bg, "ratio": ratio, "needs": need, "status": status})
    return rows


def type_scale(tokens: Dict[str, Dict[str, Any]], resolved: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for name, tok in tokens.items():
        if tok["type"] != "typography" or not isinstance(resolved.get(name), dict):
            continue
        v = resolved[name]
        family = v.get("fontFamily")
        rows.append({"token": name,
                     "family": family[0] if isinstance(family, list) and family else family,
                     "size": v.get("fontSize"), "px": None if to_px(v.get("fontSize")) is None else round(to_px(v.get("fontSize")), 1),
                     "weight": v.get("fontWeight"), "lineHeight": v.get("lineHeight"),
                     "letterSpacing": v.get("letterSpacing", "0")})
    rows.sort(key=lambda r: -(r["px"] or 0))
    for bigger, smaller in zip(rows, rows[1:]):
        if bigger["px"] and smaller["px"]:
            bigger["ratio"] = round(bigger["px"] / smaller["px"], 3)
    return rows


def check(data: Dict[str, Any]) -> Dict[str, Any]:
    tokens = collect(data)
    resolved, errors, warnings = validate(tokens)
    contrast = contrast_pairs(tokens, resolved)
    by_type: Dict[str, int] = {}
    for tok in tokens.values():
        by_type[tok["type"] or "?"] = by_type.get(tok["type"] or "?", 0) + 1
    return {"tokens": len(tokens), "by_type": by_type, "errors": errors, "warnings": warnings,
            "contrast": contrast, "type_scale": type_scale(tokens, resolved),
            "ok": not errors and not any(r["status"] == "fail" for r in contrast)}


def to_markdown(report: Dict[str, Any], source: str) -> str:
    icon = {"pass": "✅ pass", "fail": "❌ fail", "warn": "⚠️ check"}
    out = [f"## Token check: `{source}`", "",
           f"{report['tokens']} tokens · " + ", ".join(f"{k} {v}" for k, v in sorted(report["by_type"].items())),
           "", f"**Result:** {'OK' if report['ok'] else 'problems found'}", ""]
    if report["errors"] or report["warnings"]:
        out += ["### Problems", ""] + [f"- ❌ {e}" for e in report["errors"]] + [f"- ⚠️ {w}" for w in report["warnings"]] + [""]
    if report["contrast"]:
        out += ["### Contrast (WCAG 2.2)", "", md_table(
            ["Mode", "Foreground", "Background", "Ratio", "Needs", "Status"],
            [[r["mode"], f"`{r['fg']}`", f"`{r['bg']}`", f"{r['ratio']}:1", f"{r['needs']}:1", icon[r["status"]]] for r in report["contrast"]]), ""]
    else:
        out += ["_No color mode found: put role colors (bg, surface, text, primary, on-primary …) in a group such as `color.light`._", ""]
    if report["type_scale"]:
        out += ["### Type scale", "", md_table(
            ["Token", "Family", "Size", "px", "Weight", "Line height", "Tracking", "Step ratio"],
            [[f"`{r['token']}`", r["family"], r["size"], r["px"] if r["px"] is not None else "—", r["weight"],
              r["lineHeight"], r["letterSpacing"], r.get("ratio", "—")] for r in report["type_scale"]]), ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="tokens.json (W3C Design Tokens format)")
    parser.add_argument("--format", choices=["md", "json"], default="md")
    args = parser.parse_args(argv)
    path = Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print(f"error: {path} must contain a JSON object", file=sys.stderr)
        return 2
    report = check(data)
    print(json.dumps(report, indent=2) if args.format == "json" else to_markdown(report, str(path)))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
