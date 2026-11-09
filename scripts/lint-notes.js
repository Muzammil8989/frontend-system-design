#!/usr/bin/env node
'use strict';

/**
 * Note linter — zero dependencies.
 *
 * Checks every note in notes/<NN-phase>/ (or the files passed as arguments) against
 * the structure defined in notes/_TEMPLATE.md, then checks that README.md is in
 * sync with the notes on disk (✅ rows, Progress table, progress badge).
 *
 * Usage:
 *   node scripts/lint-notes.js                                 # lint all notes + README sync
 *   node scripts/lint-notes.js notes/03-state-and-data/foo.md  # lint specific notes (+ README sync)
 *   node scripts/lint-notes.js --no-readme     # skip README sync checks
 *   node scripts/lint-notes.js --json          # machine-readable output
 */

const fs = require('fs');
const path = require('path');

const REQUIRED_SECTIONS = [
  { prefix: 'ELI5', label: 'ELI5 — Simple Explanation' },
  { prefix: 'Core Concept', label: 'Core Concept — Step by Step' },
  { prefix: 'Real-World Examples', label: 'Real-World Examples' },
  { prefix: 'Key Points Summary', label: 'Key Points Summary' },
  { prefix: 'Test Your Understanding', label: 'Test Your Understanding' },
  { prefix: 'Cheat Sheet', label: 'Cheat Sheet' },
  { prefix: 'References', label: 'References & Further Reading' },
];

const REQUIRED_META = ['Date', 'Category', 'Sub-Topic', 'Level'];
const MIN_QUIZ_ANSWERS = 3;
const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*\.md$/;
const PLACEHOLDERS = [
  { re: /YYYY-MM-DD/, msg: 'template date placeholder "YYYY-MM-DD" not replaced' },
  { re: /<Topic Title>/, msg: 'template title placeholder "<Topic Title>" not replaced' },
  { re: /\]\(https:\/\/example\.com\)/, msg: 'template link placeholder "https://example.com" not replaced' },
  { re: /\]\(\.\/(previous|next)-topic\.md\)/, msg: 'template prev/next link placeholder not replaced' },
];

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

/** Splits a markdown file into lines and marks which lines are inside fenced code. */
function scan(text) {
  const lines = text.split(/\r?\n/);
  const inCode = new Array(lines.length).fill(false);
  let fence = null; // { char, len, line }
  const fences = [];
  lines.forEach((line, i) => {
    const m = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      inCode[i] = true;
      if (m && m[1][0] === fence.char && m[1].length >= fence.len && m[2].trim() === '') {
        fence = null;
      }
    } else if (m) {
      inCode[i] = true;
      fence = { char: m[1][0], len: m[1].length, line: i + 1, info: m[2].trim() };
      fences.push(fence);
    }
  });
  return { lines, inCode, unclosedFence: fence, fences };
}

/** GitHub-style heading slug (close enough for anchor validation). */
function githubSlug(heading) {
  return heading
    .trim()
    .toLowerCase()
    .replace(/<[^>]+>/g, '')
    .replace(/[`*_~]/g, (c) => (c === '_' ? '_' : ''))
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[^\p{L}\p{N}\s_-]/gu, '')
    .replace(/ /g, '-');
}

function collectAnchors(scanned) {
  const anchors = new Set();
  const seen = new Map();
  scanned.lines.forEach((line, i) => {
    if (scanned.inCode[i]) return;
    const m = line.match(/^#{1,6}\s+(.+?)\s*#*\s*$/);
    if (!m) return;
    const base = githubSlug(m[1]);
    const n = seen.get(base) || 0;
    anchors.add(n === 0 ? base : `${base}-${n}`);
    seen.set(base, n + 1);
  });
  return anchors;
}

/* ------------------------------------------------------------------ */
/* Per-note checks                                                     */
/* ------------------------------------------------------------------ */

function lintNote(absFile, root) {
  const rel = path.relative(root, absFile).split(path.sep).join('/');
  const problems = [];
  const report = (line, severity, rule, message) =>
    problems.push({ file: rel, line, severity, rule, message });

  const base = path.basename(absFile);
  if (!SLUG_RE.test(base)) {
    report(1, 'error', 'slug', `file name "${base}" must be lower-case and hyphenated (e.g. dom-and-virtual-dom.md)`);
  }

  const text = fs.readFileSync(absFile, 'utf8');
  const sc = scan(text);
  const { lines, inCode } = sc;

  // Title
  const firstContent = lines.findIndex((l) => l.trim() !== '');
  if (firstContent === -1 || !/^# \S/.test(lines[firstContent])) {
    report(firstContent + 1 || 1, 'error', 'title', 'note must start with a single "# Title" heading');
  }
  const h1s = lines.filter((l, i) => !inCode[i] && /^# \S/.test(l));
  if (h1s.length > 1) report(1, 'warning', 'title', `found ${h1s.length} H1 headings; use one H1 and H2/H3 for sections`);

  // Metadata header (must appear in the first 15 lines)
  const head = lines.slice(0, 15).join('\n');
  for (const key of REQUIRED_META) {
    if (!new RegExp(`\\*\\*${key}:\\*\\*`).test(head)) {
      report(3, 'error', 'metadata', `missing "**${key}:**" in the metadata block at the top of the note`);
    }
  }
  const dateMatch = head.match(/\*\*Date:\*\*\s*(\S+)/);
  if (dateMatch && !/^\d{4}-\d{2}-\d{2}$/.test(dateMatch[1]) && dateMatch[1] !== 'YYYY-MM-DD') {
    report(3, 'error', 'metadata', `Date "${dateMatch[1]}" must use ISO format YYYY-MM-DD`);
  }

  // Template placeholders
  lines.forEach((line, i) => {
    for (const p of PLACEHOLDERS) if (p.re.test(line)) report(i + 1, 'error', 'placeholder', p.msg);
  });

  // Code fences
  if (sc.unclosedFence) {
    report(sc.unclosedFence.line, 'error', 'code-fence', 'code fence is never closed');
  }
  sc.fences.forEach((f) => {
    if (f.info === '' && f !== sc.unclosedFence) {
      report(f.line, 'warning', 'code-fence', 'code fence has no language (use ```javascript, ```mermaid, ```text, ...)');
    }
  });

  // Required sections (H2, in order)
  const h2 = [];
  lines.forEach((line, i) => {
    if (!inCode[i]) {
      const m = line.match(/^## (.+)$/);
      if (m) h2.push({ text: m[1].trim(), line: i + 1 });
    }
  });
  let lastIdx = -1;
  for (const sec of REQUIRED_SECTIONS) {
    const idx = h2.findIndex((h) => h.text.startsWith(sec.prefix));
    if (idx === -1) {
      report(1, 'error', 'sections', `missing required section "## ${sec.label}"`);
      continue;
    }
    if (idx < lastIdx) {
      report(h2[idx].line, 'warning', 'sections', `section "## ${sec.label}" is out of template order`);
    }
    lastIdx = Math.max(lastIdx, idx);
  }

  // Empty sections
  h2.forEach((h, n) => {
    const start = h.line; // 1-based line of heading → index start
    const end = n + 1 < h2.length ? h2[n + 1].line - 1 : lines.length;
    const body = lines.slice(start, end).filter((l) => l.trim() && !/^-{3,}$/.test(l.trim()));
    if (body.length === 0) report(h.line, 'error', 'sections', `section "## ${h.text}" is empty`);
  });

  // <details>/<summary> balance (outside code)
  const count = (re) => lines.reduce((n, l, i) => n + (inCode[i] ? 0 : (l.match(re) || []).length), 0);
  const counts = {
    detailsOpen: count(/<details\b[^>]*>/g),
    detailsClose: count(/<\/details>/g),
    summaryOpen: count(/<summary\b[^>]*>/g),
    summaryClose: count(/<\/summary>/g),
  };
  if (counts.detailsOpen !== counts.detailsClose) {
    report(1, 'error', 'details', `unbalanced <details>: ${counts.detailsOpen} opened, ${counts.detailsClose} closed`);
  }
  if (counts.summaryOpen !== counts.summaryClose) {
    report(1, 'error', 'details', `unbalanced <summary>: ${counts.summaryOpen} opened, ${counts.summaryClose} closed`);
  }

  // Quiz answers inside "Test Your Understanding"
  const quiz = h2.findIndex((h) => h.text.startsWith('Test Your Understanding'));
  if (quiz !== -1) {
    const start = h2[quiz].line;
    const end = quiz + 1 < h2.length ? h2[quiz + 1].line - 1 : lines.length;
    const answers = lines.slice(start, end).filter((l, j) => !inCode[start + j] && /<details\b/.test(l)).length;
    if (answers < MIN_QUIZ_ANSWERS) {
      report(h2[quiz].line, 'error', 'quiz', `quiz needs at least ${MIN_QUIZ_ANSWERS} questions with collapsible <details> answers (found ${answers})`);
    }
  }

  // Links: relative files must exist; same-file anchors should exist
  const anchors = collectAnchors(sc);
  const linkRe = /!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)/g;
  lines.forEach((line, i) => {
    if (inCode[i]) return;
    const stripped = line.replace(/`[^`]*`/g, '');
    let m;
    while ((m = linkRe.exec(stripped))) {
      const target = m[1];
      if (/^[a-z][a-z0-9+.-]*:/i.test(target)) continue; // http:, https:, mailto:, ...
      if (target.startsWith('#')) {
        const anchor = decodeURIComponent(target.slice(1)).toLowerCase();
        if (anchor && !anchors.has(anchor)) {
          report(i + 1, 'warning', 'anchor', `anchor "${target}" does not match any heading in this note`);
        }
        continue;
      }
      const filePart = decodeURIComponent(target.split('#')[0]);
      if (!filePart) continue;
      const resolved = path.resolve(path.dirname(absFile), filePart);
      if (!fs.existsSync(resolved)) {
        report(i + 1, 'error', 'link', `relative link "${target}" points to a file that does not exist`);
      }
    }
  });

  // Diagrams
  const mermaid = sc.fences.filter((f) => f.info.startsWith('mermaid')).length;
  if (mermaid === 0) report(1, 'warning', 'diagram', 'no Mermaid diagram found; every note should have at least one');

  return problems;
}

/* ------------------------------------------------------------------ */
/* README sync checks                                                  */
/* ------------------------------------------------------------------ */

function lintReadme(root, noteFiles) {
  const problems = [];
  const readmePath = path.join(root, 'README.md');
  const report = (line, severity, rule, message) =>
    problems.push({ file: 'README.md', line, severity, rule, message });

  if (!fs.existsSync(readmePath)) {
    report(1, 'error', 'readme', 'README.md not found');
    return problems;
  }
  const lines = fs.readFileSync(readmePath, 'utf8').split(/\r?\n/);

  // Roadmap rows: | 4 | ✅ [Title](./notes/01-web-fundamentals/x.md) | Category |
  const linked = new Map(); // note path -> line
  const perPhase = new Map(); // phase number -> done count
  let phase = null;
  lines.forEach((line, i) => {
    const ph = line.match(/^## Phase (\d+)\b/);
    if (ph) {
      phase = Number(ph[1]);
      perPhase.set(phase, 0);
      return;
    }
    if (/^## /.test(line)) phase = null;
    if (phase === null || !line.startsWith('|')) return;
    if (line.includes('✅')) {
      perPhase.set(phase, perPhase.get(phase) + 1);
      const m = line.match(/✅\s*\[[^\]]+\]\(\.?\/?(notes\/[^)#\s]+)\)/);
      if (!m) {
        report(i + 1, 'error', 'readme', 'completed (✅) roadmap row must link to its note, e.g. ✅ [Title](./notes/<NN-phase>/slug.md)');
      } else {
        linked.set(m[1], i + 1);
        if (!fs.existsSync(path.join(root, m[1]))) {
          report(i + 1, 'error', 'readme', `roadmap links to "${m[1]}" which does not exist`);
        }
      }
    } else if (/\]\(\.?\/?notes\//.test(line)) {
      report(i + 1, 'warning', 'readme', 'row links to a note but is not marked ✅');
    }
  });

  // Every note must be listed as ✅
  for (const abs of noteFiles) {
    const rel = path.relative(root, abs).split(path.sep).join('/');
    if (!linked.has(rel)) {
      report(1, 'error', 'readme', `"${rel}" is not linked as ✅ in the README roadmap`);
    }
  }

  // Progress table: | 1 · Web Fundamentals | 4 | 14 |  and  | **Total** | **4** | **120** |
  let doneTotal = 0;
  perPhase.forEach((n) => (doneTotal += n));
  lines.forEach((line, i) => {
    const row = line.match(/^\|\s*(\d+)\s*·[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|/);
    if (row) {
      const p = Number(row[1]);
      const done = Number(row[2]);
      if (perPhase.has(p) && perPhase.get(p) !== done) {
        report(i + 1, 'error', 'progress', `Progress table says phase ${p} has ${done} done, roadmap shows ${perPhase.get(p)} ✅`);
      }
    }
    const tot = line.match(/^\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|/);
    if (tot && Number(tot[1]) !== doneTotal) {
      report(i + 1, 'error', 'progress', `Progress total says ${tot[1]} done, roadmap shows ${doneTotal} ✅`);
    }
    const badge = line.match(/badge\/progress-(\d+)%2F(\d+)/);
    if (badge && Number(badge[1]) !== doneTotal) {
      report(i + 1, 'error', 'progress', `progress badge says ${badge[1]}, roadmap shows ${doneTotal} ✅`);
    }
  });

  return problems;
}

/* ------------------------------------------------------------------ */
/* Runner                                                              */
/* ------------------------------------------------------------------ */

/** Notes live in one folder per roadmap phase: notes/<NN-phase>/<slug>.md. */
function listNotes(root) {
  const dir = path.join(root, 'notes');
  if (!fs.existsSync(dir)) return [];
  const isNote = (f) => f.endsWith('.md') && !f.startsWith('_') && f !== 'README.md';
  const out = fs.readdirSync(dir).filter(isNote).map((f) => path.join(dir, f));
  for (const d of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!d.isDirectory()) continue;
    const sub = path.join(dir, d.name);
    out.push(...fs.readdirSync(sub).filter(isNote).map((f) => path.join(sub, f)));
  }
  return out.sort();
}

function run({ root = process.cwd(), files = [], readme = true, json = false } = {}) {
  const all = listNotes(root);
  const targets = files.length
    ? files.map((f) => path.resolve(root, f)).filter((f) => !path.basename(f).startsWith('_'))
    : all;

  const problems = [];
  for (const f of targets) {
    if (!fs.existsSync(f)) {
      problems.push({ file: path.relative(root, f), line: 1, severity: 'error', rule: 'file', message: 'file not found' });
      continue;
    }
    problems.push(...lintNote(f, root));
  }
  if (readme) problems.push(...lintReadme(root, all));

  const errors = problems.filter((p) => p.severity === 'error').length;
  const warnings = problems.length - errors;

  if (json) {
    process.stdout.write(JSON.stringify({ errors, warnings, problems }, null, 2) + '\n');
    return errors ? 1 : 0;
  }

  const color = process.stdout.isTTY && !process.env.NO_COLOR;
  const c = (code, s) => (color ? `\x1b[${code}m${s}\x1b[0m` : s);
  const github = process.env.GITHUB_ACTIONS === 'true';

  for (const p of problems) {
    const sev = p.severity === 'error' ? c(31, 'error  ') : c(33, 'warning');
    console.log(`${c(2, `${p.file}:${p.line}`)}  ${sev}  ${p.message}  ${c(2, `(${p.rule})`)}`);
    if (github) {
      const level = p.severity === 'error' ? 'error' : 'warning';
      console.log(`::${level} file=${p.file},line=${p.line},title=notes/${p.rule}::${p.message}`);
    }
  }

  const summary = `${targets.length} note(s) checked — ${errors} error(s), ${warnings} warning(s)`;
  console.log(errors ? c(31, `\n✖ ${summary}`) : c(32, `\n✔ ${summary}`));
  return errors ? 1 : 0;
}

module.exports = { run, lintNote, lintReadme };

if (require.main === module) {
  const args = process.argv.slice(2);
  const files = args.filter((a) => !a.startsWith('--'));
  process.exitCode = run({
    files,
    readme: !args.includes('--no-readme'),
    json: args.includes('--json'),
  });
}
