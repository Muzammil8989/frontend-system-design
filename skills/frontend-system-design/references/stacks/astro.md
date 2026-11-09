# Astro

> **Platform:** web · **Language:** TypeScript (`.astro` + any UI framework) · **Rendering:** SSG by default, on-demand SSR per route, islands (partial hydration), server islands · **Best for:** content-driven sites — marketing, docs, blogs, landing pages, catalogs — that need top Core Web Vitals and SEO

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Content is the product: marketing site, docs (Starlight), blog, portfolio, editorial | The whole UI is an app shell with heavy shared client state (SaaS dashboard, editor) |
| You want near-zero JS by default and interactive "islands" only where needed | Most components need to share state and re-render together across the page |
| Content comes from Markdown/MDX, a headless CMS, or APIs at build time | You need deep client-side routing transitions with persistent app state everywhere |
| Team wants to reuse React/Vue/Svelte/Solid components in one site | You need a single-framework full-stack app with complex mutations (Next.js, SvelteKit, Nuxt) |
| Mostly static with a few dynamic routes (search, cart, personalized header) | Real-time collaborative UI is core |

## Project structure

```text
site/
├── astro.config.mjs                   # integrations (react, mdx, sitemap), adapter, output, env schema
├── src/
│   ├── content.config.ts              # content collections: loaders + zod schemas
│   ├── content/
│   │   ├── blog/                      # *.md / *.mdx entries
│   │   └── docs/
│   ├── pages/
│   │   ├── index.astro
│   │   ├── pricing.astro
│   │   ├── blog/
│   │   │   ├── index.astro
│   │   │   └── [slug].astro           # getStaticPaths from collection
│   │   ├── search.astro               # export const prerender = false (on-demand)
│   │   └── api/newsletter.ts          # endpoint (POST)
│   ├── actions/index.ts               # Astro Actions: typed, validated server functions
│   ├── middleware.ts                  # auth, locals, headers
│   ├── layouts/                       # BaseLayout.astro (head, SEO), DocsLayout.astro
│   ├── components/
│   │   ├── ui/                        # static .astro primitives (Button, Card, Badge)
│   │   ├── sections/                  # Hero.astro, FeatureGrid.astro, Footer.astro
│   │   └── islands/                   # interactive: PricingToggle.tsx, SearchBox.tsx
│   ├── stores/                        # nanostores shared between islands
│   ├── lib/                           # cms.ts, seo.ts, utils.ts
│   ├── assets/                        # images processed by astro:assets
│   └── styles/                        # tokens.css, global.css
├── public/                            # robots.txt, favicons (unprocessed)
└── tests/                             # unit/, e2e/
```

- Default to `.astro` components (zero JS); only files in `components/islands/` use a UI framework and a `client:*` directive.
- Islands receive serializable props only; cross-island state goes through Nano Stores, not React context.
- Images that should be optimized live in `src/assets/`, not `public/`.
- All content is typed through `content.config.ts` schemas — invalid frontmatter fails the build.
- Unit tests colocated or in `tests/unit`; Playwright in `tests/e2e`.

## Routing & navigation

- File-based routing in `src/pages` (`.astro`, `.md`, `.mdx`, `.ts` endpoints); dynamic `[slug]` with `getStaticPaths` for static builds; rest params `[...path]`.
- Multi-page by default (full navigations). Add `<ClientRouter />` (view transitions router) for SPA-like transitions and `transition:persist` to keep islands alive across pages.
- Prefetch links with the `prefetch` config (`hover`, `tap`, `viewport`, `load` strategies).
- Redirects via `redirects` config or `Astro.redirect()` in on-demand routes; i18n routing built in (`i18n` config, `getRelativeLocaleUrl`).

## State & data

| State kind | Recommended tool |
|---|---|
| Server state | Fetch in component frontmatter at build time (SSG) or per request (on-demand); content collections (`getCollection`, `getEntry`) with loaders for CMS/API sources |
| Mutations | Astro Actions (`defineAction` + Zod `input`, callable from forms or islands); endpoints for webhooks |
| URL state | `Astro.url.searchParams` on on-demand pages; `URLSearchParams` + `history.replaceState` inside islands |
| Forms + validation | HTML forms posting to Actions (work without JS); inside islands use the framework's tools (React Hook Form + Zod, etc.) |
| Local UI state | The island framework's primitives (`useState`, `$state`, signals) |
| Global client state | Nano Stores (`atom`, `map`) with framework bindings (`@nanostores/react`, `/vue`, `/solid`, Svelte native) |

- Keep data fetching on the server/build; islands should rarely fetch on mount for content.
- Server islands (`server:defer`) render personalized fragments (avatar, cart count) after the cached static page — keeps the page CDN-cacheable.
- Cache on-demand responses with `Cache-Control`/CDN headers; consider incremental content updates via webhooks + rebuilds for SSG.

## Styling & design system

- Scoped `<style>` in `.astro` files; tokens as CSS custom properties in `styles/tokens.css`; Tailwind CSS via its Vite plugin is common.
- Components: static design primitives written in `.astro`; for interactive islands use the framework's headless libs (Radix/React Aria/shadcn/ui for React, Reka UI for Vue, Bits UI for Svelte, Kobalte for Solid). **Starlight** for documentation sites.
- Dark mode: inline `is:inline` script in `<head>` sets `data-theme`/`.dark` from `localStorage`/`prefers-color-scheme` before paint; re-apply on `astro:after-swap` when using `<ClientRouter />`.

## Performance

- Islands architecture: HTML first, JS only for components with `client:*`. Choose the laziest directive: `client:visible` / `client:idle` / `client:media` over `client:load`; `client:only` skips SSR (avoid above the fold — hurts LCP/CLS).
- LCP ≤ 2.5s: static HTML + CDN; `<Image>`/`<Picture>` from `astro:assets` (AVIF/WebP, dimensions, lazy by default) and set `loading="eager"` + `fetchpriority="high"` on the hero image.
- CLS ≤ 0.1: `astro:assets` sets width/height; reserve space for islands that hydrate; self-host fonts with `font-display: swap` and preloads.
- INP ≤ 200ms: few islands means little main-thread work; isolate third-party scripts (Partytown integration for analytics/tags).
- Keep framework count low — each UI framework used ships its own runtime.

## Accessibility

- Mostly static HTML makes semantics easy: landmarks and headings in layouts, `lang` on `<html>`.
- The Astro dev toolbar includes an audit app that flags common a11y issues; add `eslint-plugin-astro` (with its jsx-a11y rules) and axe in Playwright.
- With `<ClientRouter />`, Astro announces the new page title; verify focus lands sensibly and respect `prefers-reduced-motion` for transitions (fallback config).
- Islands must be usable before hydration or show a non-interactive placeholder that is not misleading (no dead buttons).

## Testing

- **Unit:** Vitest with Astro's `getViteConfig()`; test `lib/` utilities and island components with the relevant Testing Library.
- **Astro components:** Container API (`experimental_AstroContainer`) to render `.astro` to strings.
- **E2E:** Playwright against `astro preview`/the built output; Lighthouse CI for CWV budgets.
- **Content:** schema validation happens at build — run `astro check` in CI.

## Build & deploy

- `astro build` → static `dist/` (any CDN: Cloudflare Pages, Netlify, Vercel, GitHub Pages, S3) or server output with an adapter (`@astrojs/node`, `/vercel`, `/netlify`, `/cloudflare`) when any route is on-demand.
- Env vars: `import.meta.env.PUBLIC_*` is exposed to client code; others are server-only. Prefer the typed `astro:env` schema (`envField` with `context: 'client' | 'server'` and `access: 'public' | 'secret'`).
- Values used in `.astro` frontmatter at build time end up in static HTML — never render secrets.

## Pitfalls

- **`client:load` everywhere** → recreates SPA bundle costs; default to `client:visible`/`client:idle` or no directive.
- **Building the whole page as one big island** → loses Astro's benefits; keep islands small.
- **Sharing state via framework context across islands** → islands are separate roots; use Nano Stores.
- **Passing non-serializable props (functions, class instances) to islands** → fails; pass plain data.
- **Images in `public/`** → no optimization; move to `src/assets`.
- **Scripts not re-running after `<ClientRouter />` navigation** → listen to `astro:page-load`.
- **Mixing several UI frameworks casually** → multiple runtimes; pick one for islands.

## References

- https://docs.astro.build/en/concepts/islands/
- https://docs.astro.build/en/guides/content-collections/
- https://docs.astro.build/en/guides/images/
- https://docs.astro.build/en/guides/on-demand-rendering/
- https://docs.astro.build/en/guides/environment-variables/
- https://docs.astro.build/en/guides/view-transitions/
