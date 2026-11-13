'use strict';

/**
 * `install --hooks`: guardrails that enforce the git-workflow skill's rules instead of only advising them.
 *   - Claude Code: hooks/fsd-guard.js as a PreToolUse hook (merged into .claude/settings.json)
 *   - git: a commit-msg hook that runs commit_check.py (project only; never replaces someone else's hook)
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { NPX, PKG_ROOT, SHARED_SKILLS_DIR, read } = require('./util');

const GUARD = 'fsd-guard.js';
const MARKER = '# fsd-guard: managed';

/** settings.json merge: add or replace our PreToolUse entry; never touch anyone else's hooks. */
function mergeGuard(command) {
  return (cfg) => {
    if (cfg.hooks !== undefined && (typeof cfg.hooks !== 'object' || Array.isArray(cfg.hooks))) throw new Error('"hooks" is not an object; left untouched');
    cfg.hooks = cfg.hooks || {};
    const list = cfg.hooks.PreToolUse === undefined ? [] : cfg.hooks.PreToolUse;
    if (!Array.isArray(list)) throw new Error('"hooks.PreToolUse" is not an array; left untouched');
    const entry = { matcher: 'Bash', hooks: [{ type: 'command', command, timeout: 10 }] };
    const ours = (e) => e && Array.isArray(e.hooks) && e.hooks.some((h) => String((h && h.command) || '').includes(GUARD));
    const i = list.findIndex(ours);
    if (i >= 0) list[i] = entry;
    else list.push(entry);
    cfg.hooks.PreToolUse = list;
    return cfg;
  };
}

/** Outputs for Claude Code (written relative to `root`: the project, or ~ with --global). */
function claudeHookOutputs({ global }) {
  const command = global
    ? `node "${path.join(os.homedir(), '.claude', 'hooks', GUARD).replace(/\\/g, '/')}"`
    : `node "\${CLAUDE_PROJECT_DIR}/.claude/hooks/${GUARD}"`;
  return [
    { path: `.claude/hooks/${GUARD}`, content: read(path.join(PKG_ROOT, 'hooks', GUARD)) },
    { path: '.claude/settings.json', json: mergeGuard(command) },
  ];
}

function commitMsgScript(scriptRel) {
  return `#!/bin/sh
${MARKER} by \`${NPX} install --hooks\`. Delete this file to remove it.
# Checks the commit message with the git-workflow skill (Conventional Commits). WIP and fixup! commits are allowed here;
# run commit_check.py --range before merging to catch them.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
script="$root/${scriptRel}"
[ -f "$script" ] || exit 0
for py in python3 py python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    exec "$py" "$script" --file "$1" --allow-wip
  fi
done
echo "fsd-guard: Python 3.9+ not found; commit message not checked." >&2
exit 0
`;
}

const git = (cwd, args) => execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();

/**
 * The git commit-msg hook, or a reason it was skipped (with the line to add by hand).
 * @returns {{ root: string, out: object } | { skip: string }}
 */
function commitMsgHook({ tools, skills, global }, projectRoot) {
  if (!skills.includes('git-workflow')) return { skip: 'the git-workflow skill is not being installed' };
  // Where the installed checker lives inside the project.
  let skillDir;
  if (tools.includes('claude') && !global) skillDir = '.claude/skills/git-workflow';
  else if (tools.some((t) => t !== 'claude')) skillDir = `${SHARED_SKILLS_DIR}/git-workflow`;
  else return { skip: 'with --global the checker lives outside this project; add the hook by hand if you want it' };

  let top;
  try {
    top = git(projectRoot, ['rev-parse', '--show-toplevel']);
  } catch {
    return { skip: 'not a git repository' };
  }
  const scriptRel = path.relative(top, path.join(projectRoot, skillDir, 'scripts', 'commit_check.py')).replace(/\\/g, '/');
  const manual = `python3 "${scriptRel}" --file "$1" --allow-wip`;
  let hooksPath = '';
  try {
    hooksPath = git(projectRoot, ['config', '--get', 'core.hooksPath']);
  } catch {
    /* not set */
  }
  if (hooksPath) return { skip: `core.hooksPath is set (${hooksPath}, e.g. husky or lefthook). Add this to its commit-msg hook: ${manual}` };

  const hooksDir = path.resolve(projectRoot, git(projectRoot, ['rev-parse', '--git-path', 'hooks']));
  const rel = path.relative(top, hooksDir);
  if (rel.startsWith('..') || path.isAbsolute(rel)) return { skip: `the hooks folder is outside the repo (${hooksDir}); add it by hand: ${manual}` };
  const hookAbs = path.join(hooksDir, 'commit-msg');
  if (fs.existsSync(hookAbs) && !read(hookAbs).includes(MARKER)) return { skip: `a commit-msg hook already exists; add this line to it: ${manual}` };
  return { root: top, out: { path: path.join(rel, 'commit-msg').replace(/\\/g, '/'), content: commitMsgScript(scriptRel), mode: 0o755 } };
}

module.exports = { claudeHookOutputs, commitMsgHook, mergeGuard, GUARD, MARKER };
