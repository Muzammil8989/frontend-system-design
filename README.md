# Frontend System Design — Learning Roadmap

> 120 topics across 11 phases. Every completed topic saved as a structured `.md` note.

**Legend:** ✅ Completed &nbsp;|&nbsp; 🔄 Started &nbsp;|&nbsp; ⬜ Not Started

---

## Phase 1 — Web Fundamentals

| # | Topic | Category |
|---|---|---|
| 1 | ✅ [How Browsers Work](./notes/how-browsers-work.md) | Browser Internals |
| 2 | ✅ [Critical Rendering Path](./notes/critical-rendering-path.md) | Browser Internals |
| 3 | 🔄 Browser Storage Mechanisms | Browser Internals |
| 4 | ⬜ JavaScript Runtime & Event Loop | Browser Internals |
| 5 | ⬜ DOM & Virtual DOM | Browser Internals |
| 6 | ⬜ HTTP/1.1 vs HTTP/2 vs HTTP/3 | Networking |
| 7 | ⬜ DNS Resolution & CDN | Networking |
| 8 | ⬜ TCP/TLS Handshake | Networking |
| 9 | ⬜ REST vs GraphQL vs gRPC-Web | Networking |
| 10 | ⬜ WebSockets & SSE & Long Polling | Networking |
| 11 | ⬜ CORS & Same-Origin Policy | Networking |
| 12 | ⬜ Service Workers & Web Workers | Browser APIs |
| 13 | ⬜ Web APIs (Intersection Observer, ResizeObserver) | Browser APIs |
| 14 | ⬜ Browser Caching Strategies | Caching |

---

## Phase 2 — Rendering & Architecture

| # | Topic | Category |
|---|---|---|
| 15 | ⬜ Client-Side Rendering (CSR) | Rendering Patterns |
| 16 | ⬜ Server-Side Rendering (SSR) | Rendering Patterns |
| 17 | ⬜ Static Site Generation (SSG) | Rendering Patterns |
| 18 | ⬜ Incremental Static Regeneration (ISR) | Rendering Patterns |
| 19 | ⬜ Streaming SSR & React Server Components | Rendering Patterns |
| 20 | ⬜ Island Architecture | Rendering Patterns |
| 21 | ⬜ Edge Rendering | Rendering Patterns |
| 22 | ⬜ Micro-Frontends Architecture | Architecture |
| 23 | ⬜ Mono-repo vs Multi-repo | Architecture |
| 24 | ⬜ Component Architecture & Design Systems | Architecture |
| 25 | ⬜ Feature-Sliced Design | Architecture |
| 26 | ⬜ Module Bundling & Build Systems | Build Tools |

---

## Phase 3 — State & Data

| # | Topic | Category |
|---|---|---|
| 27 | ⬜ Client State Management Patterns | State Management |
| 28 | ⬜ Redux & Redux Toolkit | State Management |
| 29 | ⬜ Zustand / Jotai / Recoil | State Management |
| 30 | ⬜ Server State vs Client State | State Management |
| 31 | ⬜ React Query / TanStack Query | Data Fetching |
| 32 | ⬜ SWR & Stale-While-Revalidate | Data Fetching |
| 33 | ⬜ GraphQL Client (Apollo, urql) | Data Fetching |
| 34 | ⬜ Data Normalization & Caching | Data Fetching |
| 35 | ⬜ Optimistic UI Updates | Data Fetching |
| 36 | ⬜ Pagination & Infinite Scroll | Data Fetching |
| 37 | ⬜ Real-Time Data Sync | Data Fetching |
| 38 | ⬜ Offline-First Architecture | Data Fetching |

---

## Phase 4 — Performance Engineering

| # | Topic | Category |
|---|---|---|
| 39 | ⬜ Core Web Vitals (LCP, FID, CLS, INP) | Performance Metrics |
| 40 | ⬜ Lighthouse & Performance Auditing | Performance Metrics |
| 41 | ⬜ Performance Budgets | Performance Metrics |
| 42 | ⬜ Code Splitting & Lazy Loading | Loading Performance |
| 43 | ⬜ Tree Shaking & Dead Code Elimination | Loading Performance |
| 44 | ⬜ Image Optimization | Loading Performance |
| 45 | ⬜ Font Loading Strategies | Loading Performance |
| 46 | ⬜ Prefetching & Preloading | Loading Performance |
| 47 | ⬜ JavaScript Bundle Optimization | Loading Performance |
| 48 | ⬜ Virtual Scrolling & Windowing | Runtime Performance |
| 49 | ⬜ React Performance (memo, useMemo, useCallback) | Runtime Performance |
| 50 | ⬜ Debouncing & Throttling | Runtime Performance |
| 51 | ⬜ Web Workers for Heavy Computation | Runtime Performance |
| 52 | ⬜ Memory Leaks in Frontend Apps | Runtime Performance |
| 53 | ⬜ Animation Performance (CSS vs JS) | Runtime Performance |

---

## Phase 5 — Design Systems & Components

| # | Topic | Category |
|---|---|---|
| 54 | ⬜ Atomic Design Methodology | Design System |
| 55 | ⬜ Design Tokens | Design System |
| 56 | ⬜ Component API Design | Design System |
| 57 | ⬜ Compound Component Pattern | Component Patterns |
| 58 | ⬜ Headless UI / Renderless Components | Component Patterns |
| 59 | ⬜ Controlled vs Uncontrolled Components | Component Patterns |
| 60 | ⬜ Higher-Order Components & Render Props | Component Patterns |
| 61 | ⬜ Custom Hooks Patterns | Component Patterns |
| 62 | ⬜ Storybook & Component Documentation | Design System |
| 63 | ⬜ CSS Architecture (CSS-in-JS, Tailwind, CSS Modules) | Styling |
| 64 | ⬜ Responsive Design Patterns | Styling |
| 65 | ⬜ Theming & Dark Mode | Styling |

---

## Phase 6 — Accessibility & i18n

| # | Topic | Category |
|---|---|---|
| 66 | ⬜ ARIA Roles, States & Properties | Accessibility |
| 67 | ⬜ Keyboard Navigation & Focus Management | Accessibility |
| 68 | ⬜ Screen Reader Testing | Accessibility |
| 69 | ⬜ Color Contrast & Visual Accessibility | Accessibility |
| 70 | ⬜ Accessible Forms & Error Handling | Accessibility |
| 71 | ⬜ Automated A11y Testing (axe, Lighthouse) | Accessibility |
| 72 | ⬜ Internationalization (i18n) Architecture | Internationalization |
| 73 | ⬜ RTL Layout Support | Internationalization |
| 74 | ⬜ Date, Number & Currency Formatting | Internationalization |

---

## Phase 7 — Security

| # | Topic | Category |
|---|---|---|
| 75 | ⬜ XSS Prevention (Reflected, Stored, DOM) | Frontend Security |
| 76 | ⬜ Content Security Policy (CSP) | Frontend Security |
| 77 | ⬜ CSRF Protection | Frontend Security |
| 78 | ⬜ Authentication Flows in SPAs | Frontend Security |
| 79 | ⬜ Secure Token Storage | Frontend Security |
| 80 | ⬜ Subresource Integrity (SRI) | Frontend Security |
| 81 | ⬜ Clickjacking & iframe Protection | Frontend Security |
| 82 | ⬜ Dependency Vulnerability Scanning | Frontend Security |

---

## Phase 8 — Testing

| # | Topic | Category |
|---|---|---|
| 83 | ⬜ Unit Testing Components (Jest, Vitest) | Testing |
| 84 | ⬜ React Testing Library Patterns | Testing |
| 85 | ⬜ Integration Testing | Testing |
| 86 | ⬜ E2E Testing (Playwright, Cypress) | Testing |
| 87 | ⬜ Visual Regression Testing | Testing |
| 88 | ⬜ Performance Testing | Testing |
| 89 | ⬜ Accessibility Testing | Testing |
| 90 | ⬜ Testing Strategies & Pyramid | Testing |

---

## Phase 9 — Monitoring & Observability

| # | Topic | Category |
|---|---|---|
| 91 | ⬜ Error Boundaries & Global Error Handling | Error Handling |
| 92 | ⬜ Error Tracking (Sentry, Datadog RUM) | Error Handling |
| 93 | ⬜ Real User Monitoring (RUM) | Monitoring |
| 94 | ⬜ Synthetic Monitoring | Monitoring |
| 95 | ⬜ Feature Flags & A/B Testing | Analytics |
| 96 | ⬜ Analytics Architecture | Analytics |
| 97 | ⬜ Logging Best Practices | Monitoring |

---

## Phase 10 — Advanced Topics

| # | Topic | Category |
|---|---|---|
| 98 | ⬜ Progressive Web Apps (PWA) | Advanced |
| 99 | ⬜ WebAssembly (WASM) in Frontend | Advanced |
| 100 | ⬜ Web Components & Shadow DOM | Advanced |
| 101 | ⬜ Authentication Architecture (BFF Pattern) | Advanced |
| 102 | ⬜ SEO for SPAs & Dynamic Content | Advanced |
| 103 | ⬜ Deployment & CI/CD for Frontend | Advanced |
| 104 | ⬜ CDN Architecture & Edge Caching | Advanced |
| 105 | ⬜ Monorepo Tooling (Turborepo, Nx) | Advanced |

---

## Phase 11 — System Design Cases

| # | Topic | Category |
|---|---|---|
| 106 | ⬜ Design a News Feed (Facebook/Twitter) | Social |
| 107 | ⬜ Design an Autocomplete / Typeahead | Search |
| 108 | ⬜ Design an Image Carousel / Gallery | Media |
| 109 | ⬜ Design a Chat Application UI | Messaging |
| 110 | ⬜ Design a Spreadsheet (Google Sheets) | Productivity |
| 111 | ⬜ Design a Video Player (YouTube) | Media |
| 112 | ⬜ Design a Drag-and-Drop Board (Trello) | Productivity |
| 113 | ⬜ Design a Rich Text Editor | Productivity |
| 114 | ⬜ Design an E-Commerce Product Page | E-Commerce |
| 115 | ⬜ Design a Dashboard with Real-Time Data | Analytics |
| 116 | ⬜ Design a Multi-Step Form / Wizard | Forms |
| 117 | ⬜ Design a Notification System UI | Notification |
| 118 | ⬜ Design a Map-Based Application | Geo |
| 119 | ⬜ Design a Calendar Component | Productivity |
| 120 | ⬜ Design a Design Tool (Figma-like Canvas) | Advanced |

---
