"""Tests for scripts/tokens_check.py (stdlib unittest).

Run:  python -m unittest discover -s tests/python -v
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "frontend-system-design"
sys.path.insert(0, str(SKILL / "scripts"))

import tokens_check  # noqa: E402

EXAMPLE = SKILL / "references" / "templates" / "tokens.example.json"


def mode(**roles):
    return {"$type": "color", **{k: {"$value": v} for k, v in roles.items()}}


class TokensCheckTest(unittest.TestCase):
    def test_example_file_passes(self):
        report = tokens_check.check(json.loads(EXAMPLE.read_text(encoding="utf-8")))
        self.assertTrue(report["ok"], report["errors"] + [r for r in report["contrast"] if r["status"] != "pass"])
        self.assertEqual({r["mode"] for r in report["contrast"]}, {"color.light", "color.dark"})
        self.assertEqual(report["type_scale"][0]["token"], "type.display")

    def test_aliases_resolve_inside_composites_and_types_inherit(self):
        data = {"font": {"$type": "fontFamily", "sans": {"$value": ["Inter", "sans-serif"]}},
                "type": {"$type": "typography", "body": {"$value": {
                    "fontFamily": "{font.sans}", "fontSize": "1rem", "fontWeight": 400, "lineHeight": 1.5}}}}
        report = tokens_check.check(data)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["type_scale"][0]["family"], "Inter")
        self.assertEqual(report["type_scale"][0]["px"], 16.0)

    def test_missing_alias_cycle_and_missing_type_are_errors(self):
        data = {"a": {"$type": "color", "x": {"$value": "{a.y}"}, "y": {"$value": "{a.x}"}, "z": {"$value": "{nope}"}},
                "untyped": {"$value": "4px"}}
        errors = " ".join(tokens_check.check(data)["errors"])
        self.assertIn("cycle", errors)
        self.assertIn("{nope} points at no token", errors)
        self.assertIn("untyped: no $type", errors)

    def test_contrast_failures_fail_and_border_only_warns(self):
        data = {"color": {"light": mode(bg="#ffffff", text="#999999", primary="#2a4fc9", **{"on-primary": "#ffffff"}, border="#dddddd")}}
        report = tokens_check.check(data)
        status = {(r["fg"], r["bg"]): r["status"] for r in report["contrast"]}
        self.assertEqual(status[("text", "bg")], "fail")
        self.assertEqual(status[("on-primary", "primary")], "pass")
        self.assertEqual(status[("border", "bg")], "warn")
        self.assertFalse(report["ok"])

    def test_bad_dimension_and_typography_are_reported(self):
        data = {"space": {"$type": "dimension", "x": {"$value": "4 pixels"}},
                "type": {"$type": "typography", "h1": {"$value": {"fontSize": "2rem"}}}}
        errors = " ".join(tokens_check.check(data)["errors"])
        self.assertIn("space.x", errors)
        self.assertIn("missing fontFamily, fontWeight, lineHeight", errors)

    def test_cli_exit_codes_and_formats(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(tokens_check.main([str(EXAMPLE)]), 0)
        self.assertIn("### Contrast (WCAG 2.2)", buf.getvalue())
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "tokens.json"
            bad.write_text(json.dumps({"color": {"light": mode(bg="#ffffff", text="#cccccc")}}), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(tokens_check.main([str(bad), "--format", "json"]), 1)
            self.assertFalse(json.loads(buf.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
