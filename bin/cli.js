#!/usr/bin/env node
'use strict';

/**
 * frontend-system-design CLI.
 *
 *   npx github:Muzammil8989/frontend-system-design install      # interactive wizard
 *   npx github:Muzammil8989/frontend-system-design install --all --yes
 *
 * Source lives in src/cli/ (index → install → wizard/detect/adapters/writer/companions).
 */

require('../src/cli/index.js').run();
