'use strict';

/** Shared constants and small helpers for the installer. */

const fs = require('fs');
const path = require('path');

const PKG_ROOT = path.resolve(__dirname, '..', '..');
const PKG = JSON.parse(fs.readFileSync(path.join(PKG_ROOT, 'package.json'), 'utf8'));
const REPO = 'Muzammil8989/frontend-system-design';
const REPO_URL = `https://github.com/${REPO}`;
const NPX = `npx github:${REPO}`;
const SHARED_SKILLS_DIR = '.agents/skills';

/* ---------- terminal colors (respect NO_COLOR and non-TTY) ---------- */

const useColor = process.stdout.isTTY && !process.env.NO_COLOR;
const paint = (code) => (s) => (useColor ? `\x1b[${code}m${s}\x1b[0m` : String(s));
const c = { bold: paint(1), dim: paint(2), red: paint(31), green: paint(32), yellow: paint(33), cyan: paint(36), magenta: paint(35) };

class CliError extends Error {}
const fail = (message) => {
  throw new CliError(message);
};

/* ---------- file helpers ---------- */

const read = (abs) => fs.readFileSync(abs, 'utf8').replace(/\r\n/g, '\n');

function splitFrontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { meta: {}, raw: '', body: text };
  const meta = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([\w-]+):\s*(.*)$/);
    if (kv) meta[kv[1]] = kv[2].replace(/^["']|["']$/g, '');
  }
  return { meta, raw: m[0], body: text.slice(m[0].length) };
}

/** Recursively lists files under dir (relative posix paths), skipping caches and dotfiles. */
function walk(dir, base = dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '__pycache__' || entry.name.endsWith('.pyc') || entry.name.startsWith('.')) continue;
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(abs, base));
    else out.push(path.relative(base, abs).split(path.sep).join('/'));
  }
  return out.sort();
}

const quote = (s) => JSON.stringify(s);
const withFrontmatter = (fields, body) =>
  `---\n${Object.entries(fields).map(([k, v]) => `${k}: ${v}`).join('\n')}\n---\n\n${body}`;

function versionGte(actual, required) {
  const a = actual.split('.').map(Number);
  const r = required.split('.').map(Number);
  for (let i = 0; i < 3; i++) if ((a[i] || 0) !== (r[i] || 0)) return (a[i] || 0) > (r[i] || 0);
  return true;
}

module.exports = {
  PKG_ROOT, PKG, REPO, REPO_URL, NPX, SHARED_SKILLS_DIR,
  c, CliError, fail, read, splitFrontmatter, walk, quote, withFrontmatter, versionGte,
};
