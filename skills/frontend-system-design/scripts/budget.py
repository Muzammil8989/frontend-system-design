#!/usr/bin/env python3
"""Generate a performance budget for a product type.

Outputs a Markdown table (default), JSON, or a Lighthouse budget.json
(https://web.dev/articles/use-lighthouse-for-performance-budgets).

Examples:
  python3 budget.py --from "online store for sneakers"
  python3 budget.py --type dashboard --format lighthouse > budget.json
"""

from __future__ import annotations

import argparse
import json
import sys

from fsd_core import by_id, ensure_utf8_stdout, md_table, search

CWV = {"lcp_ms": 2500, "inp_ms": 200, "cls": 0.1}

# Starting targets for native/cross-platform apps. Measure on a mid-range device, release build.
NATIVE_TARGETS = {
    "mobile": [
        ("Cold start (tap → first usable screen)", "≤ 2 s", "Android vitals flags ≥ 5 s cold starts as excessive"),
        ("Warm / hot start", "≤ 1 s / ≤ 0.5 s", "Restore state, don't refetch everything"),
        ("Frame time", "≤ 16.7 ms @ 60 Hz · ≤ 8.3 ms @ 120 Hz", "Profile scrolling lists and animations"),
        ("Frozen frames (> 700 ms)", "≈ 0", "Never block the UI thread with I/O"),
        ("User-perceived crash rate", "< 1.09 % of daily users", "Android vitals bad-behavior threshold; aim far lower"),
        ("User-perceived ANR rate (Android)", "< 0.47 % of daily users", "Android vitals bad-behavior threshold"),
        ("Download size", "≤ 40 MB (starting target)", "App bundles/thinning; lazy-download heavy assets"),
        ("Interaction feedback", "≤ 100 ms", "Pressed states, optimistic UI"),
    ],
    "desktop": [
        ("Cold start (launch → usable window)", "≤ 2 s", "Show the window early, load panels lazily"),
        ("Input latency (keypress → paint)", "≤ 100 ms (≤ 50 ms for editors)", "Keep heavy work off the UI thread"),
        ("Idle memory", "Tauri ≤ 150 MB · Electron ≤ 300 MB (starting targets)", "Watch long-session growth"),
        ("Installer size", "Tauri ≤ 15 MB · Electron ≤ 150 MB (starting targets)", "Strip unused locales and assets"),
        ("Frame time", "≤ 16.7 ms @ 60 Hz", "Animations, scrolling, resize"),
        ("Crash-free sessions", "≥ 99.5 %", "Crash reporting + symbol upload"),
    ],
}


def build(product: dict) -> dict:
    js, css, font, img = (int(product[k]) for k in ("js_kb", "css_kb", "font_kb", "img_kb"))
    return {
        "product_type": product["id"],
        "name": product["name"],
        "core_web_vitals_p75": {"lcp_ms": round(float(product["lcp_s"]) * 1000), "inp_ms": int(product["inp_ms"]), "cls": CWV["cls"]},
        "resource_sizes_kb": {"script": js, "stylesheet": css, "font": font, "image": img, "total": js + css + font + img + 50},
        "lab_targets": {"ttfb_ms": 800, "fcp_ms": 1800, "total_blocking_time_ms": 200},
        "request_counts": {"third-party": 10, "script": 15, "font": 4},
    }


def lighthouse(b: dict) -> list:
    sizes = b["resource_sizes_kb"]
    return [{
        "path": "/*",
        "timings": [
            {"metric": "first-contentful-paint", "budget": b["lab_targets"]["fcp_ms"]},
            {"metric": "largest-contentful-paint", "budget": b["core_web_vitals_p75"]["lcp_ms"]},
            {"metric": "total-blocking-time", "budget": b["lab_targets"]["total_blocking_time_ms"]},
            {"metric": "cumulative-layout-shift", "budget": b["core_web_vitals_p75"]["cls"]},
        ],
        "resourceSizes": [{"resourceType": k, "budget": v} for k, v in sizes.items()],
        "resourceCounts": [{"resourceType": k, "budget": v} for k, v in b["request_counts"].items()],
    }]


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--type", help="product type id from data/product-types.csv")
    src.add_argument("--from", dest="description", help="product description (auto-classified)")
    parser.add_argument("--format", choices=("md", "json", "lighthouse"), default="md")
    parser.add_argument("--platform", choices=("web", "mobile", "desktop"), default="web",
                        help="web (Core Web Vitals + transfer sizes) or native app targets")
    args = parser.parse_args(argv)

    products = by_id("product-types.csv")
    if args.type:
        if args.type not in products:
            parser.error(f"unknown type {args.type!r}; choose from {', '.join(products)}")
        product = products[args.type]
    else:
        hits = search("products", args.description, limit=1)
        product = hits[0][1] if hits else products["saas"]

    if args.platform != "web":
        targets = NATIVE_TARGETS[args.platform]
        if args.format == "lighthouse":
            parser.error("--format lighthouse is only for --platform web")
        if args.format == "json":
            print(json.dumps({"product_type": product["id"], "platform": args.platform,
                              "targets": [{"metric": m, "target": t, "note": n} for m, t, n in targets]}, indent=2, ensure_ascii=False))
        else:
            print(f"## {args.platform.title()} performance targets — {product['name']} (`{product['id']}`)\n")
            print(md_table(["Metric", "Starting target", "Notes"], targets))
            print("\nMeasure release builds on a mid-range device (and a low-end Android for mobile). See references/platforms/"
                  f"{args.platform}.md and the stack file in references/stacks/.")
        return 0

    b = build(product)
    if args.format == "json":
        print(json.dumps(b, indent=2))
    elif args.format == "lighthouse":
        print(json.dumps(lighthouse(b), indent=2))
    else:
        cwv, sizes, lab = b["core_web_vitals_p75"], b["resource_sizes_kb"], b["lab_targets"]
        print(f"## Performance budget — {b['name']} (`{b['product_type']}`)\n")
        print("**Core Web Vitals (field, p75, mobile)**\n")
        print(md_table(["LCP", "INP", "CLS"], [(f"≤ {cwv['lcp_ms'] / 1000:g} s", f"≤ {cwv['inp_ms']} ms", f"≤ {cwv['cls']}")]))
        print("\n**Initial-route transfer size (compressed)**\n")
        print(md_table(["JS", "CSS", "Fonts", "Images", "Total"], [tuple(f"{sizes[k]} KB" for k in ("script", "stylesheet", "font", "image", "total"))]))
        print("\n**Lab diagnostics**\n")
        print(md_table(["TTFB", "FCP", "TBT"], [(f"≤ {lab['ttfb_ms']} ms", f"≤ {lab['fcp_ms']} ms", f"≤ {lab['total_blocking_time_ms']} ms")]))
        print("\nEnforce in CI: `--format lighthouse > budget.json` for Lighthouse CI, plus a bundle-size check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
