# Product playbooks

Each playbook is a baseline: the default architecture and UI for that product type. Start from it and justify any deviation.

`scripts/recommend.py` picks the closest playbook from `data/product-types.csv`.

---

## SaaS web app (B2B or B2C, behind login)
- **Rendering:** SSR or SSG for the marketing site; the app shell runs as an SPA with streaming SSR for the first view, or as a pure SPA.
- **Stack:** Next.js or Vite + React with TanStack Router. Use TanStack Query for server state, Zustand for small UI state, and React Hook Form with Zod for forms.
- **UI:** Sidebar app shell, a command palette, data tables with saved views, settings pages, and an onboarding checklist. Use a headless kit or shadcn/ui with tokens, and support dark mode.
- **Key concerns:** multi-tenant theming, roles and permissions in the UI, optimistic updates, and an audit log UI.
- **Watch out for:** a huge initial bundle (code-split per section), and filter state that isn't in the URL.

## Analytics / real-time dashboard
- **Rendering:** a CSR app shell. Optionally SSR the first paint of KPIs.
- **Data:** SSE or WebSocket for live metrics, batching updates per animation frame. Use TanStack Query for historical data and do aggregation server-side.
- **UI:** a KPI row, then trend charts, then a detail table. Use tabular numbers, a consistent chart colour language, cross-filtering, date-range presets, and an explicit "last updated" indicator.
- **Charts:** ECharts or Highcharts for heavy data, Recharts or Visx for React-native composition, uPlot for very large time series. Use canvas above about 5k points.
- **Watch out for:** re-rendering every chart on every tick (memoize and use a separate store per stream), and inaccessible charts (provide a table view and summaries).

## E-commerce storefront
- **Rendering:** SSG or ISR for category and product pages, SSR for search and cart, and edge caching for anonymous traffic. Personalization goes in client islands.
- **Stack:** Next.js or Nuxt or Astro, with a headless commerce API. Payments go through hosted fields (PCI scope reduction).
- **UI:** a product-first grid, faceted filters stored in the URL, a PDP with a gallery, price, variant selector and sticky add-to-cart on mobile, a mini-cart drawer, and guest checkout with as few fields as possible and address autocomplete.
- **Key concerns:** LCP on the hero and product image, CLS from images and ads, structured data (Product, Offer, Breadcrumb), and accessible variant pickers.
- **Watch out for:** third-party tag bloat; consider server-side tagging.

## Content site / blog / docs
- **Rendering:** SSG (or ISR with a CMS). Islands for search, theme toggle, and code-copy buttons.
- **Stack:** Astro, Next.js, Docusaurus, VitePress, or Starlight, with MDX and a headless CMS if non-developers write content.
- **UI:** editorial typography (60–75 character measure), a table of contents, in-page anchors, search (Pagefind or Algolia), and dark mode.
- **Key concerns:** close to zero JS, excellent LCP, RSS, OG images, and canonical URLs.

## Landing page / marketing site
- **Rendering:** SSG, deployed to a CDN.
- **UI:** a hero with one message and one primary CTA, then social proof, features as a bento grid or alternating rows, pricing, FAQ, and a final CTA. Motion only on scroll reveal, reduced-motion safe.
- **Key concerns:** LCP under 2 s, no layout shift from fonts, analytics without blocking render, and forms with spam protection.
- **Watch out for:** generic template aesthetics. Choose a distinctive direction (see `../core/ui-design.md`).

## Social feed / community
- **Rendering:** SSR for public profiles and posts (for SEO and share previews); the feed is CSR with cursor pagination and infinite scroll.
- **Data:** a normalized cache (posts, users), optimistic likes and comments, SSE or WebSocket for notifications, and image or video upload with progress.
- **UI:** a feed with virtualization, composer, reactions, and threaded replies. Use skeletons, and "new posts" pills instead of auto-inserting at the top.
- **Watch out for:** memory growth in long sessions, scroll-position restoration, and moderation and report flows.

## Chat / messaging
- **Data:** a WebSocket with heartbeat and reconnect, message ordering by server sequence number, optimistic send with retry, read receipts and typing indicators, and a local IndexedDB cache for history and offline.
- **UI:** a conversation list plus thread (list–detail), a composer with attachments, unread markers, and jump-to-latest. Announce new messages through `aria-live` without stealing focus.
- **Watch out for:** duplicate or out-of-order messages, unbounded DOM growth (virtualize), and notification permission UX.

## Collaborative editor / design canvas
- **Data:** CRDT (Yjs or Automerge) or OT through a sync server, presence (cursors and selections), undo per user, and offline edits.
- **Rendering:** a CSR heavy client. Use canvas or WebGL for the canvas, and ProseMirror, Tiptap or Lexical for rich text. Do heavy work in workers.
- **UI:** toolbars, contextual panels, keyboard shortcuts, minimaps, and version history.
- **Watch out for:** INP under load (yield and offload to workers), and accessibility of canvas content (provide a parallel accessible tree).

## Booking / marketplace
- **Rendering:** SSR or ISR for listings (SEO), CSR for search filters and the map, SSR for checkout.
- **UI:** search with date and guest pickers, filters plus a map split view, listing cards, an availability calendar, and a transparent price breakdown. Show trust signals.
- **Watch out for:** date-picker accessibility, time zones (store UTC, display in local time), and race conditions on availability (optimistic hold with server confirmation).

## Internal tool / admin panel
- **Rendering:** a CSR SPA is fine.
- **Stack:** Vite + React with a full design system (MUI, Mantine, or Ant Design), TanStack Table and Query, and generated API types.
- **UI:** dense tables with column config, bulk actions, inline edit, keyboard shortcuts, and audit trails. Optimize for speed of work over brand.
- **Watch out for:** permission edge cases, and destructive actions without confirmation or undo.

## Maps / location-based app
- **Rendering:** SSR the shell and lists; the map runs client-only and is lazy-loaded.
- **Stack:** MapLibre GL or Mapbox GL (vector tiles), with clustering and viewport-based fetching.
- **UI:** a list and map split that stay synchronized on hover and selection, a "search this area" control, and a geolocation permission prompt only after the user acts.
- **Watch out for:** map bundle size (lazy-load it), and keyboard and screen-reader access to markers (mirror them in the list).

## Mobile-first PWA
- **Rendering:** an SSR or SSG shell, a service worker with an app-shell cache, and a web app manifest.
- **UI:** bottom navigation, 44 px touch targets, safe-area insets, pull-to-refresh only where expected, and offline states.
- **Watch out for:** iOS PWA limitations (check current push and storage support), and storage eviction (request persistent storage for user data).

## AI / chat-assistant product
- **Data:** stream tokens over SSE or a fetch stream; cancel with `AbortController`; store conversation history; handle tool and status events.
- **UI:**
  - a streaming message list with stable layout;
  - a stop / regenerate control;
  - rich content in responses: Markdown, code blocks with copy, citations;
  - prompt suggestions in the empty state;
  - clear errors and rate-limit messages.
- **Watch out for:**
  - XSS from rendering model output: sanitize Markdown, and never render raw HTML;
  - jank while streaming: batch updates per frame;
  - focus management while streaming.

---

## Consumer mobile app
- **Platform choice:** see `../platforms/mobile.md`.
  - **SwiftUI + Jetpack Compose** when the best platform feel or deep OS integration matters and you can staff two teams.
  - **Expo (React Native)** for a React/TypeScript team.
  - **Flutter** for one custom-branded UI everywhere.
  - **Capacitor** to ship an existing web app.
- **Architecture:** feature-based modules, a typed API client, a query cache for remote data, a local DB for offline, secure storage (Keychain/Keystore) for tokens, and remote config / feature flags for staged rollouts and kill switches.
- **UI:** bottom tabs for 3–5 destinations, stack navigation inside tabs, and sheets for quick tasks. Follow the platform conventions (`../platforms/mobile.md`), use 44 pt / 48 dp touch targets, and support dynamic type.
- **Key concerns:**
  - cold start and frame rate (aim for 60 fps; profile on mid-range Android);
  - offline and poor-network states;
  - a permission pre-prompt UX;
  - deep links;
  - push notification strategy;
  - force-update path.
- **Watch out for:**
  - shipping secrets in the binary;
  - unbounded image memory;
  - ignoring Android back behaviour;
  - store review rules for payments and OTA updates.

## Fitness / health app
- **Data:**
  - **local-first logging**: the local DB is the source of truth, with a background sync queue;
  - integrate with platform health stores (HealthKit / Health Connect) only for the data you need, behind explicit permission;
  - wearables via their SDKs.
- **Architecture:** native (SwiftUI/Compose) when you depend heavily on health and sensor APIs; Flutter/Expo otherwise, with native modules for health access.
- **UI:** a today/progress dashboard (KPI cards plus trends), quick logging in 1–2 taps, streaks and gentle reminders. Use a calm palette, large numbers, and charts with a text alternative.
- **Key concerns:** privacy (health data is sensitive: minimise it, encrypt at rest, follow store health-data policies), battery use from background work, and notification fatigue.
- **Watch out for:** guilt-inducing copy, inaccessible charts, and data loss on sync conflicts. Define merge rules.

## On-demand delivery app
- **Surfaces:**
  - customer app (browse → cart → checkout → live tracking);
  - courier/driver app (job queue, navigation hand-off, status updates);
  - merchant or admin web (CSR dashboard).
- **Data:**
  - the order is a **server-driven state machine**;
  - live location over WebSocket/SSE, throttled and batched for both the UI and battery;
  - optimistic cart;
  - idempotent checkout.
- **UI:**
  - a map plus bottom sheet for tracking;
  - clear ETA and status steps;
  - live updates without layout jumps;
  - support and contact entry points at every stage.
- **Key concerns:** background location permissions and battery, flaky networks (queue courier status updates), push notifications for status changes, and accessibility of map-only information (mirror it in text).
- **Watch out for:** race conditions between client and server order state, and stale ETAs. Show "last updated".

## Desktop app
- **Shell:** see `../platforms/desktop.md`. Use **Tauri** for small, secure apps with a web UI, **Electron** when you need full Node/Chromium consistency or its ecosystem, and native (SwiftUI/WinUI) for deep OS integration.
- **Architecture:**
  - a native core (Rust/Node main process) that owns the file system, OS APIs, auto-update and secrets;
  - a UI process that only talks to the core through typed IPC commands, with least privilege (Electron `contextIsolation` + sandbox; Tauri capabilities);
  - local-first storage (files or SQLite) with optional cloud sync.
- **UI:** a menu bar and keyboard shortcuts for every command, a command palette, multi-window support where it helps, native dialogs, and respect for the OS theme and accent.
- **Key concerns:** code signing and notarization, auto-update channels, crash reporting, offline by default, and startup time.
- **Watch out for:** remote content loaded with Node access (never do this), large bundles, and memory growth in long sessions.
