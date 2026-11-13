#!/usr/bin/env node
'use strict';

/** Runs the Python unittest suite with whichever interpreter exists (python3, python, or the Windows `py` launcher). */

const { spawnSync } = require('child_process');
const path = require('path');
const { ENV, findPython, notFoundMessage } = require('../src/cli/python');

const { exe } = findPython();
if (!exe) {
  console.error(`✖ ${notFoundMessage()}`);
  process.exit(1);
}
const args = ['-m', 'unittest', 'discover', '-s', path.join('tests', 'python'), '-v'];
const r = spawnSync(exe, args, { stdio: 'inherit', cwd: path.resolve(__dirname, '..'), env: ENV });
process.exit(r.status ?? 1);
