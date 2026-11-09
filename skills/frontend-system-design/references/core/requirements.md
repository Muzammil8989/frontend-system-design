# Requirements: discovery and scoping

The goal is to learn the few facts that change the architecture, then move on. Ask the user only the questions whose answers would change a decision. For everything else, assume a default and write it down as an assumption.

## 1. Classify the product

Start with `scripts/recommend.py "<description>"`. It returns the closest product type and its baseline. The product types are listed in `references/playbooks/product-playbooks.md`. Settle the **platform** (web, mobile, desktop) early: see `references/platforms/`.

If the product is a hybrid (e.g. a marketing site plus a SaaS app), split it into **surfaces** and design each one separately. Different surfaces often need different rendering.

## 2. Questions that change the architecture

| # | Question | Why it matters | Default if unknown |
|---|---|---|---|
| 1 | Must public pages rank in search or render rich link previews? | SSR/SSG vs CSR | Yes for marketing/content, no for apps behind login |
| 2 | How fresh must data be (static, minutes, seconds, live)? | SSG/ISR vs SSR vs real-time transport | Minutes |
| 3 | Is there multi-user real-time interaction (chat, presence, collaboration)? | WebSocket/SSE, CRDTs, conflict handling | No |
| 4 | Must it work offline or on very poor networks? | Service worker, local-first storage, sync | No, but it must degrade gracefully |
| 5 | Who are the users and what devices do they use? | Budgets, input mode, layout | Global, mid-range Android over 4G, plus desktop |
| 6 | How big is the data per view (rows, items, media)? | Virtualization, pagination, streaming | Under 1k rows |
| 7 | Are there authentication or role/permission needs? | BFF, route guards, per-role UI | Cookie session, 2–3 roles |
| 8 | Is internationalization needed? Any RTL languages? | i18n architecture, logical CSS | English only, but i18n-ready strings |
| 9 | What accessibility target or legal requirement applies? | Component choices, testing | WCAG 2.2 AA |
| 10 | What are the team size and skills? Is there an existing stack? | Framework choice, monorepo, conventions | Small team, React and TypeScript |
| 11 | What are the hosting and budget constraints (static host, edge, containers)? | Rendering options, cost | A managed platform that supports SSR |
| 12 | Will this be embedded elsewhere or white-labelled? | Theming, iframes, Web Components | No |

## 3. Functional requirements format

List the **3–7 core user journeys** as verbs. Example: "browse catalog → filter → view product → add to cart → checkout".

For each journey, note:
- the main screens;
- the critical interactions;
- the data each screen needs;
- the success metric (e.g. checkout conversion, time-to-first-insight).

## 4. Non-functional requirements matrix

| Attribute | Target | Notes |
|---|---|---|
| Performance | LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 (p75, mobile) | Add a JS budget from `scripts/budget.py` |
| Availability | e.g. static fallback if the API is down | Error boundaries, cached shells |
| Scalability | Peak concurrent users and data growth | Affects caching/CDN and pagination |
| Accessibility | WCAG 2.2 AA | Plus product-specific needs |
| Security | Auth model, PII, payment | CSP, cookie flags, third-party scripts |
| SEO | Indexable routes, structured data | Rendering per route |
| Observability | RUM for Core Web Vitals, error tracking | See `quality.md` |
| Browser support | Evergreen plus Safari (last 2 versions) | Note any legacy requirement explicitly |

## 5. Back-of-envelope estimation (when scale matters)

- **Payload per view:** HTML + critical CSS + JS + images, compared with the budget.
- **Request fan-out:** API calls per page load. More than 4 sequential calls suggests a BFF or aggregation endpoint.
- **List size:** items × row height. Past about 200–500 complex rows, plan for virtualization.
- **Real-time volume:** messages/sec per client × payload size, which decides throttling and batching.
- **Cache hit ratio:** static versus personalized share of each page, which decides CDN and edge strategy.

## 6. Output of this step

A short **Requirements summary** block. It is the input for every specialist and for the design doc:

```text
Product type: <type> (confidence: high/med/low)  Surfaces: <list>
Core journeys: 1) … 2) … 3) …
Key NFRs: SEO <y/n>, freshness <…>, real-time <…>, offline <…>, a11y <…>, i18n <…>
Users/devices: <…>   Scale: <…>   Team/stack: <…>
Assumptions: <bullets>
Open questions: <only the ones that block decisions>
```
