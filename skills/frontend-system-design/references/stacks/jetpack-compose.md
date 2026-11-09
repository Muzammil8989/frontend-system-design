# Jetpack Compose (native Android)

> **Platform:** mobile (Android phones, tablets, foldables, Wear OS, TV, ChromeOS) · **Language:** Kotlin · **Rendering:** native Android UI toolkit (Compose runtime + Android graphics) · **Best for:** Android-first products that need full platform integration, Material 3 and long-term maintainability

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Android is primary, or you are building separate native apps per platform | You need iOS too with one small team — consider Compose Multiplatform/KMP, Flutter or RN |
| Deep OS integration: background work, widgets (Glance), Wear OS, Android Auto, foreground services | Team has only web skills and must ship both platforms fast |
| Material 3 + dynamic color + adaptive layouts for foldables/tablets matter | You must support very old Android versions below Compose's minimum SDK |
| Performance-sensitive UI where native rendering and Baseline Profiles help | Heavily View-based legacy app with no capacity to migrate incrementally (still possible via `ComposeView` interop) |
| You want official Google tooling (Android Studio, Previews, Macrobenchmark) | Product is mostly content best served by the web |

## Project structure

```text
app/                              # application module: MainActivity, NavHost, Hilt app
  src/main/java/com/acme/shop/
    ShopApplication.kt            # @HiltAndroidApp
    MainActivity.kt               # setContent { ShopTheme { ShopNavHost() } }
    navigation/ShopNavHost.kt
feature/
  orders/                         # one Gradle module per feature
    src/main/.../orders/
      OrdersRoute.kt              # @Serializable route objects + navGraphBuilder ext
      OrdersScreen.kt             # stateless composable (state in, events out)
      OrdersViewModel.kt          # @HiltViewModel, StateFlow<OrdersUiState>
      components/OrderRow.kt
  checkout/
  settings/
core/
  designsystem/                   # ShopTheme, color/typography/shape tokens, components
  data/                           # repositories (offline-first), sync workers
  database/                       # Room DB, DAOs, entities, migrations
  network/                        # Retrofit/Ktor service, DTOs, OkHttp interceptors
  datastore/                      # Proto/Preferences DataStore
  model/                          # pure Kotlin domain models
  testing/                        # fakes, test rules, test dispatchers
build-logic/                      # convention plugins (android-library, compose, hilt)
gradle/libs.versions.toml         # version catalog
baselineprofile/                  # Baseline Profile generator module
```

- Feature modules depend on `core:*`, never on other features; navigation wired in `app`.
- Screens split into a stateful `XRoute` (gets ViewModel) and stateless `XScreen` (previewable, testable).
- Repositories expose `Flow`; Room is the single source of truth for offline-first data.
- Convention plugins + version catalog keep module build files to a few lines.

## Routing & navigation

- **Navigation Compose** with type-safe `@Serializable` route classes; nested graphs per feature; `NavHost` in `app`.
- **Navigation 3** is the newer library where you own the back stack as state — evaluate for new projects, especially adaptive multi-pane UIs.
- Bottom/rail/drawer chosen by window size: `NavigationSuiteScaffold` (Material 3 adaptive); list–detail via `ListDetailPaneScaffold`.
- Deep links: `navDeepLink` on destinations + verified **Android App Links** (`assetlinks.json`, `autoVerify`).
- Support predictive back (`BackHandler`/`PredictiveBackHandler`, enable in manifest).

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | Retrofit + OkHttp (or Ktor client) + kotlinx.serialization; cache into Room; Paging 3 for paged lists |
| Local persistence / offline DB | **Room** (Flow queries, migrations); sync via **WorkManager** |
| Key-value / prefs | **DataStore** (Preferences or Proto); secrets encrypted with Android Keystore keys |
| Forms + validation | ViewModel-held form state (`TextFieldState`/`mutableStateOf`), validation in ViewModel or domain use cases, errors in UiState |
| UI state | `remember`, `rememberSaveable`; hoist to the lowest common parent |
| Screen state | **ViewModel + StateFlow<UiState>** collected with `collectAsStateWithLifecycle()`; one-off events as state, not SharedFlow toasts |
| App-wide state | Singleton repositories exposing `StateFlow`, scoped by Hilt |
| DI | **Hilt** (`@HiltViewModel`, `hiltViewModel()`); Koin is a lighter alternative |

## Styling & design system

- **Material 3**: `MaterialTheme(colorScheme, typography, shapes)`; generate schemes with Material Theme Builder.
- Dynamic color (`dynamicLightColorScheme`/`dynamicDarkColorScheme`) on supported Android versions, brand fallback otherwise.
- Custom tokens via `CompositionLocal` (`LocalSpacing`, `LocalBrandColors`) wrapped in a `ShopTheme` object.
- Dark mode: `isSystemInDarkTheme()`; edge-to-edge with proper `WindowInsets` handling.
- Font scaling: text in `sp`, avoid fixed heights on text containers; test at max font scale and display size.
- Adaptive: window size classes for phone/tablet/foldable/desktop-mode layouts.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz; inspect with Layout Inspector recomposition counts and system tracing.
- **Baseline Profiles** (+ Startup Profiles) improve startup and first-run jank; generate with Macrobenchmark, ship in release.
- Release builds with **R8** full mode and resource shrinking; profile release/benchmark variants, never debug.
- Stability: immutable UI models (`@Immutable`/`@Stable`, kotlinx immutable collections); strong skipping reduces wasted recomposition.
- Defer state reads: lambda modifiers (`Modifier.offset { }`, `graphicsLayer { }`), `derivedStateOf` for threshold-derived values.
- Lists: `LazyColumn`/`LazyVerticalGrid` with `key` and `contentType`; Paging 3 for large data.
- Images: **Coil** (memory/disk cache, size-aware decoding).
- Startup: App Startup library, lazy Hilt bindings, SplashScreen API; avoid disk/network on main thread (StrictMode in debug).
- Background: WorkManager for deferrable guaranteed work; foreground services only with a declared type and user-visible reason.

## Accessibility

- Semantics: `contentDescription` on icons/images, `Modifier.semantics { role; stateDescription; heading(); contentDescription }`.
- Grouping: `Modifier.semantics(mergeDescendants = true)`, `clearAndSetSemantics {}` for custom composites; `Modifier.toggleable`/`selectable` give roles for free.
- Traversal order: `isTraversalGroup` and `traversalIndex`.
- Touch targets ≥ 48 dp: Material components enforce `minimumInteractiveComponentSize()`; apply it to custom clickables.
- Live updates: `liveRegion` semantics; custom actions via `customActions`.
- Test: TalkBack, Switch Access, Accessibility Scanner; semantics assertions in Compose UI tests; automated accessibility checks (Accessibility Test Framework) in UI tests.

## Testing

| Level | Tooling |
|---|---|
| Unit | JUnit, kotlinx-coroutines-test (`runTest`, test dispatchers), **Turbine** for Flows, MockK or hand-written fakes |
| ViewModel | Fake repositories from `core:testing`; assert `UiState` sequences |
| Compose UI | `createComposeRule` / `createAndroidComposeRule`; finders by semantics (`onNodeWithText`, `onNodeWithContentDescription`); run on JVM with Robolectric |
| Screenshot | Roborazzi, Paparazzi or Compose Preview Screenshot Testing |
| E2E | Espresso/UI Automator, Maestro; Firebase Test Lab / Gradle Managed Devices in CI |
| Perf | Macrobenchmark (startup, scroll jank), Baseline Profile generator |

## Build & deploy

- Gradle (Kotlin DSL), version catalog, convention plugins, configuration cache.
- Ship **Android App Bundles**; enable **Play App Signing** (keep the upload key in CI secrets).
- CI/CD: GitHub Actions/GitLab + Gradle Play Publisher or **Fastlane supply**; tracks internal → closed → open → production.
- Rollout: Play **staged rollouts** with halt; **In-App Updates API** (flexible/immediate) for prompting or forcing updates.
- Play policy: apps must not download executable code (dex/so) outside Play; use Play Feature Delivery for on-demand modules and remote config for behavior.
- Monitoring: Android vitals in Play Console, Crashlytics/Sentry with R8 mapping files uploaded.

## Pitfalls

- Collecting flows with `collectAsState()` without lifecycle awareness (wastes work in background).
- Passing ViewModels deep into the tree instead of state + lambdas — kills previews and testability.
- Unstable parameters (mutable `List`, classes from non-Compose modules) causing recomposition storms.
- Measuring performance on debug builds without Baseline Profiles.
- Business logic in composables or `LaunchedEffect` instead of ViewModel/use cases.
- Ignoring large screens, edge-to-edge insets and predictive back — now expected by Play quality guidelines.
- Storing tokens in plain SharedPreferences/DataStore.

## References

- https://developer.android.com/develop/ui/compose
- https://developer.android.com/topic/architecture
- https://developer.android.com/guide/navigation/design/type-safety
- https://developer.android.com/develop/ui/compose/performance
- https://developer.android.com/develop/ui/compose/accessibility
- https://m3.material.io/
