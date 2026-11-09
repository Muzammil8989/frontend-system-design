# Ionic + Capacitor

> **Platform:** cross (iOS, Android, web/PWA; desktop via community Electron platform) · **Language:** TypeScript (Angular, React or Vue) · **Rendering:** web UI in the system WebView (WKWebView / Android System WebView) + native plugins · **Best for:** web teams turning an existing web app or skill set into store-installable mobile apps with native device access

## When to choose

| Choose it when | Avoid it when |
|---|---|
| You already have (or want) a web app and need iOS/Android apps sharing most code | Animation-heavy, gesture-rich consumer UI where native feel is the product |
| Team is web-first (Angular/React/Vue); no native hiring planned | Heavy real-time graphics, large lists of complex rows, or 120 Hz-critical interactions |
| Content, forms, dashboards, internal/enterprise apps, B2B companion apps | Deep OS integration across many native APIs (widgets, extensions, background audio) |
| You need a PWA and store apps from one codebase | Store reviewers may see a thin website wrapper — apps must add native value (Apple guideline on minimum functionality) |
| Capacitor's plugin model lets you drop to Swift/Kotlin when needed | You need consistent rendering independent of the device WebView version |

## Project structure

```text
src/
  app/                          # (Angular shown; React/Vue equivalent)
    app.routes.ts               # lazy routes per feature
    tabs/tabs.page.ts           # ion-tabs shell
    features/
      orders/
        orders.page.ts          # ion-header / ion-content / ion-list
        order-detail.page.ts
        orders.service.ts       # API + cache
        orders.store.ts         # signals/NgRx SignalStore (or Zustand/Pinia)
      auth/
      settings/
    core/
      native/                   # wrappers over Capacitor plugins (Camera, Push, Preferences)
      http/                     # interceptors: auth, retry, offline queue
      storage/                  # SQLite / IndexedDB access
    shared/ui/                  # design-system components on top of Ionic
  theme/variables.css           # Ionic CSS variables = design tokens (light/dark)
  index.html
capacitor.config.ts             # appId, webDir, plugin config, server settings
ios/App/                        # native Xcode project (committed)
android/                        # native Gradle project (committed)
```

- Wrap every Capacitor plugin call in `core/native` with a web fallback, so the app runs in the browser and tests can mock it.
- Native `ios/` and `android/` projects are source code: commit them and edit them (permissions, entitlements, icons).
- Run `npx cap sync` after web builds or plugin changes; CI must do the same.
- Lazy-load feature routes to keep the initial bundle small inside the WebView.

## Routing & navigation

- Use the framework router via Ionic's integration: Angular Router (`IonRouterOutlet`), `@ionic/react-router` (`IonReactRouter`), `@ionic/vue-router`.
- Ionic keeps a native-like **stack per tab** (`ion-tabs`) with platform page transitions and iOS swipe-back.
- Modals/sheets: `ion-modal` (with breakpoints for bottom sheets), `ion-action-sheet`, `ion-popover`.
- Deep links: Universal Links/App Links configured natively; handle with `App.addListener('appUrlOpen', ...)` and route to the matching path.
- Android hardware back: Ionic handles it inside navigation; use `ionBackButton` events for custom behavior.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | TanStack Query (React/Vue/Angular adapters) or Angular services + signals/RxJS; HTTP via framework client or `CapacitorHttp` to avoid CORS |
| Local persistence / offline DB | `@capacitor-community/sqlite` (native SQLite) or IndexedDB (Dexie) for web-compatible storage |
| Key-value / prefs | `@capacitor/preferences` (not for secrets) |
| Secrets | Keychain/Keystore-backed secure storage plugin (community or Ionic enterprise); never `localStorage` |
| Forms + validation | Angular Reactive Forms; React Hook Form + Zod; VeeValidate/Zod for Vue |
| UI state | Component state / signals / refs |
| App-wide state | NgRx SignalStore or services+signals (Angular), Zustand (React), Pinia (Vue) |
| DI | Angular DI; React/Vue use modules + context/provide-inject |

## Styling & design system

- Ionic components ship **adaptive styling**: `ios` mode (HIG-like) and `md` mode (Material Design) chosen by platform; force one mode for brand uniformity if desired.
- Tokens via Ionic CSS variables (`--ion-color-primary`, `--ion-background-color`, step colors) plus your own custom properties.
- Dark mode: Ionic's dark palette (class-based or `prefers-color-scheme`); sync with system via media query.
- Safe areas: `env(safe-area-inset-*)`, handled by `ion-header`/`ion-content`.
- Font scaling: use `rem`-based type; enable Ionic's dynamic font scaling; Android WebView text zoom follows system settings; test iOS Dynamic Type.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz — WebView main thread handles JS + layout; keep long tasks short, use `requestAnimationFrame`, prefer CSS `transform`/`opacity` animations.
- Lists: virtualize long lists (Angular CDK virtual scroll, TanStack Virtual, vue-virtual-scroller); `ion-virtual-scroll` is no longer part of Ionic.
- Startup: small initial JS bundle, lazy routes, defer analytics/SDKs, keep the native splash until first render (`SplashScreen.hide()` after data).
- Images: responsive `srcset`, lazy loading, `ion-img`, modern formats; HTTP caching headers for remote images.
- Memory: avoid keeping many heavy pages in tab stacks; unsubscribe listeners on page leave (`ionViewWillLeave`).
- Background work: limited — WebView JS pauses in background; use native plugins (background runner, push) for real background tasks.
- Old Android devices with outdated WebViews are the worst case; test on low-end hardware.

## Accessibility

- Web semantics apply: native HTML elements, labels, ARIA only where needed; WebView exposes them to VoiceOver/TalkBack.
- Ionic components include roles/labels; still set `aria-label` on icon-only buttons (`ion-button` with `ion-icon`).
- Focus management: move focus to page heading on navigation and into modals; return focus on close.
- Touch targets ≥ 44 pt iOS / 48 dp Android (Ionic defaults mostly comply; check custom elements).
- Respect `prefers-reduced-motion` and text scaling; test zoom at 200%.
- Test: axe-core/Lighthouse in browser, VoiceOver/TalkBack on device, Safari Web Inspector / Chrome remote debugging for the WebView.

## Testing

| Level | Tooling |
|---|---|
| Unit | Vitest/Jest (Jasmine/Karma or Jest for Angular); mock Capacitor plugin wrappers |
| Component | Angular TestBed / Testing Library (React/Vue) |
| Web E2E | Playwright or Cypress against `ionic serve`/production web build |
| Device E2E | Appium/WebdriverIO (hybrid context switching) or Maestro for native flows (permissions, push) |
| a11y | axe-core in Playwright/Cypress |

## Build & deploy

- Build web (`ng build`/`vite build`) → `npx cap sync` → native build with Xcode/Gradle (or `npx cap build`).
- CI/CD: GitHub Actions + Fastlane, Codemagic, Bitrise; Ionic Appflow historically offered cloud builds — verify its current availability before adopting.
- Live updates (web asset OTA): services such as Capgo or Capawesome Cloud; allowed for web content changes that do not alter the app's primary purpose (Play explicitly exempts JS in a WebView; Apple permits interpreted code updates within guideline limits). Native/plugin changes need a store release.
- Signing: Play App Signing + upload key, Apple certs/profiles via Fastlane match.
- Monitoring: Sentry (Capacitor SDK) with source maps.

## Pitfalls

- Shipping a website in a wrapper with no native value — App Store rejection risk.
- Using `localStorage` for important data: the OS can purge WebView storage; use SQLite/Preferences.
- CORS failures on device (origin `capacitor://localhost` / `https://localhost`): configure the API or use `CapacitorHttp`.
- Huge unsplit bundles and desktop-oriented CSS frameworks making startup slow on mid/low-end Android.
- Forgetting `cap sync` after plugin changes → runtime "plugin not implemented".
- Live-updating web code that depends on a native plugin version not present in the installed binary.
- Treating iOS and Android WebViews as identical — test both, especially keyboard and safe-area behavior.

## References

- https://ionicframework.com/docs
- https://capacitorjs.com/docs
- https://capacitorjs.com/docs/plugins
- https://ionicframework.com/docs/theming/basics
- https://ionicframework.com/docs/developing/hardware-back-button
- https://capacitorjs.com/docs/guides/deep-links
