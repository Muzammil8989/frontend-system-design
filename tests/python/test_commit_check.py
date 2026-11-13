"""Tests for the git-workflow commit message checker (stdlib unittest).

Run:  python -m unittest discover -s tests/python -v
"""

import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "git-workflow"
sys.path.insert(0, str(SKILL / "scripts"))

import commit_check  # noqa: E402


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = commit_check.main(argv)
        except SystemExit as exc:  # argparse usage errors
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def checks(message, **kw):
    return {i["check"] for i in commit_check.lint_message(message, **kw)["issues"]}


class HeaderTest(unittest.TestCase):
    def test_good_messages_pass_cleanly(self):
        for msg in (
            "feat(cli): add --companions all",
            "fix: keep users signed in after a token refresh",
            "docs(readme): explain the recommended install",
            "feat(api)!: require an API key\n\nBREAKING CHANGE: anonymous requests now get a 401.",
        ):
            res = commit_check.lint_message(msg)
            self.assertTrue(res["pass"], msg)
            self.assertGreaterEqual(res["score"], 90, msg)

    def test_parses_type_scope_and_breaking(self):
        res = commit_check.lint_message("feat(auth)!: drop legacy tokens")
        self.assertEqual((res["type"], res["scope"], res["breaking"]), ("feat", "auth", True))
        self.assertTrue(commit_check.lint_message("fix: x y\n\nBREAKING CHANGE: z")["breaking"])

    def test_not_conventional_fails(self):
        res = commit_check.lint_message("Added stuff.")
        self.assertFalse(res["pass"])
        self.assertTrue({"format", "imperative", "trailing-period"} <= checks("Added stuff."))

    def test_style_problems_are_flagged(self):
        self.assertIn("imperative", checks("fix: fixed the login bug"))
        self.assertIn("imperative", checks("feat: adding dark mode"))
        self.assertNotIn("imperative", checks("feat: embed the video player"))
        self.assertIn("type-case", checks("Feat: add x"))
        self.assertIn("type-unknown", checks("feature: add x"))
        self.assertIn("colon-space", checks("feat:add x"))
        self.assertIn("scope-empty", checks("feat(): add x"))
        self.assertIn("vague", checks("fix: fix bug"))
        self.assertIn("header-length", checks("feat: " + "a" * 80))
        self.assertFalse(commit_check.lint_message("feat: " + "word " * 25)["pass"])

    def test_repo_types_can_be_allowed(self):
        self.assertIn("type-unknown", checks("release: cut 2.0"))
        self.assertNotIn("type-unknown", checks("release: cut 2.0", extra_types=["release"]))

    def test_wip_and_autosquash_block_merging(self):
        self.assertFalse(commit_check.lint_message("wip")["pass"])
        self.assertIn("autosquash", checks("fixup! fix(auth): keep session"))
        self.assertFalse(commit_check.lint_message("fixup! fix(auth): keep session")["pass"])

    def test_git_generated_messages_are_skipped(self):
        for msg in ("Merge branch 'main' into feat/x", "Merge pull request #4 from a/b", 'Revert "feat: add x"'):
            res = commit_check.lint_message(msg)
            self.assertTrue(res["pass"])
            self.assertTrue(res["skipped"])


class BodyTest(unittest.TestCase):
    def test_blank_line_and_body_width(self):
        self.assertIn("blank-line", checks("fix: x y\nbody right away"))
        self.assertIn("body-length", checks("fix: x y\n\n" + "word " * 30))
        self.assertNotIn("body-length", checks("fix: x y\n\n    " + "x" * 150))
        self.assertNotIn("body-length", checks("fix: x y\n\nSee https://example.com/" + "a" * 120))

    def test_breaking_footer_must_be_exact(self):
        self.assertIn("breaking-footer", checks("fix: x y\n\nbreaking change: tokens rotate"))
        self.assertNotIn("breaking-footer", checks("fix: x y\n\nBREAKING CHANGE: tokens rotate"))
        self.assertIn("breaking-explain", checks("feat!: drop node 16"))

    def test_git_comments_and_scissors_are_ignored(self):
        msg = "fix: keep session\n\n# Please enter the commit message\n# ------------------------ >8 ------------------------\ndiff --git a b"
        self.assertEqual(commit_check.lint_message(msg)["issues"], [])


class VersionTest(unittest.TestCase):
    def test_bump_from_types(self):
        self.assertEqual(commit_check.bump_for("feat", False), "minor")
        self.assertEqual(commit_check.bump_for("fix", False), "patch")
        self.assertEqual(commit_check.bump_for("docs", False), "none")
        self.assertEqual(commit_check.bump_for("docs", True), "major")
        self.assertEqual(commit_check.bump_for(None, False), "none")

    def test_next_version(self):
        self.assertEqual(commit_check.next_version("v1.2.3", "major"), "v2.0.0")
        self.assertEqual(commit_check.next_version("1.2.3", "minor"), "1.3.0")
        self.assertEqual(commit_check.next_version("1.2.3", "patch"), "1.2.4")
        self.assertEqual(commit_check.next_version("0.4.1", "major"), "0.5.0")
        self.assertIsNone(commit_check.next_version("latest", "minor"))


class DataTest(unittest.TestCase):
    def test_commit_types_csv(self):
        types = commit_check.load_types()
        for t in ("feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore", "revert"):
            self.assertIn(t, types)
        for row in types.values():
            self.assertIn(row["semver_bump"], {"none", "patch", "minor", "major"})
            self.assertTrue(commit_check.lint_message(row["example"])["pass"], row["example"])

    def test_git_recipes_csv(self):
        with (SKILL / "data" / "git-recipes.csv").open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertGreaterEqual(len(rows), 25)
        for row in rows:
            self.assertIn(row["risk"], {"low", "medium", "high"}, row["problem"])
            self.assertIn(row["rewrites_history"], {"yes", "no"}, row["problem"])
            self.assertTrue(row["safest_fix"].strip(), row["problem"])
        problems = " ".join(r["problem"].lower() for r in rows)
        for topic in ("secret", "rebase", "deleted branch", "wrong branch", "pushed"):
            self.assertIn(topic, problems)


class CliTest(unittest.TestCase):
    def test_exit_codes_and_json(self):
        self.assertEqual(run_cli(["feat: add x"])[0], 0)
        self.assertEqual(run_cli(["Added stuff."])[0], 1)
        code, out, _ = run_cli(["fix(ui): keep focus in the dialog", "--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual((data["type"], data["scope"], data["bump"]), ("fix", "ui", "patch"))
        self.assertEqual(run_cli(["fix: fixed it", "--min-score", "100"])[0], 1)

    def test_file_input_and_bad_input(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "COMMIT_EDITMSG"
            f.write_text("docs: explain the release steps\n\n# comment\n", encoding="utf-8")
            self.assertEqual(run_cli(["--file", str(f)])[0], 0)
            self.assertEqual(run_cli(["--file", str(Path(d) / "missing")])[0], 2)
        self.assertEqual(run_cli(["   "])[0], 2)
        self.assertEqual(run_cli(["--suggest-bump", "feat: x"])[0], 2)
        self.assertEqual(run_cli(["--range", "--output=/tmp/x"])[0], 2)


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class RangeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name

        def git(*args):
            subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True)

        git("init", "-q")
        git("config", "user.email", "test@example.com")
        git("config", "user.name", "Test")
        git("config", "commit.gpgsign", "false")
        for msg in ("chore: start", "fix(api): handle empty pages", "feat(ui): add dark mode", "docs: update the readme"):
            git("commit", "-q", "--allow-empty", "-m", msg)
        git("tag", "v1.4.2", "HEAD~3")
        self.git = git

    def tearDown(self):
        self.tmp.cleanup()

    def test_range_report_and_bump(self):
        code, out, _ = run_cli(["--range", "v1.4.2..HEAD", "--repo", self.repo, "--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["checked"], 3)
        self.assertEqual(data["bump"], "minor")
        self.assertEqual(data["next_version"], "v1.5.0")
        code, out, _ = run_cli(["--range", "v1.4.2..HEAD", "--repo", self.repo, "--suggest-bump"])
        self.assertIn("Suggested bump: minor (v1.4.2 → v1.5.0)", out)

    def test_range_text_lists_only_commits_with_issues(self):
        self.git("commit", "-q", "--allow-empty", "-m", "fix: Fixed the footer")
        _, out, _ = run_cli(["--range", "v1.4.2..HEAD", "--repo", self.repo])
        self.assertIn("fix: Fixed the footer", out)
        self.assertNotIn("add dark mode", out)
        self.assertIn("3 clean or skipped not shown", out)
        _, out, _ = run_cli(["--range", "v1.4.2..HEAD", "--repo", self.repo, "--verbose"])
        self.assertIn("add dark mode", out)

    def test_range_fails_on_a_bad_commit(self):
        self.git("commit", "-q", "--allow-empty", "-m", "wip")
        self.assertEqual(run_cli(["--range", "v1.4.2..HEAD", "--repo", self.repo])[0], 1)

    def test_git_errors_exit_2(self):
        code, _, err = run_cli(["--range", "nope..HEAD", "--repo", self.repo])
        self.assertEqual(code, 2)
        self.assertIn("error", err)


if __name__ == "__main__":
    unittest.main()
