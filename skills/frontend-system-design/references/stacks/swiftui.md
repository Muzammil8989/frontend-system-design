# SwiftUI (native Apple)

> **Platform:** mobile (iOS, iPadOS; also macOS, watchOS, tvOS, visionOS) · **Language:** Swift · **Rendering:** native Apple UI frameworks (SwiftUI over UIKit/AppKit) · **Best for:** Apple-first products that need best-in-class platform feel, performance and day-one OS features

## When to choose

| Choose it when | Avoid it when |
|---|---|
| iOS (or Apple ecosystem) is the primary or only platform | You need Android parity with one small team — consider KMP, Flutter or RN |
| You need deep OS integration: widgets, Live Activities, App Intents, extensions, watch, visionOS | You have to target older OS versions where SwiftUI APIs you need are missing (fallback to UIKit) |
| Performance, battery and accessibility must be first-class | Team has only web skills and a tight deadline |
| You want new platform features as soon as they ship | Highly custom, cross-platform-identical branded UI is the goal |
| Long-lived product where native maintainability beats code sharing | Business logic must be shared with Android (then share logic via KMP, keep SwiftUI UI) |

## Project structure

```text
MyApp.xcodeproj                 # thin app target; most code in local Swift packages
MyApp/
  MyAppApp.swift                # @main App, WindowGroup, ModelContainer, environment
  AppRouter.swift               # NavigationPath per tab, deep-link handling
  Resources/Assets.xcassets     # semantic colors, app icon
  Resources/Localizable.xcstrings
Packages/
  Features/
    Sources/Orders/
      OrdersListView.swift
      OrderDetailView.swift
      OrdersModel.swift         # @Observable @MainActor feature model
    Sources/Auth/
    Sources/Settings/
  Core/
    Sources/Networking/         # APIClient (URLSession async/await), Endpoint, DTOs (Codable)
    Sources/Persistence/        # SwiftData @Model types or Core Data stack
    Sources/DesignSystem/       # Tokens, ButtonStyles, ViewModifiers, components
    Sources/Domain/             # entities, repository protocols
  Tests/                        # Swift Testing / XCTest per package
MyAppUITests/                   # XCUITest flows
Widgets/                        # WidgetKit extension sharing Core packages
```

- Modularize with local Swift packages: faster incremental builds, enforced access control (`public` only what features need).
- Views stay declarative and dumb; side effects live in `@Observable` models or services injected via `@Environment`.
- Domain/Networking packages must not import SwiftUI so they are reusable by widgets, extensions and tests.
- Enable strict concurrency checking; mark UI models `@MainActor`.

## Routing & navigation

- **NavigationStack** with a `NavigationPath` (or typed `[Route]` array) owned by a router model; `navigationDestination(for:)` maps values to views.
- **NavigationSplitView** for iPad/macOS sidebar–detail layouts; **TabView** with one stack per tab.
- Modals: `.sheet` (with `presentationDetents`), `.fullScreenCover`, `.popover`, `.inspector`; confirmation via `.confirmationDialog`/`.alert`.
- Deep links: `.onOpenURL` for custom schemes and Universal Links (Associated Domains + `apple-app-site-association`); parse URL → push routes on the path.
- State restoration: make routes `Codable`, persist `NavigationPath.codable` with `@SceneStorage`.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | `URLSession` async/await + `Codable` in an `APIClient`; caching in repository layer (in-memory + `URLCache` or persisted store) |
| Local persistence / offline DB | **SwiftData** (`@Model`, `@Query`, `ModelContainer`) for new apps; **Core Data** for mature/complex needs; GRDB for direct SQLite |
| Sync | CloudKit (via SwiftData/`NSPersistentCloudKitContainer`) or custom sync with your backend |
| Secrets | Keychain (Security framework or a small wrapper) |
| Prefs | `@AppStorage` / `UserDefaults` (non-sensitive only) |
| Forms + validation | `Form` + bound `@Observable` model; validate in model computed properties; `.disabled(!isValid)` |
| UI state | `@State`, `@Binding`, `@FocusState`, `@SceneStorage` |
| App-wide state | `@Observable` models injected with `.environment(model)`; read via `@Environment(Model.self)` |
| DI | Environment values/objects; protocols + initializer injection; swift-dependencies if you want a library |

## Styling & design system

- Follow **Apple HIG**: system fonts, SF Symbols, standard controls, navigation bars, sheets, materials.
- Tokens: semantic colors in the asset catalog (Any/Dark + high-contrast variants), spacing/radius constants in `DesignSystem`, custom `ButtonStyle`, `LabelStyle`, `ViewModifier`s.
- Dark mode is automatic with semantic colors (`Color.primary`, `.background`, asset colors); never hardcode RGB for surfaces/text.
- Dynamic Type: use text styles (`.font(.body)`, `.headline`), `@ScaledMetric` for custom sizes/padding, `ViewThatFits` and `dynamicTypeSize` checks to switch layouts at accessibility sizes.
- Multiplatform: adapt with size classes (`horizontalSizeClass`) and platform-conditional modifiers.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz (ProMotion); keep `body` cheap and side-effect free.
- Minimize invalidation: Observation tracks per-property access — read only what a view needs; split big views into subviews.
- Stable identity: `ForEach` with stable `id`s; avoid `AnyView` and conditional view identity churn.
- Lists: `List` or `LazyVStack`/`LazyVGrid` inside `ScrollView` for long content.
- Images: `AsyncImage` does not provide a persistent cache — use a cache-aware loader (e.g. Nuke, Kingfisher) or your own `URLCache` policy; downsample large images.
- Concurrency: async work in `.task {}` (auto-cancelled), heavy compute off the main actor.
- Startup: defer non-critical initialization, avoid blocking main thread in `App.init`; measure with Instruments (App Launch, SwiftUI, Time Profiler, Hangs) and MetricKit in production.
- Background work: `BackgroundTasks` (`BGAppRefreshTask`, `BGProcessingTask`) — system-scheduled, never guaranteed.

## Accessibility

- Standard controls are accessible by default; for custom views add `.accessibilityLabel`, `.accessibilityValue`, `.accessibilityHint`, `.accessibilityAddTraits(.isButton/.isHeader)`.
- Group with `.accessibilityElement(children: .combine)`; custom actions via `.accessibilityAction`; rotors via `.accessibilityRotor`.
- Focus: `@AccessibilityFocusState` to move VoiceOver focus; `.accessibilitySortPriority` to fix order.
- Respect Dynamic Type, Reduce Motion (`accessibilityReduceMotion`), Increase Contrast, Bold Text, Smart Invert.
- Touch targets ≥ 44×44 pt (`.contentShape`, `.frame(minWidth:minHeight:)`).
- Test: VoiceOver on device, Xcode Accessibility Inspector, Xcode previews at accessibility sizes, automated audits in XCUITest (`performAccessibilityAudit`).

## Testing

| Level | Tooling |
|---|---|
| Unit | **Swift Testing** (`@Test`, `#expect`, parameterized tests) for new code; XCTest still supported |
| Model/integration | Test `@Observable` models with injected fake services; in-memory `ModelContainer` for SwiftData |
| Snapshot | swift-snapshot-testing (Point-Free) across sizes, dark mode, Dynamic Type |
| UI/E2E | XCUITest (accessibility identifiers), Maestro as an alternative |
| Perf | XCTest performance metrics (`XCTApplicationLaunchMetric`), Instruments |

## Build & deploy

- Xcode + Swift Package Manager; `xcodebuild` / Fastlane (`gym`, `match`, `pilot`, `deliver`) or **Xcode Cloud**.
- Signing: automatic signing locally; CI uses App Store Connect API keys and shared certificates (Fastlane match or Xcode Cloud managed).
- Distribution: TestFlight (internal/external testers) → App Store with **phased release**; macOS outside the store needs Developer ID signing + notarization.
- No OTA for native code: App Store guidelines forbid downloading executable code that changes features; use server-driven config/feature flags instead.
- Crash/metrics: Xcode Organizer, MetricKit, Crashlytics or Sentry with dSYMs uploaded.

## Pitfalls

- Doing work (network, formatting, sorting) inside `body` — it runs often.
- Mixing `ObservableObject`/`@Published` and `@Observable` semantics inconsistently; prefer Observation for new code.
- One global NavigationStack across tabs, losing per-tab history.
- Ignoring minimum deployment target: newest SwiftUI APIs require recent OS versions — gate with `#available` or fall back to UIKit via `UIViewRepresentable`.
- Massive single app target → slow builds and tangled dependencies.
- Assuming `AsyncImage` caches across launches.
- Main-actor-blocking work causing hangs reported in Organizer.

## References

- https://developer.apple.com/documentation/swiftui
- https://developer.apple.com/design/human-interface-guidelines/
- https://developer.apple.com/documentation/observation
- https://developer.apple.com/documentation/swiftdata
- https://developer.apple.com/documentation/testing
- https://developer.apple.com/documentation/swiftui/accessibility-fundamentals
