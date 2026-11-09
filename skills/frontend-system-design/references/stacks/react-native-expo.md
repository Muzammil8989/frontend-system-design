# React Native + Expo

> **Platform:** mobile (iOS, Android; web via react-native-web) · **Language:** TypeScript · **Rendering:** native platform views driven by React (New Architecture: Fabric + TurboModules + JSI, Hermes engine) · **Best for:** product teams with React/TS skills shipping one codebase to iOS + Android with native look and OTA-able JS

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Team already writes React/TypeScript; want to share logic (and some UI) with a web app | App is dominated by heavy custom rendering (games, 3D, video editing) — use native or a game engine |
| You need native UI components and platform feel, not a pixel-identical custom canvas | You need day-one access to every new OS API with zero bridging work |
| Fast iteration matters: Fast Refresh, EAS Update for JS/asset fixes | Most screens are deep platform integrations (widgets, watch, CarPlay, extensions) — the native share dominates |
| You want managed native builds (EAS Build, Continuous Native Generation, config plugins) | Team has no JS experience but strong Swift/Kotlin skills |
| CRUD, commerce, social, content, internal tools, fintech front-ends | Strict binary-size budget where shipping a JS engine is unacceptable |

## Project structure

```text
app/                          # Expo Router: file = route
  _layout.tsx                 # root Stack, providers (QueryClient, theme, auth gate)
  (auth)/sign-in.tsx          # route group, no URL segment
  (tabs)/_layout.tsx          # bottom tabs
  (tabs)/index.tsx            # Home tab
  (tabs)/orders/index.tsx
  (tabs)/orders/[id].tsx      # dynamic route -> /orders/123 (deep-linkable)
  settings/modal.tsx          # presented as modal via Stack.Screen options
  +not-found.tsx
src/
  features/
    orders/
      api/                    # queryOptions, mutations, zod schemas
      components/             # OrderCard.tsx, OrderStatusBadge.tsx
      hooks/                  # useOrders.ts
      store/                  # feature-local zustand slice (if needed)
    auth/
  shared/
    ui/                       # design-system primitives: Button, Text, Sheet
    theme/                    # tokens.ts (color, space, radius, type scale)
    lib/                      # http client, storage (MMKV), analytics, i18n
  native/                     # local Expo modules (Swift/Kotlin) when needed
assets/                       # fonts, images, splash
app.config.ts                 # dynamic config per env (bundle ids, plugins)
eas.json                      # build profiles: development, preview, production
```

- Keep `app/` thin: route files compose feature components; logic lives in `src/features/*`.
- Features never import each other's internals; share via `shared/` or a public `index.ts`.
- Do not commit `ios/` and `android/` when using Continuous Native Generation; change native config through config plugins.
- Put every native capability behind a `shared/lib` wrapper so it can be mocked in tests and swapped later.

## Routing & navigation

- **Expo Router** (file-based, built on React Navigation): stacks, tabs, drawers, modals, route groups, typed routes, automatic deep links.
- Universal Links / Android App Links: configure `associatedDomains` and `intentFilters` in app config; host `apple-app-site-association` and `assetlinks.json`.
- Auth gating: redirect in a layout (`<Redirect>` or protected route groups) rather than conditionally mounting navigators ad hoc.
- Native stack (`react-native-screens`) for native transitions and memory; keep tab roots lazily mounted.
- Without Expo: React Navigation directly with a linking config.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | TanStack Query (persist cache with a persister; `onlineManager` + NetInfo for offline awareness) |
| Local persistence / offline DB | expo-sqlite (with Drizzle ORM if typed queries wanted), WatermelonDB for large offline-first sync, op-sqlite for raw speed |
| Key-value / small prefs | react-native-mmkv (fast, sync); expo-secure-store for tokens/secrets (Keychain/Keystore) |
| Forms + validation | React Hook Form + Zod (`zodResolver`); share schemas with backend/web |
| UI state | `useState`/`useReducer`; Reanimated shared values for animation state |
| App-wide state | Zustand (with MMKV persistence) or Jotai; React Context only for rarely-changing values (theme, auth session) |
| DI | Module boundaries + React Context/provider props; no DI container needed |

## Styling & design system

- Tokens in `shared/theme/tokens.ts`; consume through one styling layer: **NativeWind** (Tailwind classes), **Tamagui** (compiler-optimized, also targets web), or **react-native-unistyles** (StyleSheet superset with themes/breakpoints). Pick one.
- Follow platform conventions where it matters: iOS back-swipe, large titles, sheets; Android back button/predictive back, Material ripple. Use `Platform.select` sparingly.
- Dark mode: `useColorScheme()` + `userInterfaceStyle: "automatic"` in app config; semantic color tokens, never raw hex in components.
- Font scaling: text scales by default (`allowFontScaling`); cap with `maxFontSizeMultiplier` only on space-critical labels; layouts must reflow at large sizes.
- Icons: `@expo/vector-icons` or SVG via `react-native-svg`; images via `expo-image`.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz on **both** JS and UI threads. Animations and gestures on the UI thread: **Reanimated** worklets + **react-native-gesture-handler**.
- Lists: **FlashList** (or `FlatList` with `getItemLayout`, `keyExtractor`, memoized rows). Never `ScrollView` + `map` for unbounded data.
- Images: **expo-image** (memory/disk cache, blurhash placeholders, downsampling); serve correctly sized images.
- Startup: Hermes bytecode, lazy-load heavy screens, avoid synchronous work and large JSON parse at module scope, keep splash until first meaningful data via `SplashScreen.preventAutoHideAsync`.
- Re-renders: React Compiler or `memo`/`useCallback` on hot paths; select narrow slices from Zustand; avoid context churn.
- Profile **release** builds only (dev mode is much slower): React DevTools Profiler, Hermes sampling profiler, Xcode Instruments, Android Studio profiler.
- Background work: `expo-background-task` / `expo-task-manager` (OS-scheduled, not guaranteed); heavy compute in native modules.
- App size: enable Android R8/resource shrinking via build properties, ship AAB, audit dependencies with native code.

## Accessibility

- Props: `accessibilityLabel`, `accessibilityHint`, `accessibilityRole`/`role`, `accessibilityState`, `accessibilityValue`, `accessibilityActions`; `accessible` groups children into one element.
- Announcements: `AccessibilityInfo.announceForAccessibility`; detect `isScreenReaderEnabled`, `isReduceMotionEnabled`.
- Focus: move focus after navigation/modals with `AccessibilityInfo.setAccessibilityFocus`; keep logical DOM-like order.
- Touch targets ≥ 44 pt iOS / 48 dp Android: use `hitSlop` or padding on small icons.
- Respect Dynamic Type/font scale and reduce motion (Reanimated `useReducedMotion`).
- Test with VoiceOver and TalkBack on devices, Xcode Accessibility Inspector, Android Accessibility Scanner; lint with `eslint-plugin-react-native-a11y`.

## Testing

| Level | Tooling |
|---|---|
| Unit | Jest (`jest-expo` preset) for hooks, stores, schemas |
| Component | React Native Testing Library (`getByRole`, `getByLabelText` — doubles as a11y check) |
| Network | MSW for mocking HTTP in tests |
| E2E | **Maestro** (YAML flows, easy CI) or **Detox** (gray-box, synchronizes with RN) |
| Visual | Storybook for React Native; screenshot diff in E2E |

## Build & deploy

- **EAS Build** (cloud or local) with profiles; development builds replace Expo Go once you add native modules.
- **EAS Submit** to App Store Connect / Play Console; **Fastlane** if building in your own CI.
- **EAS Update** for OTA JS/asset updates: bind to `runtimeVersion` (fingerprint policy) so updates never land on incompatible native binaries; use channels (preview/production) and staged rollouts.
- Store policy: OTA may fix bugs and tweak JS behavior but must not change the app's primary purpose or bypass review; any native change requires a store build.
- Signing: let EAS manage credentials or store them in CI secrets; never commit keystores.
- Monitoring: Sentry (`@sentry/react-native`) with source maps uploaded per build/update.

## Pitfalls

- Testing performance in dev mode and drawing wrong conclusions — always profile release builds.
- Shipping an OTA update with JS that calls a native module missing from the installed binary (runtime version mismatch).
- `ScrollView` with hundreds of children, inline anonymous `renderItem`, unkeyed lists.
- Putting secrets/API keys in `app.config` or JS bundle — the bundle is readable.
- Mixing three styling systems; pick one tokenized approach.
- Animations driven from JS state (`setState` per frame) instead of Reanimated shared values.
- Choosing libraries that do not support the New Architecture; check React Native Directory before adding.

## References

- https://docs.expo.dev/
- https://docs.expo.dev/router/introduction/
- https://reactnative.dev/docs/getting-started
- https://reactnative.dev/docs/accessibility
- https://docs.expo.dev/eas-update/introduction/
- https://tanstack.com/query/latest/docs/framework/react/react-native
