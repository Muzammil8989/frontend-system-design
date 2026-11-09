# Frontend audit rubric (100 points)

Score an existing frontend: a codebase, a URL, or both. Base every finding on evidence:
- a `file:line`;
- a measured metric, with a note saying whether it is lab or field data;
- or a screenshot description.

Facts come from `scripts/audit_scan.py`. Judgement comes from reading the code and using the product.

| # | Area | Points | Full marks means |
|---|---|---:|---|
| 1 | **Architecture fit** | 15 | Rendering strategy fits each route. State is split correctly: server, URL, form, local, global. No fetch waterfalls. Clear module boundaries |
| 2 | **Performance** | 15 | Core Web Vitals good at p75, or lab proxies within budget. JS within budget, code-split, images and fonts optimized, sensible caching |
| 3 | **UI consistency and visual quality** | 15 | Tokens are used everywhere (few hard-coded values). Clear hierarchy, consistent spacing and type scale, coherent visual direction |
| 4 | **UX and states** | 10 | Primary actions are clear. Empty, loading, error, offline and success states are designed. Forms are forgiving. Copy is clear |
| 5 | **Accessibility** | 15 | Semantic HTML, keyboard operable, visible focus, contrast passes, labelled controls, correct ARIA patterns, reduced motion respected |
| 6 | **Security** | 10 | No unsafe HTML sinks. Tokens are not in Web Storage. CSP and security headers are present. Dependencies are maintained. No secrets in the bundle |
| 7 | **Responsiveness and cross-browser** | 5 | Works from 320 px to wide screens, with touch targets, safe areas, and Safari and Firefox parity |
| 8 | **Code quality and DX** | 10 | TypeScript strict, lint clean, consistent component APIs, a documented design system, reasonable dependency count |
| 9 | **Testing and observability** | 5 | Meaningful component and integration tests, e2e coverage of critical journeys, error tracking, and RUM |

**Mobile & desktop apps:** use the same 9 areas and read them as follows.
- **Performance:** cold start, frame time and jank, app size, memory, battery (`budget.py --platform mobile|desktop`).
- **Responsiveness:** device sizes, orientation, dynamic type, safe areas, tablet and foldable layouts.
- **Accessibility:** VoiceOver and TalkBack labels, traits and roles, 44 pt / 48 dp targets, focus order.
- **Security:** Keychain/Keystore for secrets, no secrets in the binary, deep-link validation, and Electron/Tauri hardening on desktop.
- **Architecture fit:** offline and sync, navigation and back behaviour, platform conventions (HIG / Material 3).

Run `detect_stack.py` first and judge against the matching `references/stacks/<stack>.md`.

**Grades:** 90–100 excellent · 75–89 good · 60–74 needs work · < 60 at risk.

A finding is a **blocker** regardless of the score if it is any of these:
- an XSS sink with user data;
- tokens in `localStorage`;
- a keyboard trap or a core journey that can't be completed by keyboard;
- Core Web Vitals "poor" on the main landing route;
- secrets in the client bundle.

## Report format

```markdown
## Frontend audit: <project>

**Score:** NN/100 (<grade>) · **Blockers:** N · **Scope:** <routes/files reviewed> · **Evidence:** static scan + code review [+ Lighthouse mobile lab / CrUX field]

### Scorecard
| Area | Score | Summary |
|---|---:|---|
| Architecture fit | x/15 | … |
| Performance | x/15 | … |
| UI consistency & visual quality | x/15 | … |
| UX & states | x/10 | … |
| Accessibility | x/15 | … |
| Security | x/10 | … |
| Responsiveness & cross-browser | x/5 | … |
| Code quality & DX | x/10 | … |
| Testing & observability | x/5 | … |

### Blockers
1. `path/file.tsx:42`: **[security]** what's wrong → impact → **Fix:** concrete change (code if short)

### Top improvements (ranked by impact ÷ effort)
| # | Finding | Evidence | Impact | Effort | Fix |
|---|---|---|---|---|---|

### Quick wins (< 1 hour each)
- …

### What's working well
- 2–4 specific strengths worth keeping
```

Rules:
- Merge repeated issues into one finding and list the locations.
- Give concrete fixes, not "consider improving".
- Keep the report under about 120 lines.
- The audit is read-only. Apply fixes only after the user agrees.
