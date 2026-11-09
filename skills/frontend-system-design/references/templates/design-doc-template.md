# Design doc template

Copy this structure into the output and fill every section. Scale the depth to the product: a landing page fits on one page, a SaaS platform may run to several. Delete sections that genuinely don't apply, and say in one line why each one was dropped.

```markdown
# <Product> — Frontend System Design

**Author:** <agent/user> · **Date:** YYYY-MM-DD · **Status:** Draft | Approved
**Product type:** <type> · **Platform:** web | mobile | desktop | cross · **Stack:** <stack> · **Surfaces:** <marketing, app, admin, …>

## 1. Problem & summary
**The problem:** 2–3 lines on who has it, the job to be done, and what makes it hard.
**Closest system design case / playbook:** <case from knowledge/INDEX.md> → what we reuse, what differs.
**Summary:** 2–4 sentences on the headline decisions (platform, rendering/app model, stack, UI direction).

## 2. Requirements
### Core journeys
1. …
### Non-functional requirements
| Attribute | Target |
|---|---|
| Performance | LCP ≤ 2.5 s · INP ≤ 200 ms · CLS ≤ 0.1 (p75 mobile); JS ≤ N KB |
| Accessibility | WCAG 2.2 AA |
| SEO | … |
| Freshness / real-time | … |
| Offline | … |
| Browsers / devices | … |
### Assumptions & open questions
- …

## 3. Architecture
### High-level diagram
(Mermaid: client ↔ CDN/edge ↔ BFF/API ↔ services; real-time channel)
### Rendering per route
| Route / surface | Strategy | Why |
|---|---|---|
### Platform & stack
| Surface | Platform | Stack (see `references/stacks/<stack>.md`) | Why |
|---|---|---|---|
### Key decisions
| Decision | Options considered | Choice | Trade-off / revisit when | Why — learn more |
|---|---|---|---|---|
| Platform (native vs cross-platform) | | | | |
| Framework | | | | |
| State management | | | | |
| Data fetching / API / offline sync | | | | |
| Real-time | | | | |
| Styling / component library | | | | |
("Why — learn more" cites `references/knowledge/<note>.md` when a project note covers the topic.)
### Project folder structure
(feature-based tree tailored from the stack file, with one-line comments and the import-boundary rules)

## 4. Data model & API interface
- Client entities and normalization; cache keys; pagination; optimistic updates; error/retry policy
- Endpoint or query list for the core journeys

## 5. Component architecture
- Component tree for the 2–3 key screens
- API (props, events, slots) of the 3–5 most important components

## 6. UI system
- **Direction:** intent sentence · 3 adjectives · benchmark systems · signature element
- **Tokens:** color roles (light/dark, contrast verified), type scale + font pairing, spacing, radius, elevation, motion
- **Layout & navigation:** app shell / nav pattern, breakpoints
- **Key screens:** for each, the layout, primary action, and states (empty / loading / error / success / offline / permission)

## 7. Performance plan
- Budget table (from `budget.py`; `--platform mobile|desktop` for apps: cold start, frame time, size), LCP element per key route, hydration strategy, code-splitting, image/font strategy, caching headers

## 8. Accessibility plan
- Landmarks/headings, keyboard map, focus management for dialogs and route changes, complex widgets → APG pattern used, testing plan

## 9. Security plan
- Auth/session model, CSP, XSS sinks avoided, CSRF, third-party scripts, secrets

## 10. Testing & observability
- Test pyramid per layer, critical e2e journeys, visual regression scope, RUM + error tracking + alerts

## 11. Rollout plan
| Phase | Scope | Exit criteria |
|---|---|---|
| 1 — Foundation | tokens, app shell, auth, CI with budgets | … |
| 2 — Core journeys | … | … |
| 3 — Polish & scale | … | … |

## 12. Risks & mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
```
