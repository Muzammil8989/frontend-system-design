'use strict';

/**
 * Finds a Python 3.9+ interpreter (python3, python, or the Windows `py` launcher) and runs the
 * skills' stdlib-only scripts with it. Used by the MCP server and by scripts/run-python-tests.js.
 */

const { spawn, spawnSync } = require('child_process');

const CANDIDATES = process.platform === 'win32' ? ['py', 'python', 'python3'] : ['python3', 'python'];
const VERSION_CHECK = ['-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'];
const ENV = { ...process.env, PYTHONDONTWRITEBYTECODE: '1', PYTHONIOENCODING: 'utf-8' };

let cached;

/** @returns {{ exe: string|null, tooOld: string[] }} the first usable interpreter (memoized). */
function findPython() {
  if (cached) return cached;
  const tooOld = [];
  for (const exe of CANDIDATES) {
    const probe = spawnSync(exe, ['--version'], { encoding: 'utf8' });
    if (probe.status !== 0) continue;
    if (spawnSync(exe, VERSION_CHECK, { encoding: 'utf8' }).status !== 0) {
      tooOld.push(`${exe} (${(probe.stdout || probe.stderr || '').trim() || 'unknown version'})`);
      continue;
    }
    return (cached = { exe, tooOld });
  }
  return (cached = { exe: null, tooOld });
}

function notFoundMessage() {
  const { tooOld } = findPython();
  const older = tooOld.length ? ` Found only older interpreters: ${tooOld.join(', ')}.` : '';
  return `Python 3.9+ not found (tried: ${CANDIDATES.join(', ')}).${older} Install it from https://www.python.org/downloads/`;
}

/**
 * Runs a script with an argument array (never a shell). Never passes -I: the frontend-system-design
 * scripts import fsd_core from their own folder, which -I would drop from sys.path.
 * @returns {Promise<{ code: number|null, stdout: string, stderr: string, timedOut: boolean }>}
 */
function runPython(script, args = [], { cwd, input, timeoutMs = 60000 } = {}) {
  const { exe } = findPython();
  if (!exe) return Promise.reject(new Error(notFoundMessage()));
  return new Promise((resolve, reject) => {
    const child = spawn(exe, [script, ...args], { cwd, env: ENV, windowsHide: true });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill();
    }, timeoutMs);
    child.stdout.setEncoding('utf8').on('data', (d) => (stdout += d));
    child.stderr.setEncoding('utf8').on('data', (d) => (stderr += d));
    child.on('error', (e) => {
      clearTimeout(timer);
      reject(e);
    });
    child.on('close', (code) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    });
    child.stdin.end(input === undefined ? '' : input);
  });
}

module.exports = { CANDIDATES, ENV, findPython, notFoundMessage, runPython };
