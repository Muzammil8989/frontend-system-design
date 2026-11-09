"""Tests for the frontend-system-design Python engine (stdlib unittest).

Run:  python -m unittest discover -s tests/python -v
"""

import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "frontend-system-design"
sys.path.insert(0, str(SKILL / "scripts"))

import audit_scan  # noqa: E402
import budget  # noqa: E402
import fsd_core  # noqa: E402
import recommend  # noqa: E402
import search  # noqa: E402


def run_cli(module, argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = module.main(argv)
    return code, buf.getvalue()


class DataIntegrityTest(unittest.TestCase):
    def test_ids_unique_and_present(self):
        for domain, (file, _) in fsd_core.DOMAINS.items():
            rows = fsd_core.load_csv(file)
            ids = [r["id"] for r in rows]
            self.assertTrue(rows, f"{file} is empty")
            self.assertEqual(len(ids), len(set(ids)), f"duplicate ids in {file}")
            self.assertTrue(all(ids), f"empty id in {file}")

    def test_product_type_references_resolve(self):
        stacks = fsd_core.by_id("stacks.csv")
        styles = fsd_core.by_id("ui-styles.csv")
        patterns = fsd_core.by_id("ux-patterns.csv")
        playbooks = (SKILL / "references" / "playbooks" / "product-playbooks.md").read_text(encoding="utf-8")
        for p in fsd_core.load_csv("product-types.csv"):
            for s in fsd_core.split_list(p["stacks"]):
                self.assertTrue(s in stacks, f"{p['id']}: unknown stack {s}")
            for s in fsd_core.split_list(p["ui_styles"]):
                self.assertTrue(s in styles, f"{p['id']}: unknown style {s}")
            for s in fsd_core.split_list(p["patterns"]):
                self.assertTrue(s in patterns, f"{p['id']}: unknown pattern {s}")
            self.assertIn(f"## {p['playbook']}", playbooks, f"{p['id']}: playbook heading missing")
            for k in ("js_kb", "css_kb", "font_kb", "img_kb", "inp_ms"):
                self.assertGreater(int(p[k]), 0)

    def test_palettes_meet_wcag_aa(self):
        for p in fsd_core.load_csv("palettes.csv"):
            for fg, bg, minimum in (
                ("text", "bg", 4.5), ("text", "surface", 4.5), ("muted", "bg", 4.5),
                ("on_primary", "primary", 4.5), ("primary", "bg", 3.0),
                ("success", "bg", 3.0), ("warning", "bg", 3.0), ("danger", "bg", 3.0),
            ):
                ratio = fsd_core.contrast_ratio(p[fg], p[bg])
                self.assertGreaterEqual(ratio, minimum, f"{p['id']}: {fg} on {bg} = {ratio:.2f}:1 < {minimum}:1")


class CoreTest(unittest.TestCase):
    def test_contrast_ratio_known_values(self):
        self.assertAlmostEqual(fsd_core.contrast_ratio("#000000", "#FFFFFF"), 21.0, places=1)
        self.assertAlmostEqual(fsd_core.contrast_ratio("#777777", "#FFFFFF"), 4.48, places=1)

    def test_tokenize_handles_hyphens_and_plurals(self):
        toks = fsd_core.tokenize("Real-time dashboards for the team")
        self.assertIn("real-time", toks)
        self.assertIn("time", toks)
        self.assertIn("dashboard", toks)
        self.assertNotIn("the", toks)


class RecommendTest(unittest.TestCase):
    CASES = {
        "real-time analytics dashboard for logistics": "dashboard",
        "online furniture store": "ecommerce",
        "documentation site for an open source library": "content",
        "customer support chat": "chat",
        "habit tracker that works offline": "pwa",
        "ai writing assistant": "ai-assistant",
        "neobank mobile wallet": "fintech",
        "kids coding course platform": "education",
        "launch landing page with waitlist": "landing",
        "hotel booking marketplace": "booking",
        "internal admin panel for inventory": "internal",
        "collaborative whiteboard like figma": "editor",
    }

    def test_classification(self):
        for text, expected in self.CASES.items():
            with self.subTest(text=text):
                self.assertEqual(recommend.recommend(text)["product_type"]["id"], expected)

    def test_result_shape(self):
        r = recommend.recommend("b2b saas project management")
        for key in ("architecture", "stack", "ui_styles", "palettes", "fonts", "patterns", "budget"):
            self.assertTrue(r[key], f"{key} empty")
        self.assertGreaterEqual(r["palettes"][0]["contrast_text"], 4.5)

    def test_forced_type_and_cli(self):
        code, out = run_cli(recommend, ["anything", "--type", "content", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["product_type"]["id"], "content")
        code, out = run_cli(recommend, ["real-time dashboard"])
        self.assertIn("## Recommendation", out)


class SearchAndBudgetTest(unittest.TestCase):
    def test_search_domains(self):
        self.assertEqual(fsd_core.search("palettes", "fintech dark")[0][1]["id"], "fintech-dark")
        self.assertEqual(fsd_core.search("patterns", "checkout payment")[0][1]["id"], "checkout")
        self.assertEqual(fsd_core.search("stacks", "time series fast")[0][1]["id"], "uplot")
        self.assertTrue(fsd_core.search("fonts", "editorial serif reading"))

    def test_search_cli_json(self):
        code, out = run_cli(search, ["--domain", "styles", "playful kids", "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out))

    def test_budget_formats(self):
        code, out = run_cli(budget, ["--type", "dashboard", "--format", "lighthouse"])
        data = json.loads(out)
        self.assertEqual(data[0]["path"], "/*")
        self.assertTrue(any(r["resourceType"] == "script" for r in data[0]["resourceSizes"]))
        code, out = run_cli(budget, ["--from", "blog about cooking"])
        self.assertIn("Content site", out)


class AuditScanTest(unittest.TestCase):
    def test_detects_known_issues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "App.tsx").write_text(
                "import moment from 'moment'\n"
                "export function App({html}: any) {\n"
                "  localStorage.setItem('authToken', t)\n"
                "  return <div onClick={go}><img src='a.png'/><p dangerouslySetInnerHTML={{__html: html}} /></div>\n"
                "}\n",
                encoding="utf-8",
            )
            (root / "index.html").write_text("<!doctype html><html><head></head><body></body></html>", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "x.js").write_text("eval('1')", encoding="utf-8")
            (root / "package.json").write_text(json.dumps({"dependencies": {"react": "x", "moment": "x"}}), encoding="utf-8")

            report = audit_scan.run(root, 100)
            rules = {f["rule"] for f in report["findings"]}
            for expected in ("dangerous-html", "token-in-web-storage", "img-no-alt", "click-on-non-interactive", "heavy-import-moment", "html-lang", "ts-any"):
                self.assertIn(expected, rules)
            self.assertNotIn("eval", rules, "node_modules must be skipped")
            self.assertIn("moment", report["package"]["heavy_dependencies"])
            self.assertIn("react", report["package"]["frameworks"])
            self.assertIn("Static scan", audit_scan.to_markdown(report))


class AuditScanRegressionTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))  # no newline translation: line numbers are asserted
        return p

    def findings(self, rel=None):
        found = audit_scan.run(self.root, 1000)["findings"]
        return [f for f in found if rel is None or f["file"] == rel]

    def test_css_selectors_starting_with_star_or_hash_are_scanned(self):
        self.write("a.css", "/* a comment: outline: none */\n/*\n * outline: none\n */\n"
                            "*:focus { outline: none }\n#id:focus{outline:0}\n")
        self.assertEqual([f["line"] for f in self.findings("a.css") if f["rule"] == "outline-none"], [5, 6])

    def test_js_private_fields_are_not_comments(self):
        self.write("a.ts", "class A {\n  #html = el.innerHTML = x\n}\n/**\n * eval(x)\n */\n")
        self.assertEqual([(f["rule"], f["line"]) for f in self.findings("a.ts")], [("dangerous-html", 2)])

    def test_single_line_bundle_is_fast(self):
        self.write("app.js", "<img " * 40000)  # 200 KB, one line
        self.write("big.js", "var a=1;" * 25000 + "\neval(x)\n")  # minified file that is not named like one
        start = time.perf_counter()
        self.findings()
        self.assertLess(time.perf_counter() - start, 1.0)

    def test_long_kotlin_line_is_fast_and_short_lines_still_scanned(self):
        self.write("Main.kt", "val a = 1\n" * 50 + "putString " * 2000 + "\nprefs.edit().putString(\"token\", t)\n" + "val b = 2\n" * 50)
        start = time.perf_counter()
        found = self.findings("Main.kt")
        self.assertLess(time.perf_counter() - start, 1.0)
        self.assertEqual([(f["rule"], f["line"]) for f in found], [("android-prefs-token", 52)])

    def test_many_long_lines_with_unclosed_tags_are_fast(self):
        self.write("a.tsx", ("<img <div <input " * 110 + "\n") * 100)
        self.write("b.kt", ("putString " * 190 + "\n") * 100)
        start = time.perf_counter()
        self.findings()
        self.assertLess(time.perf_counter() - start, 1.5)

    def test_minified_and_bundle_names_are_skipped(self):
        for name in ("vendor.min.js", "app.bundle.js", "main.chunk.js", "chunk-ABC123.js"):
            self.write(name, "eval(x)\n")
        self.assertEqual(self.findings(), [])

    def test_secret_value_is_masked(self):
        secret = "sk_live_" + "A1b2C3d4E5f6G7h8I9j0"
        self.write("src/config.ts", f"export const apiKey = '{secret}'\n")
        hits = [f for f in self.findings() if f["rule"] == "hardcoded-secret"]
        self.assertEqual(len(hits), 1)
        self.assertNotIn(secret, hits[0]["snippet"])
        self.assertIn("'sk_l****'", hits[0]["snippet"])

    def test_root_tests_dir_is_a_test_dir(self):
        self.write("tests/a.test-helper.ts", "console.log(x)\n")
        self.write("src/a.ts", "console.log(x)\n")
        self.assertEqual([f["file"] for f in self.findings() if f["rule"] == "console-log"], ["src/a.ts"])

    def test_line_numbers_ignore_form_feed_and_line_separator(self):
        self.write("a.js", "var a = 1\f\nvar b = '\u2028'\r\nconsole.log(a)\n")
        self.assertEqual([f["line"] for f in self.findings("a.js")], [3])

    def test_symlinked_file_is_skipped(self):
        target = self.write("outside/real.js", "eval(x)\n")
        (self.root / "src").mkdir()
        try:
            os.symlink(target, self.root / "src" / "link.js")
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"cannot create symlinks here: {exc}")
        self.assertEqual([f["file"] for f in self.findings()], ["outside/real.js"])

    def test_package_json_with_bom_null_deps_or_array(self):
        (self.root / "package.json").write_bytes(
            b"\xef\xbb\xbf" + json.dumps({"dependencies": None, "devDependencies": {"react": "x"}}).encode())
        pkg = audit_scan.scan_package(self.root)
        self.assertEqual(pkg["frameworks"], ["react"])
        self.assertEqual(pkg["dependency_count"], {"prod": 0, "dev": 1})
        (self.root / "package.json").write_text("[1, 2]", encoding="utf-8")
        self.assertIn("error", audit_scan.scan_package(self.root))

    def test_max_must_be_positive(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
            audit_scan.main([str(self.root), "--max", "-1"])
        self.assertEqual(cm.exception.code, 2)


class CliValidationTest(unittest.TestCase):
    def test_search_limit_must_be_positive(self):
        for bad in ("-1", "0", "x"):
            with self.subTest(limit=bad), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                run_cli(search, ["--domain", "styles", "playful", "--limit", bad])
            self.assertEqual(cm.exception.code, 2)

    def test_search_no_results_exit_code_matches_in_json(self):
        code, out = run_cli(search, ["--domain", "styles", "zzqxv"])
        self.assertEqual(code, 1)
        code, out = run_cli(search, ["--domain", "styles", "zzqxv", "--json"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out), [])

    def test_budget_lcp_is_rounded(self):
        self.assertEqual(budget.build(dict(fsd_core.by_id("product-types.csv")["dashboard"], lcp_s="2.3"))["core_web_vitals_p75"]["lcp_ms"], 2300)


if __name__ == "__main__":
    unittest.main()
