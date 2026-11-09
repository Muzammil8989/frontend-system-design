# Web platform guide

Browser-platform essentials for frontend system design. Deeper decision matrices live in [../core/architecture.md](../core/architecture.md); performance targets and playbooks in [../core/performance.md](../core/performance.md).

## Rendering strategies

| Strategy | How it works | Best for | Watch out for |
|---|---|---|---|
| CSR (SPA) | Empty HTML shell, JS renders in browser | Authenticated apps, dashboards, tools behind login | Slow first paint on weak devices, poor SEO without extra work, large JS |
| SSR | Server renders HTML per request, client hydrates | Personalized, SEO-relevant, frequently changing pages | Server cost/latency (TTFB), hydration cost, cache-unfriendly |
| Streaming SSR | SSR sent in chunks with Suspense boundaries | Pages with slow data sections | Status codes/headers fixed once streaming starts |
| SSG | HTML built at deploy time, served from CDN | Docs, marketing, blogs, catalogs that change rarely | Build time grows with page count; stale until rebuild |
| ISR / revalidation | Static pages regenerated on interval or on-demand | Large catalogs, content with moderate freshness needs | Framework/host-specific semantics; stale-while-revalidate windows |
| Islands / partial hydration | Static HTML, only interactive parts hydrate | Content sites with small interactive widgets | Cross-island state sharing is awkward |
| Server Components | Components render on server, ship no JS unless client-marked | Data-heavy React apps reducing client JS | Framework lock-in, mental model of server/client boundary |
| Edge rendering | SSR/middleware at CDN edge | Geo-personalization, auth redirects, A/B at low latency | Restricted runtimes, data far from edge negates gains |

Rule of thumb: render as statically as freshness allows; add interactivity per component, not per page. Mix strategies per route.

## Responsive and adaptive layout

- **Mobile-first** CSS; breakpoints from content, not device names.
- **Container queries** (`container-type: inline-size` + `@container`) for components that live in different-width slots; media queries for page-level layout.
- Fluid type and spacing with `clamp()`; logical properties (`margin-inline`, `padding-block`) for RTL support.
- Viewport units: prefer `dvh`/`svh`/`lvh` over `vh` on mobile (browser chrome resizing).
- Safe areas: `env(safe-area-inset-*)` with `viewport-fit=cover` for notched devices.
- Input-aware: `@media (hover: hover)`, `(pointer: coarse)` for touch target sizing; never hide functionality behind hover only.
- User preferences: `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`, `forced-colors`.
- Responsive images: `srcset` + `sizes`, `<picture>` for art direction/format (AVIF/WebP fallback), explicit `width`/`height` or `aspect-ratio` to avoid CLS.

## PWA and service workers

| Capability | Notes |
|---|---|
| Web App Manifest | name, icons (incl. maskable), `display`, `start_url`, `theme_color`; enables install |
| Service worker | Network proxy for offline, caching, push; scope = path it is served from |
| Caching strategies | Cache-first (hashed static assets), network-first (HTML/API needing freshness), stale-while-revalidate (avatars, non-critical API) |
| Tooling | Workbox (precache manifest, routing, expiration) or framework PWA plugins |
| Offline UX | Offline fallback page, queued mutations, clear "offline/syncing" status |
| Background Sync | Chromium-only; always keep a foreground retry path |
| Web Push | Supported across major browsers; on iOS only for web apps added to the Home Screen; ask permission after user intent |
| Storage | IndexedDB (via Dexie/idb) for data, Cache Storage for responses; request `navigator.storage.persist()`; plan for eviction |

Service worker rules: version caches and delete old ones on `activate`; never cache authenticated HTML across users; provide an update flow ("New version available — reload"); test with DevTools "Update on reload" off.

## SEO essentials

- Indexable content must be in server-rendered or static HTML (SSR/SSG); do not rely on client-only rendering for pages that must rank.
- Real URLs per view (History API routing, no hash routes); one canonical URL per page (`<link rel="canonical">`).
- Unique `<title>` and meta description; Open Graph/Twitter cards for sharing.
- `robots.txt`, XML sitemap(s), `hreflang` for localized variants.
- Structured data (JSON-LD, schema.org) for products, articles, breadcrumbs, FAQs where applicable.
- Correct status codes (404/410, 301 redirects) even with SSR frameworks and SPAs.
- Core Web Vitals (LCP, INP, CLS) are part of page experience signals — see [../core/performance.md](../core/performance.md).
- Semantic HTML (headings hierarchy, landmarks, link text) helps both SEO and accessibility.

## Browser support strategy

- Define support with a **browserslist** query shared by bundler, CSS tooling and linters.
- Use **Baseline** (web.dev / MDN) status to decide: "Widely available" features freely; "Newly available" behind feature detection or with fallback.
- Progressive enhancement: core tasks work with HTML + server; JS enhances. Feature-detect (`@supports`, `'x' in window`), never UA-sniff.
- Polyfill selectively (only what targets lack); avoid shipping legacy bundles to modern browsers.
- Test matrix: Chromium, Firefox, WebKit (Safari, including iOS where all browsers use WebKit) — Playwright covers all three engines.
- Low-end Android + slow network is the realistic worst case for consumer products; test throttled.

## Security headers baseline

| Header / setting | Starting value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Nonce- or hash-based `script-src` with `'strict-dynamic'`, `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'` (or allowed origins) | Mitigates XSS, clickjacking |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` (add `preload` once sure) | Forces HTTPS |
| `X-Content-Type-Options` | `nosniff` | Blocks MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limits referrer leakage |
| `Permissions-Policy` | Disable unused features, e.g. `camera=(), microphone=(), geolocation=()` | Least privilege for powerful APIs |
| `Cross-Origin-Opener-Policy` | `same-origin` (or `same-origin-allow-popups` for OAuth popups) | Process isolation, XS-leak defense |
| `Cross-Origin-Embedder-Policy` | `require-corp` only if you need cross-origin isolation (e.g. `SharedArrayBuffer`) | Enables isolation features |
| Cookies | `Secure; HttpOnly; SameSite=Lax` (or `Strict`), `__Host-` prefix for session cookies | Session protection, CSRF reduction |
| Trusted Types | `require-trusted-types-for 'script'` where supported | Blocks DOM XSS sinks |

Also: Subresource Integrity for third-party scripts, roll out CSP in `Report-Only` first, keep tokens out of `localStorage` when an HttpOnly cookie session is possible, sanitize any HTML you render (DOMPurify).

## Platform capabilities checklist

- [ ] Rendering strategy chosen per route (see [../core/architecture.md](../core/architecture.md))
- [ ] Performance budgets and Core Web Vitals targets set (see [../core/performance.md](../core/performance.md))
- [ ] Responsive layout verified from small phones to wide desktop, plus 200% zoom
- [ ] Offline/poor-network behavior defined (even if "show clear error and retry")
- [ ] SEO requirements known: which routes must be indexable
- [ ] Browser support policy written (browserslist + Baseline)
- [ ] Security headers and CSP deployed and monitored (report endpoint)
- [ ] Accessibility target: WCAG 2.2 AA, keyboard and screen-reader tested
- [ ] Analytics/consent approach compatible with privacy laws in target markets

## References

- https://web.dev/articles/rendering-on-the-web
- https://developer.mozilla.org/docs/Web/CSS/CSS_containment/Container_queries
- https://web.dev/explore/progressive-web-apps
- https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- https://web.dev/baseline
- https://owasp.org/www-project-secure-headers/
- https://developer.mozilla.org/docs/Web/HTTP/CSP
