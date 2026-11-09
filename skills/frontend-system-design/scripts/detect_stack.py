#!/usr/bin/env python3
"""Detect a project's frontend/app stack from its files (web, mobile, desktop).

Tells the agent which `references/stacks/<ref>.md` and `references/platforms/<platform>.md`
to read before designing or auditing. Looks at the project root plus common monorepo
folders (apps/*, packages/*). Read-only, no network.

Examples:
  python3 detect_stack.py .
  python3 detect_stack.py ../my-app --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fsd_core import ensure_utf8_stdout, md_table

# (package.json dependency, stack id, name, platform, reference file) — most specific first
NPM_RULES = [
    ("expo", "expo", "Expo (React Native)", "mobile", "react-native-expo"),
    ("react-native", "react-native", "React Native", "mobile", "react-native-expo"),
    ("@capacitor/core", "capacitor", "Capacitor", "mobile", "ionic-capacitor"),
    ("@ionic/core", "ionic", "Ionic Framework", "mobile", "ionic-capacitor"),
    ("@tauri-apps/api", "tauri", "Tauri", "desktop", "tauri"),
    ("electron", "electron", "Electron", "desktop", "electron"),
    ("next", "nextjs", "Next.js", "web", "nextjs"),
    ("nuxt", "nuxt", "Nuxt", "web", "vue-nuxt"),
    ("@sveltejs/kit", "sveltekit", "SvelteKit", "web", "svelte-sveltekit"),
    ("astro", "astro", "Astro", "web", "astro"),
    ("@angular/core", "angular", "Angular", "web", "angular"),
    ("@builder.io/qwik", "qwik", "Qwik", "web", "qwik"),
    ("@qwik.dev/core", "qwik", "Qwik", "web", "qwik"),
    ("@solidjs/start", "solidstart", "SolidStart", "web", "solid"),
    ("solid-js", "solid", "Solid", "web", "solid"),
    ("@react-router/dev", "react-router", "React Router (framework mode)", "web", "react-router"),
    ("@remix-run/react", "react-router", "Remix / React Router", "web", "react-router"),
    ("lit", "lit", "Lit (Web Components)", "web", "web-components-lit"),
    ("@hotwired/turbo", "hotwire", "Hotwire", "web", "server-rendered-mpa"),
    ("htmx.org", "htmx", "htmx", "web", "server-rendered-mpa"),
    ("vue", "vue", "Vue", "web", "vue-nuxt"),
    ("svelte", "svelte", "Svelte", "web", "svelte-sveltekit"),
    ("react", "react", "React", "web", "react-vite"),
]

SKIP = {"node_modules", ".git", "dist", "build", ".next", ".nuxt", ".svelte-kit", "Pods", ".gradle", "bin", "obj", "target", ".dart_tool"}
MAX_FILE_BYTES = 1_000_000  # manifests larger than this are ignored


def _read(p: Path) -> str:
    """Text of a regular (non-symlink) file of at most MAX_FILE_BYTES, else "". A UTF-8 BOM is dropped."""
    try:
        st = os.lstat(p)
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE_BYTES:
            return ""
        with open(p, "rb") as fh:
            data = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return ""
    if len(data) > MAX_FILE_BYTES:
        return ""
    return data.decode("utf-8-sig", errors="replace")


def _dict(value) -> Dict:
    return value if isinstance(value, dict) else {}


def _candidate_dirs(root: Path) -> List[Path]:
    dirs = [root]
    for group in ("apps", "packages", "mobile", "web", "desktop", "client", "frontend"):
        g = root / group
        if g.is_dir():
            dirs.append(g) if (g / "package.json").exists() or (g / "pubspec.yaml").exists() else None
            dirs.extend(sorted(d for d in g.iterdir() if d.is_dir() and d.name not in SKIP))
    return dirs


def _glob_one(d: Path, pattern: str) -> Optional[Path]:
    for p in d.glob(pattern):
        # only parts below the search dir count: a project inside e.g. ~/build/my-app must still be detected
        if not any(part in SKIP for part in p.relative_to(d).parts):
            return p
    return None


def detect_dir(d: Path, root: Path) -> List[Dict[str, str]]:
    found: List[Dict[str, str]] = []
    rel = d.relative_to(root).as_posix() if d != root else "."

    def add(stack_id, name, platform, ref, evidence):
        found.append({"id": stack_id, "name": name, "platform": platform, "ref": ref, "path": rel, "evidence": evidence})

    pkg = d / "package.json"
    if pkg.exists():
        try:
            data = json.loads(_read(pkg) or "{}")
        except ValueError:
            data = {}
        data = _dict(data)  # a top-level array or null is not a manifest
        deps = {**_dict(data.get("dependencies")), **_dict(data.get("devDependencies"))}
        matched = set()
        for dep, sid, name, platform, ref in NPM_RULES:
            if dep in deps and ref not in matched:
                # generic libraries only count when nothing more specific matched on the same platform
                if sid in ("react", "vue", "svelte") and any(f["platform"] == "web" for f in found):
                    continue
                if sid == "react-native" and "react-native-expo" in matched:
                    continue
                if sid == "react" and "vite" in deps:
                    name = "React + Vite (SPA)"
                add(sid, name, platform, ref, f"package.json → {dep}")
                matched.add(ref)

    pubspec = d / "pubspec.yaml"
    if pubspec.exists() and re.search(r"^\s*flutter\s*:", _read(pubspec), re.M):
        add("flutter", "Flutter", "cross", "flutter", "pubspec.yaml → flutter")

    for gradle in ("build.gradle.kts", "build.gradle", "app/build.gradle.kts", "app/build.gradle", "composeApp/build.gradle.kts"):
        text = _read(d / gradle)
        if not text:
            continue
        if re.search(r"org\.jetbrains\.compose|compose\.multiplatform|kotlin\(\"multiplatform\"\)|kotlinMultiplatform", text):
            add("compose-multiplatform", "Compose Multiplatform (KMP)", "cross", "compose-multiplatform", f"{gradle} → compose multiplatform")
            break
        if re.search(r"androidx\.compose|compose\s*=\s*true|buildFeatures\s*\{[^}]*compose", text, re.S):
            add("jetpack-compose", "Jetpack Compose (Android)", "mobile", "jetpack-compose", f"{gradle} → androidx.compose")
            break

    if _glob_one(d, "*.xcodeproj") or (d / "Package.swift").exists() or _glob_one(d, "ios/*.xcodeproj"):
        if not any(f["platform"] in ("mobile", "cross") for f in found):  # RN/Flutter projects also contain ios/
            swift_ui = _glob_one(d, "**/*App.swift")
            add("swiftui", "SwiftUI (Apple platforms)", "mobile", "swiftui", f"{'Xcode project' if not (d / 'Package.swift').exists() else 'Package.swift'}{' + SwiftUI App' if swift_ui else ''}")

    csproj = _glob_one(d, "*.csproj")
    if csproj and "UseMaui" in _read(csproj):
        add("dotnet-maui", ".NET MAUI", "cross", "dotnet-maui", f"{csproj.name} → UseMaui")

    if (d / "src-tauri" / "tauri.conf.json").exists() or "tauri" in _read(d / "src-tauri" / "Cargo.toml"):
        if not any(f["id"] == "tauri" for f in found):
            add("tauri", "Tauri", "desktop", "tauri", "src-tauri/")

    if "turbo-rails" in _read(d / "Gemfile"):
        add("hotwire", "Rails + Hotwire", "web", "server-rendered-mpa", "Gemfile → turbo-rails")
    composer = _read(d / "composer.json")
    if "livewire/livewire" in composer:
        add("livewire", "Laravel Livewire", "web", "server-rendered-mpa", "composer.json → livewire")
    py_deps = _read(d / "requirements.txt") + _read(d / "pyproject.toml")
    if re.search(r"\bdjango\b", py_deps, re.I) and not found:
        add("django", "Django (server-rendered)", "web", "server-rendered-mpa", "requirements → django")
    return found


def detect(path: str) -> Dict:
    root = Path(path).resolve()
    stacks: List[Dict[str, str]] = []
    seen = set()
    for d in _candidate_dirs(root):
        for s in detect_dir(d, root):
            key = (s["id"], s["path"])
            if key not in seen:
                seen.add(key)
                stacks.append(s)
    platforms = sorted({s["platform"] for s in stacks})
    refs = list(dict.fromkeys(s["ref"] for s in stacks))
    return {
        "root": str(root),
        "primary": stacks[0] if stacks else None,
        "stacks": stacks,
        "platforms": platforms,
        "read": list(dict.fromkeys([f"references/stacks/{r}.md" for r in refs]
                                   + [f"references/platforms/{p if p != 'cross' else 'mobile'}.md" for p in platforms])),
    }


def main(argv=None) -> int:
    ensure_utf8_stdout()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not Path(args.path).is_dir():
        parser.error(f"not a directory: {args.path}")
    result = detect(args.path)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    if not result["stacks"]:
        print("No known frontend/app stack detected (new project?). Use recommend.py to choose one.")
        return 0
    print(f"## Detected stack: {result['primary']['name']}\n")
    print(md_table(["Stack", "Platform", "Where", "Evidence", "Reference"],
                   [(s["name"], s["platform"], s["path"], s["evidence"], f"stacks/{s['ref']}.md") for s in result["stacks"]]))
    print("\nRead before designing or auditing:\n" + "\n".join(f"- `{r}`" for r in result["read"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
