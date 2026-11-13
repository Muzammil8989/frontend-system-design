#!/usr/bin/env node
'use strict';

/**
 * frontend-system-design CLI.
 *
 *   npx frontend-system-design install      # interactive wizard
 *   npx frontend-system-design install --all                    # recommended: everything, no questions
 *   npx frontend-system-design install --all --no-companions    # our skills only
 *
 * Source lives in src/cli/ (index → install → wizard/detect/adapters/writer/companions).
 */

require('../src/cli/index.js').run();
