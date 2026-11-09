# Learning Notes

120 frontend system design notes, organized into one folder per phase of the [learning roadmap](../README.md#learning-roadmap). Read the phases in order: 1–4 build the foundations, 5–9 cover production engineering practices, and 10–11 bring everything together in system design cases.

| Phase | Folder | Topics | Start here |
|---|---|:---:|---|
| 1 · Web Fundamentals | [`01-web-fundamentals/`](./01-web-fundamentals) | 14 | [How Browsers Work](./01-web-fundamentals/how-browsers-work.md) |
| 2 · Rendering & Architecture | [`02-rendering-and-architecture/`](./02-rendering-and-architecture) | 12 | [Client-Side Rendering (CSR)](./02-rendering-and-architecture/client-side-rendering-csr.md) |
| 3 · State & Data | [`03-state-and-data/`](./03-state-and-data) | 12 | [Client State Management Patterns](./03-state-and-data/client-state-management-patterns.md) |
| 4 · Performance Engineering | [`04-performance-engineering/`](./04-performance-engineering) | 15 | [Core Web Vitals (LCP, INP, CLS)](./04-performance-engineering/core-web-vitals-lcp-inp-cls.md) |
| 5 · Design Systems & Components | [`05-design-systems-and-components/`](./05-design-systems-and-components) | 12 | [Atomic Design Methodology](./05-design-systems-and-components/atomic-design-methodology.md) |
| 6 · Accessibility & i18n | [`06-accessibility-and-i18n/`](./06-accessibility-and-i18n) | 9 | [ARIA Roles, States & Properties](./06-accessibility-and-i18n/aria-roles-states-and-properties.md) |
| 7 · Security | [`07-security/`](./07-security) | 8 | [XSS Prevention](./07-security/xss-prevention-reflected-stored-dom.md) |
| 8 · Testing | [`08-testing/`](./08-testing) | 8 | [Unit Testing Components (Jest, Vitest)](./08-testing/unit-testing-components-jest-vitest.md) |
| 9 · Monitoring & Observability | [`09-monitoring-and-observability/`](./09-monitoring-and-observability) | 7 | [Error Boundaries & Global Error Handling](./09-monitoring-and-observability/error-boundaries-and-global-error-handling.md) |
| 10 · Advanced Topics | [`10-advanced-topics/`](./10-advanced-topics) | 8 | [Progressive Web Apps (PWA)](./10-advanced-topics/progressive-web-apps-pwa.md) |
| 11 · System Design Cases | [`11-system-design-cases/`](./11-system-design-cases) | 15 | [Design a News Feed](./11-system-design-cases/design-a-news-feed-facebook-twitter.md) |

Every note follows [`_TEMPLATE.md`](./_TEMPLATE.md): ELI5 → core concept → real-world examples → key points → quiz → cheat sheet → references. Each note links to the previous and next topic, so you can read straight through.

- **Full topic list:** the [README roadmap](../README.md#learning-roadmap)
- **Reading offline in VS Code (Mermaid setup):** [docs/reading-the-notes.md](../docs/reading-the-notes.md)
- **Adding a note:** `npm run new-note -- <slug> --phase <1-11>`, then follow [CONTRIBUTING.md](../CONTRIBUTING.md)
