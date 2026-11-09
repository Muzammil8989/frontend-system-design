# Kotlin Multiplatform + Compose Multiplatform

> **Platform:** cross (Android, iOS, desktop JVM; web via Wasm is less mature) · **Language:** Kotlin · **Rendering:** Jetpack Compose on Android; Skia-based (Skiko) canvas on iOS/desktop/web, with native view interop · **Best for:** Kotlin/Android teams sharing logic (and optionally UI) with iOS while keeping a native escape hatch

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Team is strong in Kotlin/Android and needs iOS without a second full team | Team is web/React-centric — RN/Expo will be faster |
| You want to share domain, data, networking and persistence — UI sharing optional per screen | iOS must be 100% native look with zero custom-drawn UI (share logic only, write SwiftUI UI) |
| Gradual adoption into existing native apps (KMP module embedded as a framework) | You need a mature web target for a public, SEO-relevant site |
| Desktop JVM app from the same codebase is a plus | Heavy reliance on iOS-only third-party SDKs without Kotlin/Swift bridging capacity |
| You value type-safe shared models across mobile (and Kotlin backend) | You need the largest ecosystem of ready-made UI packages today |

## Project structure

```text
composeApp/                       # shared Compose UI + app wiring
  src/
    commonMain/kotlin/com/acme/
      App.kt                      # root composable: theme + NavHost
      navigation/AppNavGraph.kt
      feature/orders/
        OrdersScreen.kt           # shared composable
        OrdersViewModel.kt        # androidx lifecycle ViewModel (multiplatform)
      di/AppModule.kt             # Koin modules
    androidMain/kotlin/           # MainActivity, Android-specific actuals
    iosMain/kotlin/               # MainViewController(), UIKit interop actuals
    desktopMain/kotlin/           # main() { application { Window { App() } } }
    commonTest/kotlin/
shared/                           # (optional split) pure logic, no UI
  src/commonMain/kotlin/com/acme/
    data/remote/                  # Ktor HttpClient, DTOs (kotlinx.serialization)
    data/local/                   # SQLDelight .sq files or Room KMP database
    domain/                       # entities, repositories, use cases
  src/androidMain/ src/iosMain/   # expect/actual: engines, drivers, secure storage
iosApp/                           # Xcode project; embeds the Kotlin framework
  iosApp/ContentView.swift        # hosts ComposeUIViewController or SwiftUI screens
gradle/libs.versions.toml
```

- Keep `commonMain` free of platform types; isolate platform code behind `expect`/`actual` or interfaces injected via DI.
- Split `shared` (logic) from `composeApp` (UI) if any platform may use native UI (SwiftUI) instead of shared UI.
- One Kotlin framework exported to iOS; expose a small, Swift-friendly API surface (use SKIE or KMP-NativeCoroutines for Flow/suspend ergonomics).
- Per-screen choice: shared Compose UI by default; drop to SwiftUI/UIKit (`UIKitView`/`UIKitViewController`) for maps, camera, platform-critical screens.

## Routing & navigation

- **Navigation Compose for Multiplatform** (JetBrains-published `androidx.navigation` port) with type-safe serializable routes — the default for new projects.
- **Decompose**: lifecycle-aware component tree, navigation logic outside UI, works with SwiftUI too; **Voyager**: simple screen-based navigation.
- Deep links: platform entry points (Android intent, iOS `onOpenURL`/scene delegate) parse URL and forward a route into shared navigation.
- Respect platform back: Android system/predictive back; iOS swipe-back — verify gesture behavior on shared screens.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | **Ktor client** (platform engines: OkHttp/Darwin) + kotlinx.serialization; cache in local DB; Store5 if you want a caching library |
| Local persistence / offline DB | **SQLDelight** (SQL-first, typed, multiplatform drivers) or **Room** (KMP-supported) |
| Key-value / prefs | DataStore (KMP) or multiplatform-settings; secrets via `actual` Keychain/Keystore wrappers |
| Forms + validation | ViewModel-held form state; validation functions in `commonMain` (shared with backend if Kotlin) |
| UI state | `remember`, `rememberSaveable`; hoisted state in composables |
| Screen state | Multiplatform **ViewModel + StateFlow** (`collectAsStateWithLifecycle`), or Decompose components with `Value`/`StateFlow` |
| App-wide state | Repository singletons exposing `StateFlow` |
| DI | **Koin** (multiplatform, simple); kotlin-inject for compile-time DI |

## Styling & design system

- Material 3 (`MaterialTheme`) works everywhere; build a brand theme with tokens in `commonMain` (colors, typography, shapes, spacing via `CompositionLocal`).
- Platform conventions: decide per product whether iOS gets Material-styled brand UI or Cupertino-like adaptations (system fonts, back-swipe, sheet styles); third-party adaptive/Cupertino component libraries exist but evaluate maintenance.
- Resources (strings, images, fonts) via Compose Multiplatform resources (`Res.string.*`, `Res.drawable.*`).
- Dark mode: `isSystemInDarkTheme()` works cross-platform.
- Font scaling: use `sp`; verify iOS Dynamic Type mapping on device at large sizes.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz (ProMotion iPhones); profile iOS with Xcode Instruments, Android with Macrobenchmark/Perfetto.
- Same Compose rules as Android: stable/immutable UI models, `key` in lazy lists, defer state reads, `derivedStateOf`.
- iOS: Kotlin/Native compiles to native code; watch framework size and first-frame time; use release frameworks for measurement.
- Lists: `LazyColumn`/`LazyVerticalGrid` everywhere; Paging (multiplatform artifacts) for large data.
- Images: **Coil** (multiplatform) with memory/disk cache and size-aware decoding.
- App size: shared UI adds the Skia-based runtime to iOS binaries — measure against your size budget early.
- Background work: platform-specific (WorkManager / BGTaskScheduler) behind `expect`/`actual`; shared code runs inside those jobs.
- Coroutines: use `Dispatchers.Default` for CPU work; avoid freezing the main thread in iOS interop calls.

## Accessibility

- Compose semantics (`contentDescription`, `semantics { role; heading(); stateDescription }`, `mergeDescendants`) map to TalkBack on Android and to the iOS accessibility tree via Compose Multiplatform's iOS integration.
- Verify every shared screen with **VoiceOver** on a real iPhone — custom-drawn UI has more edge cases than native views (focus order, traits, rotor).
- Touch targets ≥ 48 dp Android / 44 pt iOS (`minimumInteractiveComponentSize`).
- Desktop: keyboard focus traversal and visible focus indicators; screen reader support varies by OS — test with the target platform's reader.
- Respect reduce-motion and font-scale settings through platform `actual` queries where Compose does not expose them.

## Testing

| Level | Tooling |
|---|---|
| Unit (shared) | `kotlin.test` in `commonTest`, kotlinx-coroutines-test, Turbine for Flows; runs on JVM and iOS simulator targets |
| Data | SQLDelight in-memory drivers; Ktor `MockEngine` |
| UI (shared) | Compose Multiplatform UI testing (`runComposeUiTest`) in common tests; Android `createComposeRule` |
| Native E2E | Espresso/UI Automator on Android, XCUITest on iOS; Maestro for both from one flow file |
| Swift interop | XCTest/Swift Testing against the exported framework API |

## Build & deploy

- Gradle with the Kotlin Multiplatform plugin; Android via AGP; iOS framework built by Gradle and embedded via an Xcode build phase (or SPM/CocoaPods integration).
- CI needs macOS runners for iOS targets; cache Kotlin/Native toolchains (`~/.konan`).
- Signing/distribution: standard Play (AAB, Play App Signing) and App Store/TestFlight flows; Fastlane for both.
- Desktop: Compose `nativeDistributions` (jpackage) produces dmg/msi/deb; sign + notarize macOS, sign Windows installers; Conveyor is an alternative with auto-update.
- No OTA for Kotlin code; use remote config/feature flags. Store policies on executable code apply.

## Pitfalls

- Leaking platform APIs into `commonMain` instead of clean `expect`/`actual` boundaries.
- Exposing raw `Flow`/`suspend`/sealed classes to Swift without interop tooling — awkward, error-prone Swift code.
- Assuming shared UI is automatically "native enough" on iOS — budget design time for iOS conventions.
- Ignoring iOS binary size and first-frame cost until late.
- Using libraries without the needed targets; check every dependency supports iOS (and desktop if needed).
- Slow Kotlin/Native builds in CI without caching; build only needed iOS architectures in debug.
- Treating Compose for Web (Wasm) as production-equivalent to the mobile targets without validating it.

## References

- https://kotlinlang.org/docs/multiplatform.html
- https://www.jetbrains.com/compose-multiplatform/
- https://github.com/JetBrains/compose-multiplatform
- https://ktor.io/docs/client-create-multiplatform-application.html
- https://sqldelight.github.io/sqldelight/
- https://insert-koin.io/docs/reference/koin-mp/kmp/
