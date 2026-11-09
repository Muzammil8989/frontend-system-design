'use strict';

/**
 * Idempotent file writer.
 *   { path, content }         → standalone file (kept if locally modified unless --force)
 *   { path, block, heading }  → managed block inside a shared file (AGENTS.md, GEMINI.md, …)
 */

const fs = require('fs');
const path = require('path');
const { NPX, read } = require('./util');

const BLOCK_START = `<!-- fsd:start — managed by \`${NPX} install\`; edits inside this block are overwritten -->`;
const BLOCK_END = '<!-- fsd:end -->';
const BLOCK_RE = /<!-- fsd:start[\s\S]*?<!-- fsd:end -->/;

const normalize = (s) => s.replace(/\r\n/g, '\n').trimEnd() + '\n';

/**
 * A symlink at a target path (e.g. planted in an untrusted repo) must not redirect our write elsewhere.
 * Links that resolve inside root (like AGENTS.md → CLAUDE.md) are fine; dangling or outside-root links are refused.
 */
function unsafeLink(root, abs) {
  let st;
  try {
    st = fs.lstatSync(abs);
  } catch {
    return null; // does not exist yet
  }
  if (!st.isSymbolicLink()) return null;
  let target;
  try {
    target = fs.realpathSync(abs);
  } catch {
    return 'dangling symlink';
  }
  const base = fs.realpathSync(root);
  const relative = path.relative(base, target);
  return relative.startsWith('..') || path.isAbsolute(relative) ? `symlink to ${target}, outside ${base}` : null;
}

function writeOutput(root, out, { force = false, dryRun = false } = {}) {
  const abs = path.join(root, out.path);
  const reason = unsafeLink(root, abs);
  if (reason) return { path: out.path, action: 'refused', reason };
  const exists = fs.existsSync(abs);
  let next;
  let action;

  if (out.block !== undefined) {
    const block = `${BLOCK_START}\n${out.block.trim()}\n${BLOCK_END}`;
    if (!exists) {
      next = `${out.heading}\n\n${block}\n`;
      action = 'created';
    } else {
      const current = read(abs);
      const hasBlock = BLOCK_RE.test(current);
      next = hasBlock ? current.replace(BLOCK_RE, () => block) : `${current.trimEnd()}\n\n${block}\n`;
      if (normalize(next) === normalize(current)) return { path: out.path, action: 'unchanged' };
      action = hasBlock ? 'updated' : 'appended';
    }
  } else {
    next = out.content;
    if (exists) {
      if (normalize(read(abs)) === normalize(next)) return { path: out.path, action: 'unchanged' };
      if (!force) return { path: out.path, action: 'skipped' };
      action = 'overwritten';
    } else {
      action = 'created';
    }
  }

  if (!dryRun) {
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, normalize(next));
  }
  return { path: out.path, action, dryRun };
}

module.exports = { writeOutput, normalize, BLOCK_START, BLOCK_END };
