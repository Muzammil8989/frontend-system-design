# .NET MAUI

> **Platform:** cross (Android, iOS, macOS via Mac Catalyst, Windows via WinUI) · **Language:** C# + XAML (or C# markup) · **Rendering:** native platform controls via handlers (Blazor Hybrid option renders web UI in a WebView) · **Best for:** .NET/C# organizations building line-of-business, field-service and enterprise apps across mobile and Windows

## When to choose

| Choose it when | Avoid it when |
|---|---|
| Team and backend are .NET; want shared C# models, validation and services | Consumer app where polish, motion and newest platform UI are the differentiator |
| Enterprise/LOB: forms, data grids, offline field work, Windows desktop + mobile | You need the largest third-party mobile ecosystem (RN/Flutter/native have more) |
| Migrating from Xamarin.Forms (MAUI is its successor) | Linux desktop is required (no official Linux target) |
| Want to reuse Razor components via **Blazor Hybrid** inside a native shell | Team has no C# experience |
| Commercial control suites (grids, charts, schedulers) are acceptable/desired | You need OTA code updates (not available for compiled .NET apps) |

## Project structure

```text
src/
  Acme.Field.App/                    # single MAUI project, multi-targeted
    MauiProgram.cs                   # builder: DI registrations, fonts, handlers, logging
    App.xaml(.cs)                    # resources, theme
    AppShell.xaml(.cs)               # Shell: TabBar/Flyout, route registration
    Features/
      Jobs/
        JobsPage.xaml(.cs)
        JobsViewModel.cs             # ObservableObject, [ObservableProperty], [RelayCommand]
        JobDetailPage.xaml(.cs)
        JobDetailViewModel.cs        # IQueryAttributable for nav params
      Auth/
      Settings/
    Resources/
      Styles/Colors.xaml             # color tokens (Light/Dark via AppThemeBinding)
      Styles/Styles.xaml             # implicit/explicit styles
      Fonts/ Images/ Raw/ Splash/ AppIcon/
    Platforms/
      Android/ iOS/ MacCatalyst/ Windows/   # platform entry points, manifests, entitlements
  Acme.Field.Core/                   # netX class library: models, services, validation
    Services/IJobsApi.cs             # Refit interface
    Data/LocalDb.cs                  # SQLite access
  Acme.Field.Core.Tests/             # xUnit tests for ViewModels/services
  Acme.Field.UITests/                # Appium tests
```

- Keep ViewModels and services in a plain class library (no MAUI references) so they are unit-testable on any runner.
- Register pages and ViewModels in DI (`builder.Services.AddTransient<JobsPage>()`), let Shell resolve them.
- Platform code goes in `Platforms/*` or partial classes; wrap it behind interfaces.
- Use compiled bindings (`x:DataType`) on every page.

## Routing & navigation

- **Shell**: declare hierarchy with `TabBar`, `FlyoutItem`, `ShellContent`; register detail routes with `Routing.RegisterRoute`.
- Navigate with URIs: `await Shell.Current.GoToAsync($"jobdetail?id={id}")`; `".."` to go back; pass objects via `ShellNavigationQueryParameters`.
- Receive parameters with `IQueryAttributable` (preferred) or `[QueryProperty]`.
- Modals: `Shell.PresentationMode="Modal"` on the page or `Navigation.PushModalAsync`.
- Deep links: App Links/Universal Links handled in platform lifecycle events (`ConfigureLifecycleEvents`) and forwarded to Shell routes.
- Wrap navigation in an `INavigationService` so ViewModels stay testable.

## State & data

| State kind | Recommended tool |
|---|---|
| Server/remote state & caching | `HttpClient` via `IHttpClientFactory` + **Refit**; resilience with Polly/`Microsoft.Extensions.Http.Resilience`; cache in local DB |
| Local persistence / offline DB | **sqlite-net-pcl** (simple) or **EF Core SQLite**; sync with your API (or Datasync community toolkit) |
| Key-value / secrets | `Preferences` for settings; `SecureStorage` (Keychain/Keystore/DPAPI) for tokens |
| Forms + validation | **CommunityToolkit.Mvvm** `ObservableValidator` + DataAnnotations; show errors via bindings |
| UI state | ViewModel properties (`[ObservableProperty]`), `VisualStateManager` for visual states |
| App-wide state | Singleton services in DI; `WeakReferenceMessenger` for decoupled messages |
| DI | Built-in `Microsoft.Extensions.DependencyInjection` in `MauiProgram` |

## Styling & design system

- Tokens as `ResourceDictionary` entries (`Colors.xaml`, spacing as `Thickness`, font sizes); consume with `StaticResource` (or `DynamicResource` for runtime theme switching).
- Dark mode: `AppThemeBinding Light=..., Dark=...`; `Application.Current.UserAppTheme` to override.
- Platform conventions: Shell renders native tab bars/navigation; follow HIG on iOS, Material on Android, Fluent on Windows where it matters (`OnPlatform`/`OnIdiom`).
- Component libraries: **.NET MAUI Community Toolkit** (behaviors, converters, popups), commercial suites (Syncfusion, Telerik, DevExpress), UraniumUI for Material-style controls.
- Font scaling: `FontAutoScalingEnabled` (default true) respects OS text size; avoid fixed `HeightRequest` on text.

## Performance

- Frame budget 16.7 ms @60 Hz, 8.3 ms @120 Hz; layout cost dominates — flatten nested `StackLayout`s, prefer `Grid`.
- Compiled bindings (`x:DataType`) instead of reflection bindings.
- Lists: **CollectionView** (virtualized) with `DataTemplate`s; avoid `ScrollView` + `BindableLayout` for large data.
- Startup: trimming, AOT options (profiled AOT on Android; Native AOT for iOS/Mac Catalyst where libraries are compatible), lazy service creation, avoid heavy work in `App` constructor.
- Images: size assets at build time via MAUI resizetizer; cache remote images (built-in `UriImageSource` caching or a library such as FFImageLoading.Maui).
- Memory: unsubscribe events, avoid page/ViewModel leaks (transient pages + messenger weak refs); check with platform profilers and `dotnet-trace`/`dotnet-counters`.
- Background work: platform APIs (WorkManager, BGTaskScheduler) via platform-specific code.

## Accessibility

- `SemanticProperties.Description`, `SemanticProperties.Hint`, `SemanticProperties.HeadingLevel` map to VoiceOver/TalkBack/Narrator.
- `SemanticScreenReader.Announce(...)` for live updates; `SemanticExtensions.SetSemanticFocus()` to move focus.
- `AutomationProperties.IsInAccessibleTree`/`ExcludedWithChildren` to hide decorative elements.
- Focus/tab order: `TabIndex`, `IsTabStop` (Windows/keyboard).
- Touch targets ≥ 44 pt iOS / 48 dp Android (`MinimumHeightRequest`/`MinimumWidthRequest`).
- Test with VoiceOver, TalkBack, Narrator; Accessibility Insights for Windows; Xcode Accessibility Inspector.

## Testing

| Level | Tooling |
|---|---|
| Unit | xUnit/NUnit/MSTest on `Core` library; NSubstitute/Moq for service fakes |
| ViewModel | Test commands, validation and navigation via mocked `INavigationService` |
| UI/E2E | **Appium** (UiAutomator2, XCUITest, WinAppDriver/Windows drivers) using `AutomationId`; Maestro for mobile |
| Device | Real devices/emulators in CI; device farms (BrowserStack, Sauce Labs) |

## Build & deploy

- `dotnet build` / `dotnet publish -f net*-android|ios|maccatalyst|windows`; workloads installed in CI.
- CI/CD: GitHub Actions or Azure DevOps (macOS agents for iOS/Mac Catalyst); Fastlane for store upload.
- Signing: Android keystore (AAB to Play with Play App Signing); Apple certs/profiles; Windows MSIX signed with a trusted certificate.
- Distribution: App Store/TestFlight, Play tracks, Microsoft Store or MSIX/App Installer for enterprise; MDM for internal apps.
- No OTA code push — ship through stores; use remote config/feature flags. (Visual Studio App Center has been retired; do not plan around it.)
- Monitoring: Sentry, Azure Application Insights/OpenTelemetry, or Firebase Crashlytics via bindings.

## Pitfalls

- Reflection bindings everywhere (missing `x:DataType`) → slow, runtime-only errors.
- Deeply nested layouts and `StackLayout` inside `ScrollView` inside `CollectionView`.
- Using legacy `ListView`/`Frame`-heavy patterns copied from Xamarin.Forms samples.
- Assuming identical behavior on Windows/Mac Catalyst — test each target; desktop needs keyboard, mouse, resizing.
- Trimming/AOT breaking reflection-based libraries — test release configurations early.
- Planning around App Center or any OTA mechanism.
- Ignoring third-party library maintenance status for MAUI targets.

## References

- https://learn.microsoft.com/dotnet/maui/
- https://learn.microsoft.com/dotnet/maui/fundamentals/shell/navigation
- https://learn.microsoft.com/dotnet/communitytoolkit/mvvm/
- https://learn.microsoft.com/dotnet/maui/fundamentals/accessibility
- https://learn.microsoft.com/dotnet/maui/deployment/
- https://learn.microsoft.com/dotnet/communitytoolkit/maui/
