# Browser Storage Mechanisms

> **Date:** 2026-03-27
> **Category:** Frontend System Design
> **Sub-Topic:** Browser Internals / Storage

> **Pre-requisite:** Read [How Browsers Work](./how-browsers-work.md) first.
> This note covers where and how browsers store data — on the client side.

---

## ELI5 — Simple Explanation

Imagine your browser is a desk at work:
- **Cookie** = a sticky note on your monitor — small, seen by everyone, expires
- **localStorage** = your desk drawer — stays there even after you leave for the day
- **sessionStorage** = a notepad you tear up when you go home — gone when tab closes
- **IndexedDB** = a filing cabinet — holds thousands of files, searchable, structured
- **Cache API** = a shelf of saved documents so you don't reprint the same thing twice

> **Each storage type exists for a different reason.**
> Picking the wrong one causes security bugs, data loss, or poor performance.

---

## Core Concept — Step by Step

### Section 1: The Storage Landscape

There are 5 client-side storage mechanisms you need to know:

```
┌─────────────────────────────────────────────────────────┐
│                  BROWSER STORAGE                        │
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Cookie  │  │  Web Storage │  │  Advanced Storage  │  │
│  │          │  │              │  │                   │  │
│  │ ~4KB     │  │ localStorage │  │ IndexedDB (GBs)   │  │
│  │ sent to  │  │ sessionStr.  │  │ Cache API         │  │
│  │ server   │  │ ~5–10MB each │  │ (Service Worker)  │  │
│  └──────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

| Storage | Max Size | Persists After Tab Close | Persists After Browser Close | Sent to Server |
|---|---|---|---|---|
| **Cookie** | ~4KB | ✅ (if expiry set) | ✅ (if expiry set) | ✅ **Always** |
| **localStorage** | ~5–10MB | ✅ Yes | ✅ Yes | ❌ No |
| **sessionStorage** | ~5–10MB | ❌ No | ❌ No | ❌ No |
| **IndexedDB** | GBs (quota-based) | ✅ Yes | ✅ Yes | ❌ No |
| **Cache API** | GBs (quota-based) | ✅ Yes | ✅ Yes | ❌ No |

---

### Section 2: Cookies

Cookies are the oldest storage mechanism. Created by server or JavaScript, **automatically sent with every HTTP request** to the same domain.

```
Client                           Server
  │                                │
  │──── GET /page ─────────────────►│
  │◄─── Set-Cookie: token=abc; ─────│
  │     HttpOnly; Secure; SameSite  │
  │                                │
  │──── GET /api (+ Cookie: token=abc) ────►│  ← auto-attached!
```

**Creating cookies — server vs client:**

```http
# Server sets cookie (HTTP response header)
Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Strict; Max-Age=3600
```

```javascript
// Client sets cookie (JS) — cannot set HttpOnly from JS
document.cookie = "theme=dark; Max-Age=86400; SameSite=Lax";

// Reading cookies — ugly but real
const theme = document.cookie
  .split('; ')
  .find(c => c.startsWith('theme='))
  ?.split('=')[1];
```

**Cookie security flags — every one matters:**

| Flag | What it does | When to use |
|---|---|---|
| `HttpOnly` | JS cannot read this cookie | Auth tokens — prevents XSS theft |
| `Secure` | Only sent over HTTPS | Always in production |
| `SameSite=Strict` | Not sent on cross-site requests | CSRF protection — same site only |
| `SameSite=Lax` | Sent on top-level navigation only | Good default balance |
| `SameSite=None` | Sent everywhere | Requires `Secure`; for cross-site embeds |
| `Max-Age` / `Expires` | When cookie expires | Session vs persistent |
| `Domain` | Which subdomains receive it | `domain=.example.com` = all subdomains |
| `Path` | Which URL paths receive it | `/api` = only API routes get it |

> **Rule:** Auth tokens must be `HttpOnly` + `Secure` + `SameSite=Strict/Lax`.
> Never store auth tokens in localStorage — XSS can steal them.

---

### Section 3: localStorage

Synchronous key-value store. Data persists until explicitly cleared. Shared across all tabs of the same origin.

```
Origin: https://myapp.com

Tab 1: localStorage.setItem('user', 'Alice')
Tab 2: localStorage.getItem('user')  → 'Alice'   ← same data!
```

```javascript
// WRITE
localStorage.setItem('theme', 'dark');
localStorage.setItem('prefs', JSON.stringify({ lang: 'en', fontSize: 16 }));

// READ
const theme = localStorage.getItem('theme');           // 'dark'
const prefs = JSON.parse(localStorage.getItem('prefs'));  // { lang: 'en', ... }

// DELETE
localStorage.removeItem('theme');

// CLEAR ALL
localStorage.clear();

// CHECK SIZE (approximate)
let total = 0;
for (let key in localStorage) {
  total += localStorage[key].length + key.length;
}
console.log(`~${(total / 1024).toFixed(2)} KB used`);
```

**Important limitations:**
- Synchronous — blocks the main thread on large reads/writes
- Strings only — must `JSON.stringify` / `JSON.parse` objects
- No expiry — data never auto-deletes
- ~5MB limit (varies by browser)
- Not available in Web Workers or Service Workers

```
Use localStorage for:
✅ User preferences (theme, language, font size)
✅ Non-sensitive cached data (last viewed item ID)
✅ Feature flag overrides (dev tools)

Never use for:
❌ Auth tokens (XSS risk)
❌ Large datasets (use IndexedDB)
❌ Sensitive personal data
```

---

### Section 4: sessionStorage

Identical API to localStorage but data lives only for the browser tab session. Each tab gets its own isolated sessionStorage.

```
Tab 1: sessionStorage.setItem('step', '2')
Tab 2: sessionStorage.getItem('step')  → null  ← isolated!

Tab 1 closes → data gone
Tab 1 refreshes → data STILL there (refresh ≠ close)
```

```javascript
// Same API as localStorage — just replace "localStorage" with "sessionStorage"
sessionStorage.setItem('checkout_step', '3');
sessionStorage.setItem('form_draft', JSON.stringify({ name: 'Alice', email: '...' }));

const step = sessionStorage.getItem('checkout_step');

// Auto-cleared when tab closes — no manual cleanup needed
```

**localStorage vs sessionStorage — when to use:**

```
localStorage    → data needed across tabs or sessions
                  (theme, auth state, cached user prefs)

sessionStorage  → data scoped to this tab, this visit only
                  (multi-step form progress, wizard state,
                   shopping cart before login, temporary UI state)
```

---

### Section 5: IndexedDB

A full **transactional NoSQL database** in the browser. Supports complex objects, indexes, cursors, and stores gigabytes of data. Asynchronous — never blocks the main thread.

```
IndexedDB Structure:
┌─────────────────────────────────────┐
│         Database: "MyApp"           │
│                                     │
│  ┌──────────────────────────────┐   │
│  │  Object Store: "products"    │   │
│  │  ┌──────┬──────────────────┐ │   │
│  │  │  id  │      data        │ │   │
│  │  ├──────┼──────────────────┤ │   │
│  │  │  1   │ { name, price }  │ │   │
│  │  │  2   │ { name, price }  │ │   │
│  │  └──────┴──────────────────┘ │   │
│  │  Index: "by_category"        │   │
│  └──────────────────────────────┘   │
│                                     │
│  Object Store: "cart"               │
│  Object Store: "offline_queue"      │
└─────────────────────────────────────┘
```

**Raw IndexedDB API** (verbose — most devs use a wrapper library):

```javascript
// Open / create database
const request = indexedDB.open('MyApp', 1);

request.onupgradeneeded = (event) => {
  const db = event.target.result;
  // Create object store (like a table)
  const store = db.createObjectStore('products', { keyPath: 'id' });
  // Create an index for fast queries
  store.createIndex('by_category', 'category', { unique: false });
};

request.onsuccess = (event) => {
  const db = event.target.result;

  // WRITE (inside a transaction)
  const tx = db.transaction('products', 'readwrite');
  tx.objectStore('products').add({ id: 1, name: 'Laptop', price: 999, category: 'tech' });

  // READ by key
  const readTx = db.transaction('products', 'readonly');
  const getReq = readTx.objectStore('products').get(1);
  getReq.onsuccess = () => console.log(getReq.result); // { id: 1, name: 'Laptop', ... }
};
```

**Using `idb` (wrapper library — recommended):**

```javascript
import { openDB } from 'idb';

const db = await openDB('MyApp', 1, {
  upgrade(db) {
    db.createObjectStore('products', { keyPath: 'id' });
  }
});

// Write
await db.put('products', { id: 1, name: 'Laptop', price: 999 });

// Read
const product = await db.get('products', 1);

// Get all
const all = await db.getAll('products');

// Delete
await db.delete('products', 1);
```

```
Use IndexedDB for:
✅ Offline-first apps (cache API responses)
✅ Large datasets (product catalogs, documents)
✅ Structured data needing querying/indexing
✅ Background sync queues
✅ File/blob storage (images, PDFs)

Overkill for:
❌ Simple key-value pairs → use localStorage
❌ Small preferences → use localStorage
```

---

### Section 6: Cache API

Part of the Service Worker API. Stores **HTTP Request/Response pairs** — designed for caching network resources (HTML, CSS, JS, images, API responses).

```
Without Cache API:
Browser → Network → Server → Response → Display (online only)

With Cache API:
Browser → Cache? → Yes: use cached response (instant, offline)
                → No:  Network → Server → save to Cache → Display
```

```javascript
// In a Service Worker (sw.js)

// CACHE on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) =>
      cache.addAll([
        '/',
        '/styles.css',
        '/app.js',
        '/offline.html'
      ])
    )
  );
});

// SERVE from cache, fall back to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) =>
      cached ?? fetch(event.request)
    )
  );
});

// In regular JS — programmatic cache access
const cache = await caches.open('api-cache-v1');
await cache.put('/api/products', new Response(JSON.stringify(products)));
const cached = await cache.match('/api/products');
const data = await cached.json();
```

**Caching strategies:**

| Strategy | Logic | Best for |
|---|---|---|
| **Cache First** | Serve cache, ignore network | Static assets (CSS, JS, fonts) |
| **Network First** | Try network, fall back to cache | API data needing freshness |
| **Stale While Revalidate** | Serve cache instantly, update in background | Feeds, non-critical data |
| **Cache Only** | Cache or fail | Offline-only assets |
| **Network Only** | Always network, no cache | Auth endpoints, payments |

---

## Full Visual — Storage Decision Tree

```
Do you need to send data to the server automatically?
  │
  ├── YES → Cookie
  │         (auth session, CSRF token)
  │
  └── NO → Does it need to survive tab close?
            │
            ├── NO → sessionStorage
            │        (form wizard, temp UI state)
            │
            └── YES → Is it a network resource (HTML/CSS/JS/images/API)?
                       │
                       ├── YES → Cache API
                       │         (offline support, PWA, asset caching)
                       │
                       └── NO → Is data large (>100KB) or complex/structured?
                                  │
                                  ├── YES → IndexedDB
                                  │         (offline data, large datasets, files)
                                  │
                                  └── NO → localStorage
                                            (preferences, simple flags)
```

---

## Real-World Examples

**Example 1 — Auth flow: correct storage per token type:**
```javascript
// ✅ Access token: short-lived, in memory only (not in any storage)
let accessToken = null;

async function login(credentials) {
  const res = await fetch('/api/login', {
    method: 'POST',
    body: JSON.stringify(credentials)
  });
  // Server sets: Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict
  // We store access token only in memory — gone on refresh (by design)
  const { accessToken: token } = await res.json();
  accessToken = token;
}

// ✅ Refresh token: in HttpOnly cookie (auto-sent, JS can't read it)
// ✅ Theme preference: localStorage (safe, non-sensitive)
localStorage.setItem('theme', 'dark');

// ❌ WRONG: never do this
localStorage.setItem('access_token', token);  // XSS can steal it!
```

**Example 2 — Multi-step form: sessionStorage:**
```javascript
// Step 1 page: save progress
function saveStep1(formData) {
  sessionStorage.setItem('step1', JSON.stringify(formData));
  navigate('/checkout/step2');
}

// Step 2 page: restore if user goes back
function loadStep1() {
  const saved = sessionStorage.getItem('step1');
  return saved ? JSON.parse(saved) : null;
}

// Final submit: read all steps, clear storage
async function submitOrder() {
  const step1 = JSON.parse(sessionStorage.getItem('step1'));
  const step2 = JSON.parse(sessionStorage.getItem('step2'));
  await fetch('/api/order', { method: 'POST', body: JSON.stringify({ step1, step2 }) });
  sessionStorage.clear();  // clean up
}
```

**Example 3 — Offline product catalog: IndexedDB + Cache API:**
```javascript
// Service Worker: cache app shell
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open('shell-v1').then(c => c.addAll(['/', '/app.js', '/styles.css'])));
});

// App: sync products to IndexedDB for offline browsing
import { openDB } from 'idb';

const db = await openDB('shop', 1, {
  upgrade(db) { db.createObjectStore('products', { keyPath: 'id' }); }
});

async function syncProducts() {
  try {
    const res = await fetch('/api/products');
    const products = await res.json();
    const tx = db.transaction('products', 'readwrite');
    await Promise.all(products.map(p => tx.store.put(p)));
    // Also cache the raw API response
    const cache = await caches.open('api-v1');
    await cache.put('/api/products', new Response(JSON.stringify(products)));
  } catch {
    console.log('Offline — using cached data');
  }
}

async function getProducts() {
  // Try IndexedDB first (structured, queryable)
  const offline = await db.getAll('products');
  if (offline.length) return offline;
  // Fallback: Cache API response
  const cached = await caches.match('/api/products');
  return cached ? cached.json() : [];
}
```

---

## Key Points Summary

| Concept | One-Line Explanation |
|---|---|
| **Cookie** | 4KB key-value, auto-sent to server, has security flags |
| **localStorage** | 5MB key-value, persists forever, shared across tabs |
| **sessionStorage** | 5MB key-value, dies when tab closes, tab-isolated |
| **IndexedDB** | Full async NoSQL DB in the browser, GBs, structured data |
| **Cache API** | Stores Request/Response pairs for offline + PWA use |
| **HttpOnly** | Cookie flag: JS cannot read it — XSS-safe |
| **SameSite** | Cookie flag: controls cross-site sending — CSRF protection |
| **idb** | Lightweight library wrapping IndexedDB with promises |
| **Stale While Revalidate** | Serve cache immediately, update in background |
| **Origin isolation** | All storage is scoped to the origin — different ports = different storage |

---

## Test Your Understanding

**Q1 (Basic):**
A user logs in and receives a session token.
Where should you store it? Why not `localStorage`?

**Q2 (Application):**
You're building a multi-step checkout form (5 steps).
If the user refreshes the page mid-flow, their data should survive.
If they open a new tab, they should start fresh.
Which storage type do you use, and why?

**Q3 (Tricky):**
A developer builds an offline-first PWA.
They store all API responses in `localStorage` instead of `IndexedDB` + `Cache API`.
What 3 problems will they run into?

---

## Cheat Sheet

**Key Definitions:**
- **Cookie:** Small key-value store auto-attached to HTTP requests; server or JS writable
- **localStorage:** Persistent synchronous key-value store; survives sessions; same-origin
- **sessionStorage:** Tab-scoped synchronous key-value store; cleared on tab close
- **IndexedDB:** Async NoSQL object store; GBs of data; supports indexes and transactions
- **Cache API:** HTTP Request/Response cache; Service Worker access; offline-first
- **HttpOnly:** Cookie inaccessible to JS — primary XSS mitigation for auth tokens
- **SameSite:** Cookie cross-site send policy — primary CSRF mitigation

**API Quick Reference:**
```javascript
// Cookie (via JS)
document.cookie = "key=value; SameSite=Lax; Secure; Max-Age=3600";

// localStorage / sessionStorage (same API)
localStorage.setItem('key', JSON.stringify(value));
const val = JSON.parse(localStorage.getItem('key'));
localStorage.removeItem('key');
localStorage.clear();

// IndexedDB (with idb)
const db = await openDB('db', 1, { upgrade(db) { db.createObjectStore('store', { keyPath: 'id' }); } });
await db.put('store', { id: 1, data: 'value' });
const item = await db.get('store', 1);
await db.delete('store', 1);

// Cache API
const cache = await caches.open('v1');
await cache.put(request, response);
const res = await caches.match(request);
await caches.delete('v1');
```

**Storage Decision Cheatsheet:**
```
Auth session token    → HttpOnly Cookie (server-set)
Auth access token     → Memory only (variable)
User preferences      → localStorage
Multi-step form state → sessionStorage
Large app data        → IndexedDB
Static assets offline → Cache API (Cache First)
API data offline      → Cache API (Network First / SWR)
Files/blobs offline   → IndexedDB
```

**Common Mistakes to Avoid:**

| Mistake | Why Wrong | Fix |
|---|---|---|
| Storing auth tokens in `localStorage` | XSS can `document.cookie` steal them — wait, JS can read `localStorage` directly | Use `HttpOnly` cookies for refresh tokens; memory for access tokens |
| Using `localStorage` for large data | 5MB limit, synchronous, blocks main thread | Use IndexedDB for anything >100KB or complex |
| Forgetting `JSON.stringify` in Web Storage | Stores `[object Object]` — unreadable | Always `JSON.stringify` on write, `JSON.parse` on read |
| No cookie `SameSite` flag | CSRF attacks can use cookie cross-site | Always set `SameSite=Strict` or `Lax` |
| No cookie `Secure` flag in production | Cookie sent over HTTP — interceptable | Always set `Secure` in production |
| `Cache API` in regular JS without Service Worker | Fetches work, but offline support doesn't | Register a Service Worker to intercept fetches |
| Assuming storage survives forever | Browsers evict storage under storage pressure | Use `navigator.storage.persist()` to request persistence |

---

> **Previous Topic:** [Critical Rendering Path](./critical-rendering-path.md)
> — How browsers optimize the rendering pipeline

> **Next Topic:** JavaScript Runtime & Event Loop
> — How JS executes, the call stack, task queue, and microtasks

*Saved on: 2026-03-27 | Repo: Frontend System Design Learning Notes*
