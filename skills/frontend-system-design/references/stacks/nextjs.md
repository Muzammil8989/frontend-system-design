# Next.js (App Router)

> **Platform:** web · **Language:** TypeScript · **Rendering:** SSR, SSG, ISR, streaming, partial prerendering, CSR islands via Client Components · **Best for:** SEO-critical products and full-stack React apps (e-commerce, SaaS with marketing site, content + app hybrids)

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Public pages need SEO, fast LCP and rich social previews | The app is fully behind login and served as static files (React + Vite is simpler) |
| You want per-route rendering choices (static marketing, dynamic dashboard, ISR catalog) | You need to deploy to a host with no Node/edge runtime and no static-export compromise |
| React Server Components can cut client JS (content-heavy pages, catalogs) | The team is new to React and the server/client boundary would slow delivery |
| A BFF in the same repo (Route Handlers, Server Actions) fits the team | A separate backend team owns all APIs and you only need a thin client |
| You want first-class image/font/script optimization out of the box | You want minimal framework magic and explicit caching semantics everywhere |
| Vercel or a container platform is acceptable for hosting | Highly interactive, client-only canvas/editor apps with little server rendering |

## Project structure

```text
web/
├── next.config.ts
├── middleware.ts                 # auth redirects, i18n, headers (file name differs in newer versions; see docs)
├── public/
├── src/
│   ├── app/
│   │   ├── layout.tsx            # root <html>, fonts, providers
│   │   ├── globals.css
│   │   ├── (marketing)/          # route group: static, cached pages
│   │   │   ├── page.tsx
│   │   │   └── pricing/page.tsx
│   │   ├── (app)/                # route group: authenticated shell
│   │   │   ├── layout.tsx        # session check, sidebar
│   │   │   ├── projects/
│   │   │   │   ├── page.tsx      # Server Component: fetch + render list
│   │   │   │   ├── loading.tsx   # streamed skeleton
│   │   │   │   ├── error.tsx     # client error boundary
│   │   │   │   └── [projectId]/page.tsx
│   │   │   └── settings/page.tsx
│   │   ├── api/webhooks/stripe/route.ts   # Route Handler (external callers only)
│   │   └── not-found.tsx
│   ├── features/
│   │   └── projects/
│   │       ├── components/       # ProjectCard.tsx (server), ProjectFilters.tsx ('use client')
│   │       ├── actions.ts        # 'use server' mutations with zod validation + auth check
│   │       ├── queries.ts        # import 'server-only'; DB/API reads, cached
│   │       └── schemas.ts
│   ├── components/ui/            # design-system primitives (shadcn/ui)
│   ├── lib/                      # db.ts, auth.ts, env.ts (validated)
│   └── styles/tokens.css
├── e2e/
└── .env.example
```

- `app/` holds routing files only; logic lives in `features/*` and `lib/`.
- Server-only modules start with `import 'server-only'`; client modules with `'use client'` at the smallest possible leaf.
- Server Actions re-validate input (Zod) and re-check authorization — they are public HTTP endpoints.
- Colocate unit tests (`*.test.tsx`); Playwright specs in `/e2e`.
- Private folders (`_components`) or `features/` keep non-route files out of the URL space.

## Routing & navigation

- File-system routing: `page`, `layout`, `loading`, `error`, `not-found`, `template`; dynamic `[id]`, catch-all `[...slug]`, route groups `(group)`, parallel (`@slot`) and intercepting routes (modals with shareable URLs).
- `<Link>` prefetches routes in the viewport in production; `useRouter().push` for imperative navigation; `redirect()`/`notFound()` from server code.
- Request APIs (`params`, `searchParams`, `cookies()`, `headers()`) are async in current versions — `await` them; using them opts the route into dynamic rendering.
- `generateStaticParams` for prebuilding dynamic routes; `generateMetadata` for per-page SEO tags.

## State & data

| State kind | Recommended tool |
|---|---|
| Server state (reads) | Fetch in Server Components (`async` components, direct DB/API calls); cache with the framework cache (`fetch` options, `use cache`/`unstable_cache` depending on version) + `revalidateTag`/`revalidatePath` |
| Server state (client-side, live) | TanStack Query in Client Components for polling, infinite scroll, optimistic UX; hydrate from server prefetch via `HydrationBoundary` |
| Mutations | Server Actions + `useActionState` / `useOptimistic`; Route Handlers for webhooks and third-party callers |
| URL state | `searchParams` on the server; `useSearchParams` + `router.replace` or `nuqs` on the client |
| Forms + validation | React Hook Form + Zod (client UX) with the same Zod schema re-run in the Server Action; Conform for progressive-enhancement forms |
| Local UI state | `useState` in small Client Components |
| Global client state | Zustand/Jotai created per request via a provider (never module-level singletons that leak between users on the server) |

- Default to fetching on the server, close to where data is used; React dedupes identical `fetch` calls within a request.
- Avoid waterfalls: start independent promises in parallel (`Promise.all`) and stream slow parts behind `<Suspense>`.
- Caching defaults have changed across major versions — always state the intended cache policy explicitly per route/fetch.

## Styling & design system

- Tailwind CSS with tokens as CSS variables, or CSS Modules; zero-runtime CSS-in-JS (vanilla-extract, Panda CSS) works with Server Components; runtime CSS-in-JS (styled-components, Emotion) needs client boundaries and registry setup.
- Components: **shadcn/ui** (Radix/Base UI + Tailwind), **Radix Primitives**, **React Aria Components**, **Mantine**, **MUI** (App Router integration package).
- Dark mode: `next-themes` (class or `data-theme` on `<html>`, `suppressHydrationWarning` on `<html>`), tokens swapped via CSS variables.

## Performance

- Push `'use client'` to leaves: a client boundary high in the tree ships the whole subtree as JS and hydrates it (hurts INP and TBT).
- LCP ≤ 2.5s: statically render or cache above-the-fold content; `next/image` with `priority` (or `fetchPriority="high"`) on the LCP image and correct `sizes`; `next/font` self-hosts fonts with size-adjusted fallbacks (helps CLS ≤ 0.1).
- Stream with `loading.tsx`/`<Suspense>` so TTFB is not blocked by the slowest query.
- `next/dynamic` with `ssr: false` for heavy client-only widgets (charts, editors, maps).
- `next/script` with `strategy="lazyOnload"` or `worker` options for third-party tags; third parties are the usual INP killers.
- Partial prerendering (where enabled) serves a static shell instantly and streams dynamic holes.
- Analyze bundles with `@next/bundle-analyzer`; watch Client Component imports that drag server-heavy libraries.

## Accessibility

- Next.js includes a route announcer for client-side navigations; still manage focus for in-page updates and modals.
- `eslint-config-next` includes `jsx-a11y` rules; add `@axe-core/playwright` checks in e2e.
- Set `lang` on `<html>` in the root layout; unique `metadata.title` per page.
- Intercepted-route modals must trap focus, restore focus on close, and be reachable as a full page on refresh.
- Use headless primitives (Radix, React Aria) for complex widgets.

## Testing

- **Unit/component:** Vitest or Jest (`next/jest`) + React Testing Library for Client Components and pure logic. Async Server Components are best covered by e2e.
- **Server Actions / queries:** test as plain functions with mocked DB/session.
- **E2E:** Playwright against `next build && next start` (not dev mode); MSW or test DB for data.
- **Visual:** Storybook (Next.js framework preset).

## Build & deploy

- `next build` with Turbopack or webpack; output modes: default (Node server), `output: 'standalone'` (minimal Docker image), `output: 'export'` (pure static, loses server features).
- Hosts: Vercel (zero-config), Netlify, Cloudflare/AWS via OpenNext adapters, any Node container (Railway, Fly.io, Render, Kubernetes).
- Env vars: only `NEXT_PUBLIC_*` reach the browser and are **inlined at build time**; everything else is server-only. Guard server modules with `server-only`.
- Self-hosting: configure a shared cache handler for ISR across multiple instances, and keep build ID/assets consistent behind a CDN.

## Pitfalls

- **`'use client'` on layouts/pages** → entire tree becomes client JS. Move it to interactive leaves; pass Server Components as `children`.
- **Unauthenticated Server Actions** → every action is a POST endpoint; check session and validate input inside it.
- **Leaking secrets or full DB rows to Client Components** → props are serialized into the HTML; pass DTOs only, use `server-only` and taint APIs where available.
- **Accidental dynamic rendering** (reading cookies/headers in a shared layout) → whole subtree loses static caching; isolate dynamic reads.
- **Stale data confusion** → be explicit about caching and call `revalidateTag`/`revalidatePath` after mutations.
- **Sequential awaits** creating waterfalls → parallelize and stream with Suspense.
- **Hydration mismatches** from `Date.now()`, locale formatting, `window` checks → render deterministic output or defer to `useEffect`.

## References

- https://nextjs.org/docs/app/getting-started/project-structure
- https://nextjs.org/docs/app/getting-started/server-and-client-components
- https://nextjs.org/docs/app/getting-started/caching-and-revalidating
- https://nextjs.org/docs/app/guides/environment-variables
- https://nextjs.org/docs/app/api-reference/components/image
- https://nextjs.org/docs/app/guides/self-hosting
