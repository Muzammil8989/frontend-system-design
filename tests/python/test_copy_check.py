"""Tests for the product-copywriting copy checker (stdlib unittest).

Run:  python -m unittest discover -s tests/python -v
"""

import csv
import io
import json
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "product-copywriting"
sys.path.insert(0, str(SKILL / "scripts"))

import copy_check  # noqa: E402

AI_PARAGRAPH = (
    "In today's fast-paced world, our cutting-edge platform empowers you to unlock seamless "
    "productivity and elevate your workflow. Whether you're a startup or an enterprise, look no further."
)
HUMAN_PARAGRAPH = (
    "Invoices used to eat my Friday afternoons. Now they go out at 9am, and I get paid in 6 days "
    "instead of 30. Set it up once, then forget about it."
)


def run_cli(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = copy_check.main(argv)
    return code, buf.getvalue()


class ScoringTest(unittest.TestCase):
    def test_ai_paragraph_scores_low(self):
        result = copy_check.analyze(AI_PARAGRAPH)
        tells = [f for f in result["findings"] if f["check"] == "ai-tell"]
        self.assertLess(result["score"], 60)
        self.assertGreaterEqual(len(tells), 5)
        self.assertFalse(result["passed"])
        self.assertTrue(all(f["line"] == 1 for f in tells))

    def test_human_paragraph_scores_high(self):
        result = copy_check.analyze(HUMAN_PARAGRAPH)
        self.assertGreaterEqual(result["score"], 80)
        self.assertEqual(result["counts"]["high"], 0)

    def test_line_numbers_and_markdown_stripping(self):
        text = "# Title\n\n```\nleverage synergy delve\n```\n\nWe help you ship.\nIt is seamless.\n"
        result = copy_check.analyze(text, fmt="md")
        matches = {f["match"].lower(): f["line"] for f in result["findings"]}
        self.assertNotIn("leverage", matches)  # code block ignored
        self.assertEqual(matches.get("seamless"), 8)

    def test_html_is_stripped(self):
        html = "<html><body>\n<h1>Get paid faster</h1>\n<p>Our <b>robust</b> tool.</p>\n<script>var delve=1;</script></body></html>"
        result = copy_check.analyze(html, fmt="html")
        matches = {f["match"].lower(): f["line"] for f in result["findings"]}
        self.assertEqual(matches.get("robust"), 3)
        self.assertNotIn("delve", matches)

    def test_vague_claim_needs_number(self):
        flagged = copy_check.analyze("The world-class tool for teams.")
        backed = copy_check.analyze("Rated the best tool by 4,000 teams in 2025.")
        self.assertTrue(any(f["check"] == "vague-claim" for f in flagged["findings"]))
        self.assertFalse(any(f["check"] == "vague-claim" for f in backed["findings"]))


class DataIntegrityTest(unittest.TestCase):
    def test_ai_tells_csv(self):
        with (SKILL / "data" / "ai-tells.csv").open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            self.assertEqual(reader.fieldnames, ["phrase", "category", "severity", "suggestion"])
            rows = list(reader)
        self.assertGreaterEqual(len(rows), 80)
        phrases = [r["phrase"] for r in rows]
        self.assertEqual(len(phrases), len(set(phrases)), "duplicate phrases")
        for r in rows:
            self.assertIn(r["category"], copy_check.CATEGORIES, r["phrase"])
            self.assertIn(r["severity"], copy_check.SEVERITIES, r["phrase"])
            self.assertEqual(r["phrase"], r["phrase"].lower().strip(), r["phrase"])
            self.assertTrue(r["suggestion"].strip(), r["phrase"])

    def test_voice_archetypes_csv(self):
        with (SKILL / "data" / "voice-archetypes.csv").open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 8)
        self.assertEqual(len({r["id"] for r in rows}), 8)
        for r in rows:
            for col in ("id", "name", "keywords", "description", "do", "dont", "sample"):
                self.assertTrue(r[col].strip(), f"{r['id']}: empty {col}")

    def test_skill_md_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: product-copywriting\n"))
        desc = next(line for line in text.splitlines() if line.startswith("description:"))
        self.assertLess(len(desc[len("description:"):].strip()), 1024)
        for ref in ("story-frameworks", "human-writing", "voice-and-tone", "website-pages",
                    "app-copy", "microcopy"):
            self.assertTrue((SKILL / "references" / f"{ref}.md").is_file(), ref)


class CliTest(unittest.TestCase):
    def _write(self, text, suffix=".md"):
        tmp = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return tmp.name

    def test_json_output(self):
        path = self._write(AI_PARAGRAPH)
        code, out = run_cli(["--json", path])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertLess(data["score"], 60)
        self.assertIn("findings", data)
        self.assertIn("stats", data)

    def test_min_score_exit_code(self):
        bad, good = self._write(AI_PARAGRAPH), self._write(HUMAN_PARAGRAPH, ".txt")
        self.assertEqual(run_cli(["--min-score", "80", bad])[0], 1)
        self.assertEqual(run_cli(["--min-score", "80", good])[0], 0)

    def test_markdown_output(self):
        code, out = run_cli([self._write(AI_PARAGRAPH)])
        self.assertEqual(code, 0)
        self.assertIn("**Score:", out)
        self.assertIn("| Line | Severity |", out)

    def test_multiple_inputs_json(self):
        code, out = run_cli(["--json", self._write(AI_PARAGRAPH), self._write(HUMAN_PARAGRAPH)])
        self.assertEqual(len(json.loads(out)["results"]), 2)

    def test_bom_before_front_matter(self):
        tmp = tempfile.NamedTemporaryFile("wb", suffix=".md", delete=False)
        tmp.write(b"\xef\xbb\xbf---\ntitle: leverage synergy to delve\n---\nWe send the invoice at 9am.\n")
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        code, out = run_cli(["--json", tmp.name])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["stats"]["words"], 6, "front matter must be skipped")
        self.assertEqual(data["stats"]["ai_tells"], 0)

    def test_empty_input_exits_2(self):
        for text in ("", "  \n\n\t\n"):
            with self.subTest(text=text), redirect_stderr(io.StringIO()) as err:
                code, out = run_cli([self._write(text)])
            self.assertEqual(code, 2)
            self.assertEqual(out, "")
            self.assertIn("no copy found", err.getvalue())
        result = copy_check.analyze("   ")
        self.assertFalse(result["passed"])

    def test_limit_must_be_positive(self):
        for bad in ("-1", "0"):
            with self.subTest(limit=bad), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                run_cli(["--limit", bad, self._write(HUMAN_PARAGRAPH)])
            self.assertEqual(cm.exception.code, 2)


class PathologicalInputTest(unittest.TestCase):
    def test_many_abbreviations_are_fast(self):
        start = time.perf_counter()
        result = copy_check.analyze("e.g. " * 10000)  # 50 KB, one "sentence"
        self.assertLess(time.perf_counter() - start, 2.0)
        self.assertEqual(result["stats"]["sentences"], 1)

    def test_large_html_is_fast_and_lines_are_right(self):
        html = "<p>Our tool is robust.</p>\n" * 5000
        start = time.perf_counter()
        result = copy_check.analyze(html, fmt="html")
        self.assertLess(time.perf_counter() - start, 5.0)
        lines = [f["line"] for f in result["findings"] if f["match"].lower() == "robust"]
        self.assertEqual(lines[:3], [1, 2, 3])
        self.assertEqual(lines[-1], 5000)

    def test_abbreviations_still_detected(self):
        sentences = copy_check.split_sentences(copy_check.extract("Read the first chapter. Then the rest.")[0])
        self.assertEqual(len(sentences), 2)
        sentences = copy_check.split_sentences(copy_check.extract("Ask Dr. Smith, e.g. by email. Then go.")[0])
        self.assertEqual([str(x["text"]) for x in sentences], ["Ask Dr. Smith, e.g. by email.", "Then go."])

    def test_line_separators_do_not_shift_lines(self):
        result = copy_check.analyze("Intro\u2028text here.\fMore.\n\nIt is seamless.\n", fmt="md")
        matches = {f["match"].lower(): f["line"] for f in result["findings"]}
        self.assertEqual(matches.get("seamless"), 3)


if __name__ == "__main__":
    unittest.main()
