# Quality: accessibility, security, testing, observability, i18n

## Accessibility (target: WCAG 2.2 AA)

**Foundations**
- [ ] Semantic HTML first: `button`, `a`, `nav`, `main`, `header`, `form`, `label`, `table`. Use ARIA only where native semantics can't do the job.
- [ ] One `h1` per page and a logical heading order. Landmarks are present. A skip link goes to `main`.
- [ ] `<html lang>` is set, and each route has a descriptive `<title>`.
- [ ] Every interactive element is reachable and operable by keyboard, in a logical order, with no keyboard traps.
- [ ] There is a visible focus indicator. Focus is not hidden by sticky headers or footers (2.4.11, Focus Not Obscured).
- [ ] Touch and pointer targets are at least 24 × 24 CSS px (2.5.8 Target Size, Minimum).
- [ ] Contrast: text ≥ 4.5:1 (large text ≥ 3:1), UI components and graphics ≥ 3:1.
- [ ] Images have `alt`. Icons-only buttons have accessible names. SVG icons are decorative (`aria-hidden`) or labelled.
- [ ] Forms:
  - labels are tied to inputs;
  - errors are announced, linked with `aria-describedby`, and describe how to fix them;
  - users don't have to re-enter information they've already given (3.3.7, Redundant Entry);
  - authentication doesn't rely on a cognitive test alone (3.3.8, Accessible Authentication).
- [ ] Drag-and-drop has a single-pointer or keyboard alternative (2.5.7, Dragging Movements).
- [ ] Motion respects `prefers-reduced-motion`. No content flashes more than 3 times per second.
- [ ] Dynamic updates (toasts, live data, chat) use `aria-live` regions politely. Focus moves into dialogs and is restored when they close.
- [ ] The UI works at 200% zoom and reflows at 320 px width without horizontal scroll.

**Complex widgets:** follow the [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/) patterns (combobox, dialog, tabs, menu, tree, grid), or use React Aria, Radix, or Ark UI primitives.

**Testing:** axe-core in unit tests and e2e (`@axe-core/playwright`), plus a keyboard-only pass and a screen-reader pass (NVDA + Firefox/Chrome, VoiceOver + Safari) on the core journeys.

## Security

| Threat | Mitigation |
|---|---|
| XSS | Rely on framework escaping. Never pass untrusted input to `innerHTML`/`dangerouslySetInnerHTML`/`v-html`; sanitize with DOMPurify if you must. Use a strict **CSP** (nonce- or hash-based, `object-src 'none'`, `base-uri 'none'`) and Trusted Types where supported |
| Token theft | Keep session tokens in **httpOnly, Secure, SameSite** cookies, not `localStorage`. Use short-lived access tokens and refresh rotation, handled through a BFF |
| CSRF | For state-changing requests: a synchronizer token or a signed (HMAC, session-bound) double-submit cookie (ideally `__Host-`), plus `Origin` / `Sec-Fetch-Site` checks on the server. SameSite cookies as defence in depth |
| Clickjacking | `Content-Security-Policy: frame-ancestors 'none'` (or a list of allowed origins) |
| Supply chain | Lockfiles; `npm audit` or Dependabot/Renovate; minimal dependencies; **SRI** for third-party CDN scripts; review postinstall scripts |
| Secrets | Never ship secrets in client bundles. Only explicitly public env vars reach the browser |
| Open redirects / URL injection | Validate redirect targets against an allowlist. Allow-list `href` schemes: parse with `new URL()` and allow only `https:`, `http:`, `mailto:` (a `javascript:` blocklist misses `data:`, `vbscript:` and obfuscated forms) |
| Data exposure | Don't over-fetch PII into the client. Mask sensitive fields. Set `Referrer-Policy: strict-origin-when-cross-origin` |
| Third-party scripts | Inventory them; load them with least privilege; sandboxed iframes for widgets; a `Permissions-Policy` |

Baseline headers: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, and `Cross-Origin-Opener-Policy` where needed.

## Testing strategy

| Layer | Tooling | What to cover |
|---|---|---|
| Static | TypeScript strict, ESLint (with the a11y plugin), Prettier | Type safety, banned patterns |
| Unit | Vitest / Jest | Pure logic, hooks, reducers, formatters |
| Component | Testing Library (+ Vitest browser mode or Storybook interaction tests) | Behaviour from the user's view: queries by role or label, not test IDs |
| Integration | Testing Library + MSW for API mocking | Pages with real data flows, error and empty states |
| E2E | Playwright (or Cypress) | 3–7 critical journeys, cross-browser smoke, auth flows |
| Visual regression | Playwright screenshots, Chromatic, or Percy | The design system and key pages in light and dark themes |
| Accessibility | axe in component and e2e tests, plus manual screen-reader passes | Core journeys |
| Performance | Lighthouse CI, bundle-size checks | Budgets per route |

Use the testing-trophy balance: mostly integration and component tests, a few e2e, and static checks everywhere.

## Observability

- **RUM:** Core Web Vitals with attribution, segmented by route, device and connection.
- **Errors:** Sentry or similar, with source maps uploaded privately, release tagging, and user-impact grouping.
- **Logs and traces:** propagate a trace id from the frontend to the API (W3C `traceparent`).
- **Product analytics:** one typed event schema, consent-aware, with no PII in event properties.
- **Alerts:** on Core Web Vitals regressions, error-rate spikes, and failed critical journeys (synthetic checks).

## Internationalization

- Keep strings out of code in message catalogs. Use ICU MessageFormat for plurals and gender.
- Format dates, numbers, currency and relative time with `Intl.*` and the user's locale.
- Use CSS logical properties (`margin-inline-start`) and `dir="rtl"` support, and mirror directional icons.
- Allow 30–40% text expansion. Don't build strings by concatenation.
- Put the locale in the URL (`/fr/...`) for SEO, with `hreflang` tags.
