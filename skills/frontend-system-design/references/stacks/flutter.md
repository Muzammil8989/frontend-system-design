# Flutter

> **Platform:** cross (iOS, Android, web, Windows, macOS, Linux) · **Language:** Dart · **Rendering:** own rendering engine (Impeller; Skia on some targets) drawing every pixel · **Best for:** brand-heavy, pixel-consistent UIs on iOS + Android (and optionally desktop) from one codebase

## When to choose

| Choose it when | Avoid it when |
|---|---|
| You want identical custom-branded UI across platforms with smooth animation | App must feel 100% platform-native and track every OS UI change automatically |
| One team, one codebase for mobile (+ desktop/embedded) | SEO-critical or content-first web — Flutter web is canvas-based and heavy |
| Rich custom widgets, charts, motion, design-system-driven products | You rely heavily on native SDKs with no maintained plugin and lack Swift/Kotlin skills |
| Team is comfortable learning Dart; strong typed, null-safe codebase wanted | You must share code with an existing React/TS web app |
| Kiosk, embedded, automotive-style or multi-form-factor UIs | Tight binary size budget (engine adds baseline size) |

## Project structure

```text
lib/
  main.dart                    # bootstrap: ProviderScope / BlocProvider, flavors
  app/
    app.dart                   # MaterialApp.router, theme, localization
    router.dart                # go_router config, redirects, ShellRoutes
  features/
    orders/
      data/                    # OrdersApi (dio), OrdersDao (drift), dto/ (freezed)
      domain/                  # Order entity, OrdersRepository interface
      application/             # providers / blocs / notifiers
      presentation/            # orders_page.dart, widgets/order_tile.dart
    auth/
    settings/
  core/
    design_system/             # tokens.dart, ThemeExtensions, AppButton, AppCard
    network/                   # dio client, interceptors (auth, retry, logging)
    storage/                   # drift database, secure storage wrapper
    l10n/                      # ARB files (gen-l10n)
    utils/
test/                          # mirrors lib/ (unit + widget + golden)
integration_test/              # on-device flows
android/ ios/ macos/ windows/  # platform runners, signing, entitlements
pubspec.yaml
analysis_options.yaml          # strict lints (flutter_lints / very_good_analysis)
```

- Feature-first, layered inside each feature (data → domain → application → presentation); presentation never calls dio/drift directly.
- Generated code (`*.g.dart`, `*.freezed.dart`) via build_runner; decide once whether to commit it.
- One `ThemeData` source of truth in `core/design_system`; widgets read tokens from `Theme.of(context)`.
- Use flavors (`--flavor` + `--dart-define-from-file`) for dev/staging/prod.

## Routing & navigation

- **go_router** (Flutter team maintained): declarative URL routes, `redirect` for auth, `StatefulShellRoute` for bottom tabs with preserved stacks, deep links handled out of the box.
- Typed routes via `go_router_builder`; alternatives: auto_route.
- Deep/universal links: Associated Domains (iOS) and verified App Links (Android) point to the same route table.
- Modals: `showModalBottomSheet`, `showDialog`, or dedicated routes when they must be deep-linkable.
- Handle Android predictive back via `PopScope` instead of the deprecated `WillPopScope`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | Riverpod `AsyncNotifier`/`FutureProvider` (caching, refresh, invalidation) or Bloc + repository; HTTP via **dio** (interceptors) or `http` |
| Models / serialization | **freezed** + json_serializable (immutable, unions, `copyWith`) |
| Local persistence / offline DB | **drift** (typed SQLite, migrations, reactive streams); `sqflite` for raw SQL |
| Key-value / prefs | `shared_preferences`; secrets in `flutter_secure_storage` (Keychain/Keystore) |
| Forms + validation | `Form` + `TextFormField.validator`; `flutter_form_builder` or `reactive_forms` for complex forms |
| UI state | `StatefulWidget`/`ValueNotifier`, `flutter_hooks` if using hooks |
| App-wide state | **Riverpod** (compile-safe, testable) or **Bloc/Cubit** (explicit events, great for large teams) |
| DI | Riverpod providers double as DI; with Bloc use `get_it` (+ `injectable`) or `RepositoryProvider` |

## Styling & design system

- Material 3 by default: `ColorScheme.fromSeed`, `ThemeData(colorScheme: ...)`, component themes (`FilledButtonTheme`, `CardTheme`).
- Custom tokens via `ThemeExtension<T>` (spacing, brand colors, elevations) — accessible through `Theme.of(context).extension<AppTokens>()`.
- iOS feel: Cupertino widgets or `.adaptive` constructors (`Switch.adaptive`, `CircularProgressIndicator.adaptive`); decide per screen whether to adapt or stay brand-uniform.
- Dark mode: `theme` + `darkTheme` + `themeMode`; never hardcode `Colors.*` in features.
- Font scaling: respect `MediaQuery.textScalerOf(context)`; test at 200% — avoid fixed-height text containers.
- Responsive: `LayoutBuilder`, `MediaQuery.sizeOf`, breakpoints for tablet/desktop (adaptive scaffolds).

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz across UI + raster threads; check the DevTools performance overlay and timeline in **profile mode** (`flutter run --profile`).
- Use `const` constructors, split large `build` methods into widgets, scope rebuilds (`select` in Riverpod, `BlocSelector`, `buildWhen`).
- Lists: `ListView.builder`/`SliverList` with item extents (`itemExtent`, `prototypeItem`); never build long lists eagerly.
- Images: `cached_network_image`; set `cacheWidth`/`cacheHeight` to decode at display size.
- Heavy CPU work (JSON parse of large payloads, crypto, image processing) in isolates: `Isolate.run` / `compute`.
- `RepaintBoundary` around independently animating regions; avoid `Opacity`/`ClipPath`/`saveLayer` on large subtrees.
- App size: `--analyze-size`, `--split-debug-info` + `--obfuscate`, `--split-per-abi` for APKs (AAB handles it), deferred components (Android).
- Background work: `workmanager` plugin (Android WorkManager / iOS BGTaskScheduler).

## Accessibility

- Most Material/Cupertino widgets expose semantics automatically; custom widgets need `Semantics(label:, button:, header:, value:, onTap:)`.
- `MergeSemantics` to group, `ExcludeSemantics` for decoration, `SemanticsService.announce` for live updates.
- Focus order: `FocusTraversalGroup`, `OrdinalSortKey`; visible focus for keyboard/desktop.
- Tap targets ≥ 48 dp (Material default `MaterialTapTargetSize.padded`) / 44 pt iOS.
- Widget-test guidelines: `expect(tester, meetsGuideline(androidTapTargetGuideline))`, `iOSTapTargetGuideline`, `labeledTapTargetGuideline`, `textContrastGuideline`.
- Manual: VoiceOver, TalkBack, Accessibility Inspector, Android Accessibility Scanner; DevTools semantics tree.

## Testing

| Level | Tooling |
|---|---|
| Unit | `flutter_test`/`test`, `mocktail`, `bloc_test` or Riverpod `ProviderContainer` overrides |
| Widget | `testWidgets` + `WidgetTester` (fast, headless) |
| Golden | `matchesGoldenFile` (pin fonts/platform in CI to avoid flake) |
| Integration/E2E | `integration_test` on devices/Firebase Test Lab; **Patrol** for native dialogs/permissions; Maestro also works |

## Build & deploy

- `flutter build appbundle` / `flutter build ipa`; desktop: `flutter build windows|macos|linux` + platform packaging (MSIX, dmg).
- CI/CD: **Codemagic** (Flutter-focused), GitHub Actions + **Fastlane**, Bitrise, Xcode Cloud for iOS.
- Signing: Play App Signing + upload key; Apple certificates/profiles via Fastlane match or CI-managed.
- OTA: Dart code is AOT-compiled; code-push requires a third-party service (e.g. Shorebird). Store policy still applies — no changing the app's purpose via OTA; native/plugin changes need a store build.
- Crash/perf monitoring: Firebase Crashlytics or Sentry with uploaded debug symbols (obfuscation maps).

## Pitfalls

- Measuring performance in debug mode (JIT) — always profile/release.
- One giant `build()` with `setState` at the root, rebuilding the whole screen per keystroke.
- Calling `context` across async gaps without checking `mounted`.
- Plugin quality varies: check maintenance, platform coverage and federated implementations before adopting.
- Flutter web for content/SEO sites; use it only for app-like experiences.
- Ignoring platform conventions (back gestures, text selection, scroll physics) and shipping "Android on iPhone".
- Uncommitted or stale generated code breaking CI.

## References

- https://docs.flutter.dev/
- https://docs.flutter.dev/app-architecture
- https://docs.flutter.dev/perf/best-practices
- https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility
- https://pub.dev/packages/go_router
- https://riverpod.dev/
