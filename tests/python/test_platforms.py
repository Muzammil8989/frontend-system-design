"""Tests for multi-platform support: stack detection, platform-aware recommendations,
mobile/desktop budgets, native audit rules, stack reference files and knowledge notes.

Run:  python -m unittest discover -s tests/python -v
"""

import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "frontend-system-design"
sys.path.insert(0, str(SKILL / "scripts"))

import audit_scan  # noqa: E402
import budget  # noqa: E402
import detect_stack  # noqa: E402
import fsd_core  # noqa: E402
import recommend  # noqa: E402

STACK_HEADINGS = [
    "## When to choose", "## Project structure", "## Routing & navigation", "## State & data",
    "## Styling & design system", "## Performance", "## Accessibility", "## Testing",
    "## Build & deploy", "## Pitfalls", "## References",
]


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def readme_roadmap_numbers():
    """Topic numbers of the README roadmap tables, parsed the same way as scripts/sync-knowledge.js."""
    numbers, in_phase = [], False
    for line in (ROOT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        if re.match(r"^## Phase \d+ \u2014 .+$", line):
            in_phase = True
            continue
        if line.startswith("## "):
            in_phase = False
        row = re.match(r"^\|\s*(\d+)\s*\|\s*(\u2705|\u2b1c)\s*(.+?)\s*\|\s*(.+?)\s*\|$", line) if in_phase else None
        if row:
            numbers.append(int(row.group(1)))
    return numbers


class DetectStackTest(unittest.TestCase):
    def detect(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel, text in files.items():
                write(root, rel, text)
            return detect_stack.detect(tmp)

    def test_web_frameworks(self):
        r = self.detect({"package.json": json.dumps({"dependencies": {"next": "x", "react": "x"}})})
        self.assertEqual(r["primary"]["id"], "nextjs")
        self.assertEqual([s["id"] for s in r["stacks"]], ["nextjs"], "generic react must not duplicate next")
        r = self.detect({"package.json": json.dumps({"dependencies": {"react": "x"}, "devDependencies": {"vite": "x"}})})
        self.assertEqual(r["primary"]["ref"], "react-vite")

    def test_mobile_and_desktop(self):
        self.assertEqual(self.detect({"pubspec.yaml": "name: app\nflutter:\n  uses-material-design: true\n"})["primary"]["id"], "flutter")
        self.assertEqual(self.detect({"package.json": json.dumps({"dependencies": {"expo": "x", "react-native": "x", "react": "x"}})})["primary"]["id"], "expo")
        self.assertEqual(self.detect({"app/build.gradle.kts": "android { buildFeatures { compose = true } }\ndependencies { implementation(\"androidx.compose.ui:ui\") }"})["primary"]["id"], "jetpack-compose")
        self.assertEqual(self.detect({"App.csproj": "<Project><PropertyGroup><UseMaui>true</UseMaui></PropertyGroup></Project>"})["primary"]["id"], "dotnet-maui")
        r = self.detect({"package.json": json.dumps({"dependencies": {"@tauri-apps/api": "x", "react": "x"}}), "src-tauri/tauri.conf.json": "{}"})
        self.assertEqual(r["primary"]["id"], "tauri")
        self.assertIn("references/platforms/desktop.md", r["read"])

    def test_monorepo(self):
        r = self.detect({
            "apps/web/package.json": json.dumps({"dependencies": {"nuxt": "x"}}),
            "apps/mobile/pubspec.yaml": "flutter:\n",
        })
        self.assertEqual({s["id"] for s in r["stacks"]}, {"nuxt", "flutter"})

    def test_empty_project(self):
        self.assertIsNone(self.detect({})["primary"])

    def test_package_json_with_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_bytes(b"\xef\xbb\xbf" + json.dumps({"dependencies": {"nuxt": "x"}}).encode())
            self.assertEqual(detect_stack.detect(tmp)["primary"]["id"], "nuxt")

    def test_malformed_package_json_shapes(self):
        r = self.detect({"package.json": json.dumps({"dependencies": None, "devDependencies": {"astro": "x"}})})
        self.assertEqual(r["primary"]["id"], "astro")
        self.assertIsNone(self.detect({"package.json": "[1, 2]"})["primary"])
        self.assertIsNone(self.detect({"package.json": "null"})["primary"])

    def test_project_under_a_build_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "build" / "target" / "app"
            write(proj, "App.xcodeproj/project.pbxproj", "")
            write(proj, "App.csproj", "<Project><PropertyGroup><UseMaui>true</UseMaui></PropertyGroup></Project>")
            ids = {s["id"] for s in detect_stack.detect(str(proj))["stacks"]}
            self.assertEqual(ids, {"swiftui", "dotnet-maui"})

    def test_skip_dirs_inside_project_are_still_skipped(self):
        r = self.detect({"App.xcodeproj/project.pbxproj": "", "build/Gen/FooApp.swift": ""})
        self.assertEqual(r["primary"]["evidence"], "Xcode project")
        r = self.detect({"App.xcodeproj/project.pbxproj": "", "Sources/FooApp.swift": ""})
        self.assertEqual(r["primary"]["evidence"], "Xcode project + SwiftUI App")

    def test_reading_list_has_no_duplicates(self):
        r = self.detect({
            "apps/web/package.json": json.dumps({"dependencies": {"expo": "x"}}),
            "apps/mobile/pubspec.yaml": "flutter:\n",
        })
        self.assertEqual(r["read"].count("references/platforms/mobile.md"), 1)
        self.assertEqual(len(r["read"]), len(set(r["read"])))

    def test_symlinked_manifest_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = Path(tmp) / "elsewhere.json"
            real.write_text(json.dumps({"dependencies": {"nuxt": "x"}}), encoding="utf-8")
            proj = Path(tmp) / "proj"
            proj.mkdir()
            try:
                os.symlink(real, proj / "package.json")
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"cannot create symlinks here: {exc}")
            self.assertIsNone(detect_stack.detect(str(proj))["primary"])


class PlatformRecommendTest(unittest.TestCase):
    def test_platform_inference(self):
        cases = {
            "fitness tracking app for iOS and Android": ("fitness-health", "mobile"),
            "food delivery app with live courier tracking": ("on-demand", "mobile"),
            "markdown notes desktop app": ("desktop-app", "desktop"),
            "online furniture store": ("ecommerce", "web"),
            "consumer mobile app for splitting bills": ("mobile-consumer", "mobile"),
        }
        for text, (ptype, platform) in cases.items():
            with self.subTest(text=text):
                r = recommend.recommend(text)
                self.assertEqual((r["product_type"]["id"], r["platform"]), (ptype, platform))

    def test_mobile_stack_and_reading_list(self):
        r = recommend.recommend("social app", platform="mobile")
        frameworks = [s for s in r["stack"] if s["category"] == "framework"]
        self.assertTrue(all(s["platform"] in ("mobile", "cross") for s in frameworks))
        self.assertIn("references/platforms/mobile.md", r["read_next"])

    def test_forced_stack(self):
        r = recommend.recommend("habit tracker", stack="flutter")
        self.assertEqual(r["stack"][0]["id"], "flutter")
        self.assertEqual(r["platform"], "mobile")
        self.assertIn("references/stacks/flutter.md", r["read_next"])

    def test_project_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), "pubspec.yaml", "flutter:\n")
            r = recommend.recommend("add a checkout flow", project=tmp)
            self.assertEqual(r["stack"][0]["id"], "flutter")

    def test_project_detection_maps_ids_to_stacks_csv(self):
        cases = {
            "vite-react": {"dependencies": {"react": "x"}, "devDependencies": {"vite": "x"}},
            "expo": {"dependencies": {"react-native": "x", "react": "x"}},
            "nuxt": {"dependencies": {"vue": "x"}},
            "sveltekit": {"devDependencies": {"svelte": "x"}},
            "solidstart": {"dependencies": {"solid-js": "x"}},
        }
        for expected, pkg in cases.items():
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                write(Path(tmp), "package.json", json.dumps(pkg))
                r = recommend.recommend("add a booking flow", project=tmp)
                self.assertEqual(r["stack"][0]["id"], expected)
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), "requirements.txt", "Django==5.0\n")
            self.assertEqual(recommend.recommend("add a booking flow", project=tmp)["stack"][0]["id"], "htmx")

    def test_every_detected_id_maps_to_a_stack(self):
        stacks = fsd_core.by_id("stacks.csv")
        for sid in {r[1] for r in detect_stack.NPM_RULES} | {"django"}:
            with self.subTest(sid=sid):
                self.assertIn(sid if sid in stacks else recommend.DETECTED_TO_STACK.get(sid), stacks)

    def test_missing_project_dir_is_an_error(self):
        missing = str(ROOT / "no-such-project-dir")
        with self.assertRaises(SystemExit):
            recommend.recommend("add a checkout flow", project=missing)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            recommend.main(["add a checkout flow", "--project", missing])
        self.assertEqual(cm.exception.code, 2)

    def test_alternatives_exclude_forced_type(self):
        natural = recommend.recommend("online furniture store")
        self.assertEqual(natural["product_type"]["id"], "ecommerce")
        forced = recommend.recommend("online furniture store", forced_type="content")
        alt_ids = [a["id"] for a in forced["alternatives"]]
        self.assertNotIn("content", alt_ids)
        self.assertEqual(alt_ids[0], "ecommerce", "the best natural match must stay an alternative when another type is forced")

    def test_notes_are_cited(self):
        r = recommend.recommend("offline-first field service app with local storage")
        self.assertTrue(any("knowledge/" in n["file"] for n in r["notes"]))
        for n in r["notes"]:
            self.assertTrue((SKILL / n["file"]).exists(), n["file"])


class BudgetAndAuditTest(unittest.TestCase):
    def test_native_budgets(self):
        for platform in ("mobile", "desktop"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = budget.main(["--type", "mobile-consumer", "--platform", platform, "--format", "json"])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(buf.getvalue())["targets"])

    def test_native_audit_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "lib/main.dart", "final img = Image.network(url);\nprefs.setString('authToken', t);\n")
            write(root, "ios/App/ContentView.swift", "Text(\"Hi\").onTapGesture {\n}\nUserDefaults.standard.set(token, forKey: \"token\")\n")
            write(root, "app/src/Main.kt", "runBlocking { load() }\nIcon(icon, contentDescription = null)\n")
            write(root, "Views/Main.xaml", "<Image Source=\"a.png\" />\n")
            write(root, "src/auth.ts", "await AsyncStorage.setItem('token', jwt)\n")
            rules = {f["rule"] for f in audit_scan.run(root, 200)["findings"]}
            for expected in ("flutter-image-no-semantics", "flutter-prefs-token", "swift-tap-gesture", "ios-userdefaults-token",
                             "kotlin-runblocking", "compose-null-description", "maui-image-no-description", "rn-asyncstorage-token"):
                self.assertIn(expected, rules)


class ReferenceFilesTest(unittest.TestCase):
    def test_stack_refs_exist_and_follow_template(self):
        refs = {s["ref"] for s in fsd_core.load_csv("stacks.csv") if s.get("ref")}
        refs |= {r[4] for r in detect_stack.NPM_RULES}
        for ref in sorted(refs):
            with self.subTest(ref=ref):
                path = SKILL / "references" / "stacks" / f"{ref}.md"
                self.assertTrue(path.exists(), f"missing references/stacks/{ref}.md")
                text = path.read_text(encoding="utf-8")
                positions = [text.find(h) for h in STACK_HEADINGS]
                self.assertTrue(all(p >= 0 for p in positions), f"{ref}: missing headings {[h for h, p in zip(STACK_HEADINGS, positions) if p < 0]}")
                self.assertEqual(positions, sorted(positions), f"{ref}: headings out of order")
                self.assertIn("```text", text, f"{ref}: project structure tree missing")

    def test_platform_guides(self):
        for p in ("web", "mobile", "desktop"):
            self.assertTrue((SKILL / "references" / "platforms" / f"{p}.md").exists(), p)

    def test_knowledge_index(self):
        index = json.loads((SKILL / "references" / "knowledge" / "index.json").read_text(encoding="utf-8"))
        topics = index["topics"]
        self.assertEqual(index["total"], len(topics))
        self.assertEqual(index["written"], sum(1 for t in topics if t["written"]))
        # the index is generated from the README roadmap (scripts/sync-knowledge.js): same topic numbers
        self.assertEqual([t["number"] for t in topics], readme_roadmap_numbers(), "index.json is stale: run scripts/sync-knowledge.js")
        for t in topics:
            if t["written"]:
                self.assertTrue((SKILL / "references" / "knowledge" / t["file"]).exists())


if __name__ == "__main__":
    unittest.main()
