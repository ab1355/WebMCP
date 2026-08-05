# 371-OS Frontend Framework — Standards & Patterns v1.0

> **Status:** v1.0 — extracted from The Orrery build (2026-07-27). Applies to all three UIs (Orrery :7373, Hub :5174, workplace_sim :5175) which share the same stack (Vite + React + TypeScript + Tailwind + Shadcn UI).
> **Purpose:** Standardize how 371-OS frontends are built — performance, security, data, and design.
> **Companion:** `CYBERSECURITY.md` (security framework), `ORGANISM_ARCHITECTURE.md` (organism model)

---

## I. Architecture — Mode-Transforming, Not Page-Navigating

371-OS frontends are **single-page instruments**, not multi-page apps. The user doesn't navigate between pages — they switch **cognitive modes** that reshape the same data from different angles.

```
App
├── NebulaBackground       (ambient layer — always present)
├── TopBar                 (mode switcher — the hero interaction)
├── <Suspense fallback={LoadingOrb}>
│   └── ActiveMode         (lazy-loaded — only one mode in memory)
└── BottomBar              (SSE event ticker)
```

### Rules
1. **One mode at a time.** Modes are mutually exclusive views, not tabs. Switching transforms the layout with a blur/scale transition.
2. **Lazy-load every mode.** `React.lazy()` + `Suspense`. Only the active mode's code ships in the initial bundle. This cut our LCP from 18.7s → 315ms.
3. **Shared shell stays eager.** TopBar, BottomBar, and the ambient background load immediately. Everything else defers.
4. **LoadingOrb, not blank page.** Every Suspense boundary gets a CSS-only skeleton (no JS deps) that renders instantly.

---

## II. Performance Patterns

### The loading hierarchy
```
1. HTML + CSS           → instant (critical path)
2. LoadingOrb skeleton  → instant (CSS-only, no framer-motion)
3. Shell (TopBar, etc)  → ~50ms (React mount)
4. Active mode chunk    → ~100ms (lazy-loaded)
5. Live data (API/SSE)  → async (falls back to mock gracefully)
```

### Font loading
- **Always** use `&display=swap` in Google Fonts URLs. Prevents FOIT.
- **Always** add `<link rel="preconnect">` for font CDNs. Reduces TLS handshake.
- Self-hosting fonts is the sovereign option (future).

### Animation rules
- **CSS animations for repeating effects** (pulses, breathing, ripples). Zero main-thread cost.
- **Framer-motion for transitions only** (mode switches, enter/exit). It's heavy (~100KB) — use sparingly.
- **Never** use `motion.circle`/`motion.svg` with static `r` props — framer-motion consumes SVG geometry attrs as animatable values and may set them to `undefined`. Use regular `<circle>` with CSS classes for SVG effects.
- **Never** use the `layout` prop on function components inside `<AnimatePresence mode="popLayout">` — it passes a ref that function components can't accept. Use `mode="wait"` or remove `layout`.

### Canvas (NebulaBackground pattern)
- **Read `window.innerWidth`**, never `canvas.offsetWidth` — the latter forces synchronous layout (layout thrashing).
- **Throttle resize listeners** (150ms debounce). Unthrottled resize regenerates expensive arrays.
- **Cleanup on unmount** — cancel `requestAnimationFrame`, clear timers, remove listeners.

### Code splitting targets
| What | How | Why |
|---|---|---|
| Mode components | `React.lazy(() => import(...))` | Only active mode ships |
| Heavy charts | Dynamic import inside the mode | Radar/chart libs are 5KB+ each |
| framer-motion | (future) `LazyMotion features={domAnimation}` | Defers unused animation features |

---

## III. Security Patterns (from CYBERSECURITY.md)

Every 371-OS frontend enforces the **Membrane (M)** at three layers:

### Layer 1: HTTP — Content Security Policy (index.html)
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';     ← dev only; tighten to 'self' in prod
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' http://localhost:7372 https://noaa... https://usgs...;
  img-src 'self' data:;
  base-uri 'self';
  form-action 'self';
" />
<meta http-equiv="X-Content-Type-Options" content="nosniff" />
```

| Directive | Interbeing | What it prevents |
|---|---|---|
| `script-src` | Screener (F) | XSS via injected scripts |
| `connect-src` | Membrane (M) | Data exfil to unknown origins |
| `base-uri` | Membrane (M) | Base-tag hijacking |
| `nosniff` | Screener (F) | MIME-type confusion |

### Custom security-check plugin (`plugins/security-check.ts`)
A Vite plugin that runs on every build and enforces the framework's own rules:

| Check | Severity | What it catches |
|---|---|---|
| CSP meta tag exists + has required directives | fail | Missing Membrane at HTTP layer |
| No inline `<script>` in production output | fail | XSS injection surface |
| No `eval()` in source | fail | Code injection risk |
| `dangerouslySetInnerHTML` / `.innerHTML` flagged | warn | Injection surface to audit |
| External URLs in CSP allowlist | warn | Uncontrolled egress |
| `X-Content-Type-Options: nosniff` present | warn | MIME confusion defense |

Output: a security report printed at the end of every `vite build`. Production failures exit non-zero (blocks CI/CD).

**Dev vs Prod:** Dev needs `'unsafe-inline'` for Vite's React Refresh injection. Production builds have no inline scripts — tighten to `script-src 'self'`.

### Layer 2: API — CORS (gateway)
```ts
app.use("*", cors({
  origin: ["http://localhost:7373", "https://*.ts.net:7373"],
  allowMethods: ["GET", "POST", "OPTIONS"],
  allowHeaders: ["Content-Type", "Authorization"],
}));
```
The origin allowlist IS the Membrane — only known frontends can cross the trust boundary.

### Layer 3: Application — Input Sanitization (future)
Any user input that enters React state (search, compose, dispatch) passes through NFKC normalization + zero-width strip before storage. The Membrane at the application layer.

---

## IV. Data Patterns — Graceful Degradation

Every data source follows the **fallback pattern**: try live → fall back to mock → never crash.

### Hook pattern
```ts
export function useLiveData() {
  const [data, setData] = useState(MOCK_DATA)
  const [live, setLive] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(API_URL)
        const data = await res.json()
        setData(transform(data))
        setLive(true)
      } catch {
        setLive(false)  // keep mock, mark not-live
      }
    }
    load()
    const interval = setInterval(load, REFRESH_MS)
    return () => clearInterval(interval)
  }, [])

  return { data, live }
}
```

### Rules
1. **Always have mock fallback.** The UI never breaks if the API is down.
2. **Show live/mock status.** A `·live` or `·mock` indicator tells the operator what they're seeing.
3. **Merge live + mock.** Live data for what the API provides; mock for what it doesn't yet (health, gate, state). Merge, don't replace.
4. **Auto-refresh.** Poll intervals: agents 15s, cosmic 3min, SSE continuous.

### SSE pattern
```ts
const es = new EventSource('/events')
es.onmessage = (e) => {
  const data = JSON.parse(e.data)
  setEvents(prev => [data, ...prev].slice(0, 20))
}
// 10s timeout → if no events, close + keep mock
```

---

## V. Design System

### Colors
| Token | Hex | Use |
|---|---|---|
| `--space` | `#0A1628` | Background (deep space navy) |
| `--cyan` | `#00E5FF` | Operational / default accent |
| `--amber` | `#FFB300` | Warning / awaiting |
| `--crimson` | `#FF3D5A` | Alert / threat / blocked |
| `--violet` | `#B388FF` | Creative / intent |
| `#38E8A0` | green | Healthy / cleared |

### Typography
- **Body:** Geist (sans), loaded with `display=swap`
- **Telemetry:** Geist Mono, loaded with `display=swap`
- **Preconnect** to `fonts.googleapis.com` + `fonts.gstatic.com`

### Surfaces
- `.glass` — `rgba(14,30,54,0.55)` + `backdrop-filter: blur(14px)` + thin border
- `.glass-strong` — `rgba(10,22,40,0.78)` + `blur(18px)` (for bars/headers)
- Panels: `rounded-2xl` + glass + `1px solid rgba(120,170,230,0.14)`

### Scrollbars
- 6px, `rgba(120,170,230,0.22)` thumb, transparent track, rounded.

---

## VI. Build & Deploy

### Stack
- **Runtime:** Bun (monorepo), Vite 7 (dev server + build)
- **Framework:** React 18 + TypeScript (strict)
- **Styling:** Tailwind CSS v3 (PostCSS pipeline, not CDN)
- **Animation:** Framer Motion (transitions only) + CSS (repeating effects)
- **DevTools:** `vite-plugin-devtools-json` — maps performance traces to source files
- **Type checking:** `vite-plugin-checker` — live TS errors in dev overlay (separate worker thread)
- **Security:** Custom `security-check.ts` plugin — CYBERSECURITY.md enforcement at build time
- **Compression:** `vite-plugin-compression` — brotli pre-compression (288KB → 83.5KB)

### Commands
```bash
cd apps/cognitive-interface

# Development (HMR, unminified — for building)
bun run dev          # or: npx vite --host 0.0.0.0 --port 7373

# Production build (minified, code-split — for testing/deploy)
npx vite build       # outputs to dist/
npx vite preview     # serves the production build

# Gateway (API + SSE)
cd apps/api-gateway && bun run server.ts    # :7372
```

### DevTools integration (vite-plugin-devtools-json)
Serves `/.well-known/appspecific/com.chrome.devtools.json` with the monorepo root + stable UUID.
This lets Chrome DevTools:
- **Map performance traces to source files** — click a function in the flame chart → jumps to the actual `.tsx` line (not the minified chunk)
- **Persist project settings** — breakpoints, local overrides, workspace folders survive across restarts
- **Attribute code across the monorepo** — `projectRoot` points at the monorepo root so traces show `packages/agents/` and `apps/` correctly

Config:
```ts
import devtoolsJson from 'vite-plugin-devtools-json'
// in vite.config.ts plugins:
devtoolsJson({ projectRoot: '/home/ab/Projects/oblique-order' })
```

### Gotchas (what we learned)
| Symptom | Cause | Fix |
|---|---|---|
| Stale UI after code changes | Vite dep cache from old process | `rm -rf node_modules/.vite` + restart |
| App blank, no errors | CSP `script-src 'self'` blocks Vite's inline React Refresh | Add `'unsafe-inline'` for dev |
| `<circle> r=undefined` | `motion.circle` consumes `r` as animatable attr | Use `<circle>` + CSS class |
| `Function components cannot be given refs` | `layout` prop on motion.div in popLayout | Remove `layout` or use `mode="wait"` |
| CORS errors on API fetch | Gateway missing CORS headers | `app.use('*', cors({ origin: [...] }))` |
| 18.7s LCP | All modes in one bundle | `React.lazy` + Suspense + LoadingOrb |
| Tailwind not applying | CDN script conflicting with local build | Remove `<script src="cdn.tailwindcss.com">`, use PostCSS only |

---

## VII. The Orrery Component Inventory

```
src/
├── App.tsx                     Shell: mode state + AnimatePresence + Suspense
├── index.css                   Tailwind + CSS vars + glass + animations
├── types/index.ts              Domain types (Mode, Interbeing, Agent, etc.)
├── data/
│   ├── orrery.ts               Mock domain model (fallback data)
│   └── cosmic.ts               Real NOAA + USGS fetchers
├── hooks/
│   ├── useCosmic.ts            Cosmic perturbation state (lifted)
│   ├── useLiveAgents.ts        /api/agents fetch + interbeing mapping
│   └── useLiveEvents.ts        SSE /events with mock fallback
└── components/
    ├── Orbital.tsx             SVG orbital (accepts agents + cosmicPerturbed)
    ├── NebulaBackground.tsx    Canvas nebula (window.innerWidth, throttled)
    ├── CosmicField.tsx         Universal resonance panel
    ├── RadarChart.tsx          48-dim resilience radar
    ├── LoadingOrb.tsx          CSS-only skeleton
    ├── TopBar.tsx              Mode pills (hero interaction)
    ├── BottomBar.tsx           SSE ticker
    ├── ui/Primitives.tsx       HealthDot, Panel, SectionLabel, Gauge
    └── modes/                  Lazy-loaded mode components
```

---

*Living document. Each frontend built on this framework updates it. The substrate accumulates trace.*
