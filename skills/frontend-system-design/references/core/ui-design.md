# UI system design

Aim for a UI that looks **intentional, consistent, and accessible**, and that fits the product's users and brand. Good visual design comes from a small set of systematic decisions applied consistently.

If they're installed, use **ui-ux-pro-max** for broader style, palette and font search, and **impeccable** or **frontend-design** for polish and critique.

## 1. Design direction (decide first)

Write the direction down before choosing any pixels:
- **Intent:** one sentence, e.g. *"A calm, trustworthy finance dashboard that makes anomalies jump out."*
- **3 adjectives:** e.g. *precise, calm, dense*.
- **Benchmark design systems:** 1–2 to learn from (see §7).
- **Signature element:** one memorable detail, e.g. a distinctive display font, an accent shape, or a data-viz colour language.

Direction by product type (starting points; override them for the brand):

| Product | Feel | Density | Notes |
|---|---|---|---|
| SaaS / dashboard | Calm, precise | Medium-high | Neutral surfaces, one accent, strong data-viz palette, tabular numbers |
| Fintech / banking | Trustworthy, secure | Medium | Restrained colour; clear positive and negative semantics (never colour alone) |
| E-commerce | Inviting, product-first | Medium | Large media, clear price and CTA hierarchy, sticky add-to-cart on mobile |
| Content / blog / docs | Readable, editorial | Low | 60–75 character measure, generous line height, strong typographic scale |
| Landing / marketing | Bold, memorable | Low | One idea per section, strong hero, social proof, a single primary CTA |
| Social / community | Lively, personal | Medium | Avatars, reactions, motion that gives feedback |
| Developer tools | Technical, efficient | High | Monospace accents, keyboard-first, a dark theme people actually use |
| Health / wellness | Calm, reassuring | Low | Soft palette, large touch targets, plain language |
| Kids / education | Playful, clear | Low | Rounded shapes, high contrast, large type, illustration |
| Enterprise / internal | Efficient, predictable | High | Dense tables, bulk actions, keyboard shortcuts, conservative styling |

Use `scripts/search.py --domain styles "<product mood>"` for named styles (e.g. minimal SaaS, glassmorphism, neo-brutalism, editorial, bento) and when each one is appropriate.

## 2. Design tokens

Define tokens as CSS custom properties, the single source of truth, and map component styles to **roles**, not raw values.

**Color roles**
- `--color-bg`, `--color-surface`, `--color-surface-raised`
- `--color-text`, `--color-text-muted`
- `--color-border`
- `--color-primary`, `--color-on-primary`
- `--color-accent`
- `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, each with an `-on-` pair
- `--color-focus-ring`

Rules:
- Text contrast is at least **4.5:1**, or **3:1** for large text (≥ 24 px, or ≥ 18.66 px bold).
- UI component boundaries and focus indicators are at least **3:1**.
- Define dark mode as a separate set of role values. Don't simply invert. Lower the saturation and avoid pure `#000` / `#fff` on large areas.
- Never use colour alone to convey meaning. Pair it with an icon, text, or pattern.
- For palettes, use `scripts/search.py --domain palettes "<industry mood>"`. Every palette in the dataset is contrast-checked.

**Typography**
- 1–2 families: a sans for UI, plus an optional display or serif for headings or editorial content.
- For pairings, use `scripts/search.py --domain fonts "<tone>"`.
- Use a modular scale (ratio 1.2–1.25 for apps, 1.25–1.333 for marketing). Base size is 16 px, never below 14 px for body text in apps.
- Line height is 1.4–1.6 for body text and 1.1–1.25 for headings. The reading measure is 60–75 characters.
- Use `font-variant-numeric: tabular-nums` for tables and metrics.
- Use `font-display: swap` or `optional`, preload only the one or two critical font files, prefer variable fonts, and subset them.

**Spacing, size, shape**
- Spacing uses a 4 px base: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- Radius uses 2–3 steps, e.g. 6 / 10 / 16. Keep it consistent per component family.
- Elevation uses 3 levels at most, built from shadow plus surface colour. In dark mode, use lighter surfaces rather than shadows.
- Breakpoints are content-driven. Typical values are ≈ 640 / 768 / 1024 / 1280 px. Use container queries for components.

**Motion**
- Durations are 100–200 ms for micro-interactions and 200–350 ms for larger transitions. Ease-out for entering, ease-in for exiting.
- Animate only `transform` and `opacity`.
- Respect `prefers-reduced-motion`.
- Motion explains a change. It is not decoration.

## 3. Component library choice

| Option | When |
|---|---|
| **Headless primitives + your styles** (Radix, React Aria, Ark UI, Headless UI) | You want a custom brand with accessibility handled for you |
| **Copy-in components** (shadcn/ui on Radix + Tailwind) | Fast start, full ownership of the code, easy theming through tokens |
| **Full design system** (MUI/Material, Chakra, Mantine, Ant Design, Fluent, Carbon, Polaris, PrimeVue, Vuetify, Angular Material) | Internal or enterprise tools where speed and consistency beat brand uniqueness |
| **Build your own** | Mature product with a dedicated design-system team. Still build on accessible primitives |

Styling: Tailwind CSS or CSS Modules with tokens are strong defaults. Avoid runtime CSS-in-JS in Server Component and streaming setups.

## 4. Layout and navigation patterns

| Pattern | Use for |
|---|---|
| Sidebar + top bar app shell | SaaS and dashboards with more than 5 sections; collapse to icons, then a drawer on mobile |
| Top nav + mega-menu | E-commerce and marketing sites with deep catalogs |
| Bottom tab bar (mobile) | 3–5 primary destinations in mobile-first apps |
| Command palette (⌘K) | Power users, developer tools, large apps |
| List–detail (master–detail) | Email, tickets, CRM. Split view on desktop, stacked on mobile |
| Bento grid | Marketing feature sections and dashboard overviews |
| Wizard / stepper | Long forms and onboarding: show progress, allow going back, save drafts |

For screen-level patterns (data table, filters, checkout, onboarding, empty states), use `scripts/search.py --domain patterns "<screen>"`.

## 5. Design every state

For each key screen and component, specify:

| State | Guidance |
|---|---|
| **Empty** (first use / no results) | Explain why, then give one clear next action. Use illustration sparingly |
| **Loading** | Skeletons that match the final layout (no CLS). Spinners only for actions under ~1 s. Show progress for long tasks |
| **Partial / streaming** | Show what has arrived and placeholder the rest |
| **Error** | Say what happened, why, and how to fix it. Offer retry. Keep the user's input |
| **Offline** | A banner plus queued actions. Tell the user what still works |
| **Success** | Confirm inline or with a toast. Don't block with modals |
| **Permission / locked** | Explain and offer the upgrade or request-access path |
| **Hover / focus / active / disabled** | A visible focus ring (≥ 2 px, ≥ 3:1). Avoid disabled buttons that give no reason |

## 6. UI quality checklist

Hierarchy and layout:
- [ ] One clear primary action per view. Secondary actions are visually quieter.
- [ ] Visual hierarchy through size, weight and contrast, not colour alone. Squint test passes.
- [ ] Spacing comes only from the scale, and related items sit closer than unrelated ones (proximity).
- [ ] Alignment is on a grid. Edges line up. No more than about 3 type sizes per screen.

Interaction and copy:
- [ ] Touch targets are at least 24 × 24 px (WCAG 2.2 minimum); 44 × 44 px recommended for primary touch actions.
- [ ] Forms have visible labels (not placeholder-only), inline validation on blur, error text tied to the field, and correct `autocomplete`/`inputmode`.
- [ ] Copy is concise, uses sentence case, and buttons use verbs ("Save changes", not "OK").
- [ ] Numbers, dates and currency are formatted for the locale.

Robustness:
- [ ] Images have fixed aspect ratios, responsive `srcset`, and meaningful `alt` text (or `alt=""` if decorative).
- [ ] Dark mode is checked separately for contrast and for images and logos.
- [ ] Responsive behaviour is checked at 320 px, 768 px, 1024 px, and wide screens. Nothing scrolls horizontally.
- [ ] Generic "AI-template" defaults are avoided: same-y purple gradients, random emoji icons, centre-everything layouts, and gratuitous glassmorphism, unless deliberately on-brand.

## 7. Benchmark design systems (learn from them, don't copy them)

| System | Learn from it |
|---|---|
| [Material Design 3](https://m3.material.io/) | Colour roles, dynamic colour, component states |
| [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) | Clarity, hierarchy, platform conventions |
| [GitHub Primer](https://primer.style/) | Dense developer UI, accessibility documentation |
| [Shopify Polaris](https://polaris.shopify.com/) | Commerce admin patterns, content guidelines |
| [IBM Carbon](https://carbondesignsystem.com/) | Enterprise data-heavy UI, data visualization |
| [Atlassian Design System](https://atlassian.design/) | Collaboration tools, tokens |
| [Radix Themes / Radix Colors](https://www.radix-ui.com/colors) | Accessible 12-step colour scales |
| [GOV.UK Design System](https://design-system.service.gov.uk/) | Plain-language forms, accessibility rigour |

More references: [Refactoring UI](https://www.refactoringui.com/) (practical visual design), [Laws of UX](https://lawsofux.com/), [NN/g articles](https://www.nngroup.com/articles/), [WebAIM contrast checker](https://webaim.org/resources/contrastchecker/), [Inclusive Components](https://inclusive-components.design/).
