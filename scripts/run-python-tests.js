#!/usr/bin/env node
'use strict';

/** Runs the Python unittest suite with whichever interpreter exists (python3, python, or the Windows `py` launcher). */

const { spawnSync } = require('child_process');
const path = require('path');

const candidates = process.platform === 'win32' ? ['py', 'python', 'python3'] : ['python3', 'python'];
const args = ['-m', 'unittest', 'discover', '-s', path.join('tests', 'python'), '-v'];
const versionCheck = ['-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'];

const tooOld = [];
for (const exe of candidates) {
  const probe = spawnSync(exe, ['--version'], { encoding: 'utf8' });
  if (probe.status !== 0) continue;
  if (spawnSync(exe, versionCheck, { encoding: 'utf8' }).status !== 0) {
    tooOld.push(`${exe} (${(probe.stdout || probe.stderr || '').trim() || 'unknown version'})`);
    continue;
  }
  const r = spawnSync(exe, args, { stdio: 'inherit', cwd: path.resolve(__dirname, '..'), env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } });
  process.exit(r.status ?? 1);
}

const found = tooOld.length ? ` Found only older interpreters: ${tooOld.join(', ')}.` : '';
console.error('✖ Python 3.9+ not found (tried: ' + candidates.join(', ') + ').' + found + ' Install it from https://www.python.org/downloads/');
process.exit(1);
