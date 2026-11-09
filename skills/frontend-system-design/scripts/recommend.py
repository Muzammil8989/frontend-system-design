#!/usr/bin/env python3
"""Recommend a frontend/app architecture + UI system for a product (web, mobile or desktop).

Classifies the product against data/product-types.csv (BM25), infers the platform,
then resolves the stack, UI styles, palettes, font pairings, UX patterns, budget,
the reference files to read next, and the learning notes that explain the decisions.

Examples:
  python3 recommend.py "real-time analytics dashboard for logistics"
  python3 recommend.py "fitness tracking app for iOS and Android"
  python3 recommend.py "markdown notes desktop app" --platform desktop
  python3 recommend.py "online furniture store" --stack nuxt --json
  python3 recommend.py "add a booking flow" --project ../my-app      # detect stack from code
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fsd_core import BM25, SKILL_DIR, by_id, contrast_ratio, ensure_utf8_stdout, load_csv, md_table, search, split_list

PLATFORMS = ("web", "mobile", "desktop", "cross")
DEFAULT_MOBILE = "expo;flutter;swiftui;jetpack-compose"
DEFAULT_DESKTOP = "tauri;electron"
MOBILE_HINT = re.compile(r"\b(mobile app|ios|android|iphone|ipad|app store|play store|react native|flutter|swift(ui)?|kotlin|native app|wearable)\b", re.I)
DESKTOP_HINT = re.compile(r"\b(desktop|windows app|mac app|macos app|linux app|electron|tauri|menu bar|system tray)\b", re.I)
WEB_HINT = re.compile(r"\b(web ?site|web app|website|landing|browser|seo|saas|dashboard|web)\b", re.I)

# detect_stack.py ids that are not data/stacks.csv ids -> the stacks.csv row for the same framework
DETECTED_TO_STACK = {
    "react": "vite-react",
    "react-native": "expo",
    "vue": "nuxt",
    "svelte": "sveltekit",
    "solid": "solidstart",
    "django": "htmx",
}


def infer_platform(description: str, product: Dict[str, str]) -> str:
    mobile, desktop, web = bool(MOBILE_HINT.search(description)), bool(DESKTOP_HINT.search(description)), bool(WEB_HINT.search(description))
    if mobile and (web or desktop):
        return "cross"
    if mobile:
        return "mobile"
    if desktop:
        return "desktop"
    listed = split_list(product.get("platforms", "web"))
    return listed[0] if listed else "web"  # the product type lists its primary platform first


def relevant_notes(query: str, limit: int = 3) -> List[Dict[str, str]]:
    index_file = SKILL_DIR / "references" / "knowledge" / "index.json"
    if not index_file.exists():
        return []
    topics = [t for t in json.loads(index_file.read_text(encoding="utf-8"))["topics"] if t.get("written")]
    rows = [{"id": t["file"], "title": t["title"], "informs": t["informs"], "category": t["category"]} for t in topics]
    if not rows:
        return []
    hits = BM25(rows, ("informs", "title", "category")).score(query)[:limit]
    return [{"title": r["title"], "file": f"references/knowledge/{r['id']}", "informs": r["informs"]} for _, r in hits]


def recommend(description: str, forced_type: Optional[str] = None, platform: Optional[str] = None,
              stack: Optional[str] = None, project: Optional[str] = None, alternatives: int = 2) -> Dict:
    products = by_id("product-types.csv")
    stacks = by_id("stacks.csv")
    styles = by_id("ui-styles.csv")
    patterns = by_id("ux-patterns.csv")

    detected = None
    if project:
        if not Path(project).is_dir():
            raise SystemExit(f"--project is not a directory: {project}")
        from detect_stack import detect  # local import keeps recommend.py usable on its own
        detected = detect(project)
        if detected["primary"] and not stack:
            found = detected["primary"]["id"]
            found = found if found in stacks else DETECTED_TO_STACK.get(found, "")
            if found in stacks:
                stack = found
        if detected["platforms"] and not platform:
            platform = "cross" if len(detected["platforms"]) > 1 else detected["platforms"][0]

    ranked = search("products", description, limit=len(products))
    if forced_type:
        if forced_type not in products:
            raise SystemExit(f"unknown --type {forced_type!r}; choose from {', '.join(products)}")
        primary, confidence = products[forced_type], "forced"
    elif ranked:
        primary = ranked[0][1]
        top, second = ranked[0][0], (ranked[1][0] if len(ranked) > 1 else 0.0)
        confidence = "high" if top >= 2 * max(second, 0.01) else "medium" if top >= 1.25 * max(second, 0.01) else "low"
    else:
        primary, confidence = products["saas"], "low (no keyword match — defaulted to SaaS web app)"

    if platform and platform not in PLATFORMS:
        raise SystemExit(f"unknown --platform {platform!r}; choose from {', '.join(PLATFORMS)}")
    if stack and not platform and stack in stacks and stacks[stack]["category"] == "framework":
        platform = {"cross": "mobile"}.get(stacks[stack]["platform"], stacks[stack]["platform"])
    platform = platform or infer_platform(description, primary)

    # Stack ids for the chosen platform
    web_ids = split_list(primary["stacks"])
    mobile_ids = split_list(primary.get("mobile_stacks") or DEFAULT_MOBILE)
    desktop_ids = split_list(primary.get("desktop_stacks") or DEFAULT_DESKTOP)
    shared = [i for i in web_ids if stacks.get(i, {}).get("platform") == "cross"]
    if platform == "web":
        ids = web_ids
    elif platform == "mobile":
        ids = mobile_ids + shared
    elif platform == "desktop":
        ids = desktop_ids + [i for i in web_ids if stacks.get(i, {}).get("category") in ("framework", "state", "ui-kit", "styling")][:3]
    else:  # cross: native/mobile surface + web surface
        ids = mobile_ids[:2] + web_ids
    if stack:
        if stack not in stacks:
            raise SystemExit(f"unknown --stack {stack!r}; see data/stacks.csv")
        ids = [stack] + [i for i in ids if i != stack]
    ids = list(dict.fromkeys(i for i in ids if i in stacks))

    palette_hits = search("palettes", f"{primary['palette_query']} {description}", limit=3)
    font_hits = search("fonts", f"{primary['font_query']} {description}", limit=3)

    refs = list(dict.fromkeys(stacks[i]["ref"] for i in ids if stacks[i].get("ref") and stacks[i]["category"] == "framework"))[:4]
    platform_files = ["web", "mobile"] if platform == "cross" else [platform]
    read_next = (
        [f"references/platforms/{p}.md" for p in platform_files]
        + [f"references/stacks/{r}.md" for r in refs]
        + [f"references/playbooks/product-playbooks.md → \"{primary['playbook']}\"", "references/core/architecture.md", "references/core/ui-design.md"]
    )
    notes = relevant_notes(" ".join([description, primary["name"], primary["rendering"], primary["state"], platform]))

    return {
        "input": description,
        "product_type": {"id": primary["id"], "name": primary["name"], "confidence": confidence, "playbook": primary["playbook"]},
        "platform": platform,
        "detected": detected,
        "alternatives": [{"id": row["id"], "name": row["name"], "score": round(score, 2)}
                         for score, row in [h for h in ranked if h[1]["id"] != primary["id"]][:alternatives]],
        "architecture": {"rendering": primary["rendering"], "state": primary["state"]},
        "stack": [{"id": s["id"], "name": s["name"], "category": s["category"], "platform": s["platform"], "why": s["best_for"],
                   "ref": s.get("ref", ""), "url": s["url"]} for s in (stacks[i] for i in ids)],
        "ui_styles": [{"id": s["id"], "name": s["name"], "characteristics": s["characteristics"], "a11y": s["a11y_notes"]}
                      for s in (styles[i] for i in split_list(primary["ui_styles"]) if i in styles)],
        "palettes": [
            {"id": row["id"], "name": row["name"], "scheme": row["scheme"], "bg": row["bg"], "text": row["text"],
             "primary": row["primary"], "on_primary": row["on_primary"], "accent": row["accent"],
             "contrast_text": round(contrast_ratio(row["text"], row["bg"]), 2),
             "contrast_primary": round(contrast_ratio(row["on_primary"], row["primary"]), 2)}
            for _, row in palette_hits
        ],
        "fonts": [{"id": r["id"], "heading": r["heading"], "body": r["body"], "mono": r["mono"], "notes": r["notes"]} for _, r in font_hits],
        "patterns": [{"id": p["id"], "name": p["name"], "key_rules": p["key_rules"]} for p in (patterns[i] for i in split_list(primary["patterns"]) if i in patterns)],
        "budget": {"platform": platform, "js_kb": int(primary["js_kb"]), "css_kb": int(primary["css_kb"]), "font_kb": int(primary["font_kb"]),
                   "img_kb": int(primary["img_kb"]), "lcp_s": float(primary["lcp_s"]), "inp_ms": int(primary["inp_ms"]), "cls": 0.1},
        "read_next": read_next,
        "notes": notes,
    }


def to_markdown(r: Dict) -> str:
    pt = r["product_type"]
    out = [f"## Recommendation: {pt['name']} · platform: {r['platform']}", "",
           f"**Input:** {r['input']}  ",
           f"**Product type:** `{pt['id']}` — confidence: {pt['confidence']}  "]
    if r.get("detected") and r["detected"]["primary"]:
        out.append(f"**Detected in project:** {', '.join(s['name'] for s in r['detected']['stacks'])}  ")
    if r["alternatives"]:
        out.append("**Also consider:** " + ", ".join(f"`{a['id']}` ({a['name']})" for a in r["alternatives"]))
    out += ["", "### Architecture", f"- **Rendering / app model:** {r['architecture']['rendering']}", f"- **State:** {r['architecture']['state']}", "",
            "### Stack",
            md_table(["Category", "Choice", "Platform", "Why"], [(s["category"], f"[{s['name']}]({s['url']})", s["platform"], s["why"]) for s in r["stack"]]),
            "", "### UI direction",
            md_table(["Style", "Characteristics", "Accessibility note"], [(s["name"], s["characteristics"], s["a11y"]) for s in r["ui_styles"]]),
            "", "### Palettes (contrast-checked)",
            md_table(["Palette", "Scheme", "bg / text", "primary / on-primary", "accent", "Contrast text · primary"],
                     [(p["name"], p["scheme"], f"{p['bg']} / {p['text']}", f"{p['primary']} / {p['on_primary']}", p["accent"],
                       f"{p['contrast_text']}:1 · {p['contrast_primary']}:1") for p in r["palettes"]]),
            "", "### Font pairings",
            md_table(["Heading", "Body", "Mono", "Notes"], [(f["heading"], f["body"], f["mono"], f["notes"]) for f in r["fonts"]]),
            "", "### Key UX patterns",
            md_table(["Pattern", "Key rules"], [(p["name"], p["key_rules"]) for p in r["patterns"]]), ""]
    b = r["budget"]
    if r["platform"] in ("mobile", "desktop"):
        out += ["### Performance budget", f"Run `budget.py --type {pt['id']} --platform {r['platform']}` for startup, frame-time and size targets.", ""]
    else:
        out += ["### Performance budget (initial route, mobile network, compressed)",
                md_table(["JS", "CSS", "Fonts", "Images", "LCP", "INP", "CLS"],
                         [(f"{b['js_kb']} KB", f"{b['css_kb']} KB", f"{b['font_kb']} KB", f"{b['img_kb']} KB", f"≤ {b['lcp_s']} s", f"≤ {b['inp_ms']} ms", f"≤ {b['cls']}")]), ""]
    out += ["### Read next", *[f"- `{x}`" for x in r["read_next"]], ""]
    if r["notes"]:
        out += ["### Learn more (project notes behind these decisions)",
                *[f"- [{n['title']}]({n['file']}): {n['informs']}" for n in r["notes"]], ""]
    out.append("> Starting point only — validate against the requirements (references/core/requirements.md) and justify deviations.")
    return "\n".join(out)


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("description", nargs="?", default="", help="one-line product description")
    parser.add_argument("--type", dest="forced_type", help="force a product type id (see --list-types)")
    parser.add_argument("--platform", choices=PLATFORMS, help="web | mobile | desktop | cross (default: inferred)")
    parser.add_argument("--stack", help="preferred stack id from data/stacks.csv (e.g. nuxt, flutter, swiftui)")
    parser.add_argument("--project", help="path to an existing project; its stack is detected and used")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-types", action="store_true", help="list product type ids and exit")
    args = parser.parse_args(argv)

    if args.list_types:
        for row in load_csv("product-types.csv"):
            print(f"{row['id']:<16} {row['name']:<34} {row['platforms']}")
        return 0
    if not args.description:
        parser.error("a product description is required")
    if args.project and not Path(args.project).is_dir():
        parser.error(f"--project is not a directory: {args.project}")

    result = recommend(args.description, args.forced_type, args.platform, args.stack, args.project)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else to_markdown(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
