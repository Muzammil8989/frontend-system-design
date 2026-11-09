# Performance

## Targets (acceptance criteria)

Core Web Vitals are measured at the **75th percentile** of real users, segmented by mobile and desktop:

| Metric | Good | Needs improvement | Poor |
|---|---|---|---|
| **LCP**: Largest Contentful Paint | ≤ 2.5 s | ≤ 4.0 s | > 4.0 s |
| **INP**: Interaction to Next Paint (replaced FID in March 2024) | ≤ 200 ms | ≤ 500 ms | > 500 ms |
| **CLS**: Cumulative Layout Shift | ≤ 0.1 | ≤ 0.25 | > 0.25 |

Diagnostic metrics: TTFB (aim for ≤ 0.8 s), FCP (≤ 1.8 s), and Total Blocking Time in lab tests.

## Budgets

Generate the budget with `scripts/budget.py --from "<description>"`, or `--type <product-type>`. It outputs a table and a Lighthouse `budget.json`.

Budgets are compressed transfer sizes for the **initial route** on mobile. They are starting points; tighten them for content sites and relax them for authenticated apps.

| Product kind | JS | CSS | Fonts | Images (above fold) |
|---|---|---|---|---|
| Content / marketing | ≤ 100 KB | ≤ 50 KB | ≤ 100 KB | ≤ 200 KB |
| E-commerce | ≤ 170 KB | ≤ 60 KB | ≤ 100 KB | ≤ 300 KB |
| SaaS / dashboard (after login) | ≤ 250 KB | ≤ 80 KB | ≤ 100 KB | ≤ 150 KB |

Enforce budgets in CI with a bundle-size check (e.g. size-limit, bundler stats) and Lighthouse CI on the key routes.

## LCP playbook

1. Make the LCP element discoverable in the initial HTML. Don't inject it with client JS, and don't load it lazily.
2. Use `fetchpriority="high"` on the LCP image, plus a `preload` if it's in CSS. Serve AVIF or WebP at the correct size with `srcset`/`sizes`.
3. Reduce TTFB with CDN caching, SSG/ISR, streaming, and edge caching for anonymous traffic.
4. Remove render-blocking resources:
   - inline the critical CSS and defer the rest;
   - use `defer` or `type="module"` for scripts;
   - self-host fonts with `font-display`.
5. Preconnect to the 1–2 critical third-party origins only.

## INP playbook

1. Keep the main thread free: break long tasks above 50 ms with `scheduler.yield()` where it's supported, falling back to `setTimeout`. Yield after visual feedback.
2. Hydrate less: Server Components, islands, lazy hydration of below-the-fold widgets.
3. Make event handlers cheap. Debounce input-driven work, and move heavy computation to a Web Worker.
4. Use virtualization for long lists. Use `content-visibility: auto` for long off-screen sections.
5. Avoid layout thrashing: batch DOM reads, then writes.
6. Audit third-party scripts. Load them after interaction or idle, or isolate them with a facade or partytown-style offloading.

## CLS playbook

1. Set `width`/`height` or `aspect-ratio` on all media, embeds and ads. Reserve space for dynamic slots.
2. Use skeletons with the final dimensions. Never insert content above existing content unless the user asked for it.
3. Limit layout shift from font swap with `size-adjust` and the ascent/descent overrides, or use `font-display: optional`.
4. Animate `transform` and `opacity` only.

## Loading techniques

| Technique | Use |
|---|---|
| Route-level code splitting | Always. Lazy-load heavy, rarely used features (editors, charts, maps) |
| Tree shaking and ESM imports | Import per function (e.g. `lodash-es/debounce`). Avoid barrel files that defeat tree shaking |
| Replace heavy libraries | `moment` → `date-fns`/`Intl`/Temporal polyfill; full icon sets → per-icon imports |
| Image CDN | Automatic format, size and quality. `loading="lazy"` below the fold only |
| Prefetching | Prefetch the likely next route on hover or in viewport. Use the Speculation Rules API for prerender where supported |
| HTTP caching | Hashed static assets with `Cache-Control: public, max-age=31536000, immutable`. HTML is short-lived or revalidated |
| Service worker | Offline and repeat visits. Precache only the shell |
| bfcache | Don't use `unload` handlers. Avoid `Cache-Control: no-store` on pages that are safe to cache |

## Measuring

- **Lab:** Lighthouse, DevTools Performance panel (with CPU throttling), WebPageTest.
- **Field:** CrUX / PageSpeed Insights, plus your own RUM using the `web-vitals` library with attribution builds to find the slow element or interaction.
- Always state whether a number comes from lab or field data, and the device profile used.

References: [web.dev — Core Web Vitals](https://web.dev/articles/vitals) · [Optimize LCP](https://web.dev/articles/optimize-lcp) · [Optimize INP](https://web.dev/articles/optimize-inp) · [Optimize CLS](https://web.dev/articles/optimize-cls) · [Lighthouse performance budgets](https://web.dev/articles/use-lighthouse-for-performance-budgets) · [Critical Rendering Path note](https://github.com/Muzammil8989/frontend-system-design/blob/main/notes/01-web-fundamentals/critical-rendering-path.md)
