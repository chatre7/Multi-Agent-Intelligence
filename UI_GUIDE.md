# UI Guide (Frontend)

Last updated: 2026-01-30

This document describes the current UI architecture and conventions in `frontend/` based on the refactors we’ve applied:

- Layout routes with `Outlet` (React Router)
- Consistent “left sidebar + top header + content” shell across pages
- Full-height layouts (no “screen not full height” bugs)
- Tailwind CSS v3 and **no dark mode**
- Shared header styling via `AppHeader`

---

## 1) Stack & conventions

- Framework: React + TypeScript (Vite)
- Router: `react-router` (`Routes`, `Route`, `Outlet`, `Navigate`)
- Styling: Tailwind CSS **v3**
- Icons: `lucide-react`

**Non-negotiables**
- **No dark mode**: do not add `dark:*` utilities or `prefers-color-scheme` CSS back.
- Use consistent header/spacing patterns (see sections below).

---

## 2) Route map (high level)

All routes are defined in `frontend/src/App.tsx`.

### Auth gating
- `/login` is public.
- Everything else is behind `RequireAuth` (redirects to `/login` when no token).

### Pages (current)
- `/` → `HomePage` (placeholder page)
- `/chat` → `ChatPage` (chat experience)
- `/threads` and `/threads/:id` → `ThreadsPage`
- `/visualizer` → `VisualizerPage` (lazy-loaded)
- `/admin` → `AdminPage`
- Unknown route → redirect to `/chat`

### Layout routes
We use layout routes so pages render **content only**, while shells (sidebar/header) live at route/layout level.

Current layout routes:
- `HomeRouteLayout` → wraps Home with `PageLayout`
- `ChatRouteLayout` → wraps Chat with `ChatLayout`
- `ThreadsRouteLayout` → wraps Threads with `ThreadsLayout`
- `AdminRouteLayout` → wraps Admin/Visualizer with `PageLayout`

Files:
- `frontend/src/App.tsx`
- `frontend/src/presentation/routes/HomeRouteLayout.tsx`
- `frontend/src/presentation/routes/ChatRouteLayout.tsx`
- `frontend/src/presentation/routes/ThreadsRouteLayout.tsx`
- `frontend/src/presentation/routes/AdminRouteLayout.tsx`

---

## 3) Navigation (left menu)

Main nav items are defined in:
- `frontend/src/presentation/config/appNavigation.ts`

Current main nav:
- Home (`/`)
- Chat (`/chat`)
- Threads (`/threads`)
- Visualizer (`/visualizer`)
- Admin (`/admin`)

This array is rendered in:
- `frontend/src/presentation/components/chat/ChatSidebar.tsx`
- `frontend/src/presentation/components/threads/ThreadsSidebar.tsx`

Rule of thumb:
- If you add a new “top-level section”, add it to `MAIN_NAV_ITEMS`.
- If you add a nested route under an existing section (e.g. `/chat/foo`), don’t add it to `MAIN_NAV_ITEMS` unless it’s a top-level nav destination.

---

## 4) Layout system (how pages become full-height)

### Root shell
`AppShellLayout` (in `frontend/src/App.tsx`) sets:
- `h-screen w-screen`
- `flex flex-col`
- child content with `flex-1 min-h-0 overflow-hidden`

This is the top-level guardrail that prevents “page not full height”.

### Core layout components

#### `AppHeader`
File: `frontend/src/presentation/components/layout/AppHeader.tsx`

Purpose:
- Shared top header styling (border, blur, height, padding, layout).

Usage patterns:
- Default (compact) header is “Threads style”: small title + optional actions.
- Use two headers when needed (Admin uses a second header row for tabs).

Key props:
- `variant`: `"compact"` (default) or `"tall"`
- `sticky`: optional sticky header behavior
- `className`: additional classes

#### `ChatLayout`
File: `frontend/src/presentation/components/layout/ChatLayout.tsx`

Chat-specific shell:
- Left: `ChatSidebar` (history + global nav)
- Top: `ChatHeader` (toggle + domain/agent selector)
- Content: renders children (`<Outlet />`) inside a full-height flex container

#### `ThreadsLayout`
File: `frontend/src/presentation/components/layout/ThreadsLayout.tsx`

Threads-specific shell:
- Left: `ThreadsSidebar` with its own categories/recents + global nav
- Top: `AppHeader` with toggle + “Threads”
- Mobile: sidebar becomes an overlay (`fixed`, backdrop) controlled by state

#### `PageLayout`
File: `frontend/src/presentation/components/layout/PageLayout.tsx`

Generic shell used for:
- Home (`/`)
- Admin (`/admin`)
- Visualizer (`/visualizer`)

It renders:
- Left: `ChatSidebar` in **nav-only mode** (see below)
- Right: page content (`<Outlet />`) with **no absolute-position toggle**

Why:
- We previously had an `absolute top-left` toggle which caused the “icon position not aligned when collapsed” issue.
- Now each page that uses `PageLayout` renders its toggle **inside** its header, aligned like Threads.

---

## 5) Sidebar architecture & toggle state

### `ChatSidebar` has modes
File: `frontend/src/presentation/components/chat/ChatSidebar.tsx`

Props:
- `mode?: "full" | "nav"` (default `"full"`)

Modes:
- `full`: shows Logo, “New Chat”, Search, Chat history, plus footer nav
- `nav`: shows only the chrome that makes sense as a generic left nav (Logo + footer nav + user area). It does **not** fetch or show chat history.

Where used:
- Chat section uses `mode="full"` via `ChatLayout`
- Home/Admin/Visualizer use `mode="nav"` via `PageLayout`

### Sharing sidebar state with page headers
When using `PageLayout`, pages need to render the “collapse/expand” button in their headers.

We provide sidebar state via context:
- `frontend/src/presentation/components/layout/SidebarLayoutContext.tsx`

How it works:
- `PageLayout` owns `sidebarOpen` state.
- `PageLayout` wraps its subtree in `SidebarLayoutProvider`.
- Pages call `useSidebarLayout()` to access:
  - `sidebarOpen`
  - `setSidebarOpen(open)`

Pages currently using this pattern:
- `frontend/src/presentation/pages/HomePage.tsx`
- `frontend/src/presentation/pages/AdminPage.tsx`
- `frontend/src/presentation/pages/VisualizerPage.tsx`

**Rule**: If a page is rendered under `PageLayout`, put the toggle button in the page header using `useSidebarLayout()` (not absolute positioning).

---

## 6) Header patterns (“Threads style”)

Our default header style is the compact Threads-like bar:

- Use `AppHeader` (default variant)
- Left area: `flex items-center gap-3`
  - optional sidebar toggle button:
    - class: `p-2 -ml-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors`
    - aria-label toggles between “Open sidebar”/“Close sidebar”
  - page title: `text-sm font-semibold text-gray-900`
- Right area: actions (icon buttons) or an empty `<div />` for alignment

Examples:
- Threads: `frontend/src/presentation/components/layout/ThreadsLayout.tsx`
- Admin: `frontend/src/presentation/pages/AdminPage.tsx`
- Visualizer: `frontend/src/presentation/pages/VisualizerPage.tsx`
- Home: `frontend/src/presentation/pages/HomePage.tsx`

Notes:
- Chat is intentionally different because it has a domain/agent selector in its header: `frontend/src/presentation/components/chat/ChatHeader.tsx`.

---

## 7) Height, flex, and scroll rules (avoid “not full screen”)

These rules are the difference between “works on one page” vs “works everywhere”.

### Golden rules
1. If a parent is `flex`, children that should fill remaining space must use `flex-1` **and** `min-h-0`.
2. Put `overflow-hidden` at the shell boundaries and decide exactly *one* scroll owner per panel.
3. Avoid using fixed `calc()` heights unless absolutely necessary.

### Pattern used in shells
- Root shell: `h-screen w-screen flex flex-col`
- Main content wrapper: `flex-1 min-h-0 overflow-hidden flex`
- Panel layout: sidebar + main panel with `min-w-0 min-h-0`

Example shells:
- `frontend/src/App.tsx` (`AppShellLayout`)
- `frontend/src/presentation/components/layout/ChatLayout.tsx`
- `frontend/src/presentation/components/layout/ThreadsLayout.tsx`
- `frontend/src/presentation/components/layout/PageLayout.tsx`

---

## 8) Tailwind v3 + no dark mode

### Tailwind version
This project uses Tailwind CSS **v3**.

### Dark mode policy
We intentionally removed:
- all `dark:*` utilities from `frontend/src`
- `@media (prefers-color-scheme: dark)` from CSS

**Rule**: Do not reintroduce dark mode utilities or CSS without explicit product decision.

---

## 9) Buttons & UI consistency

### “Primary sidebar action” button style
The “New Chat” button is the reference, and “New Request” was aligned to match it.

Where to see the canonical pattern:
- `frontend/src/presentation/components/chat/ChatSidebar.tsx` (“New Chat”)
- `frontend/src/presentation/components/threads/ThreadsSidebar.tsx` (“New Request”)

Characteristics:
- White card button with border + subtle shadow
- Inner icon container (blue) that inverts on hover
- `active:scale-[0.98]`

If you add a new primary action button in a sidebar, match this pattern to keep UI consistent.

---

## 10) Images/assets

### Where to put images
You have two valid choices in Vite:

1) Bundled assets (recommended for UI images)
- Put files under: `frontend/src/assets/`
- Import them in TSX so Vite fingerprints them in `dist/assets/*`.

Example:
- Image file: `frontend/src/assets/myai.png`
- Usage: `frontend/src/presentation/pages/HomePage.tsx`

2) Static public assets (URL-based)
- Put files under: `frontend/public/images/`
- Reference by absolute URL: `src="/images/..."`.

Choose (1) when:
- you want cache-busting filenames
- you want the code to fail build-time if the asset is missing

Choose (2) when:
- you want “drop files in place” without touching TS/JS imports

---

## 11) Adding a new page (checklist)

### A) New top-level page under left sidebar (Home/Admin/Visualizer style)
1. Create page in `frontend/src/presentation/pages/YourPage.tsx`
2. Decide layout:
   - If it should use the generic left menu: place it under `PageLayout` (via a route layout or `AdminRouteLayout`).
3. Add route in `frontend/src/App.tsx`
4. If it should appear in the nav:
   - Add to `frontend/src/presentation/config/appNavigation.ts`
5. Use the “Threads-style” header:
   - `AppHeader` + optional toggle via `useSidebarLayout()`

### B) New nested page under Chat
1. Add nested route under `path="chat"` in `frontend/src/App.tsx`
2. Render within Chat shell:
   - `ChatRouteLayout` already wraps the `chat/*` section.

### C) New nested page under Threads
1. Add nested route under Threads routes in `frontend/src/App.tsx`
2. Ensure scroll ownership still makes sense (avoid adding extra scroll containers).

---

## 12) Troubleshooting

### “Page doesn’t fill the screen / content cuts off”
Checklist:
- Parent chain has `h-screen` at the root (it does via `AppShellLayout`).
- Your panel has `flex-1 min-h-0` (especially if it’s inside another `flex` container).
- Only one scroll owner per panel (`overflow-y-auto` on exactly one container).

### “Sidebar toggle icon position is weird when collapsed”
Fix:
- Toggle button must live inside `AppHeader` (not `absolute` positioned).
- For pages under `PageLayout`, use `useSidebarLayout()` for state.

---

## 13) Suggested future refactors (optional)

These are not required for current behavior, but would reduce complexity:

- Split `ChatSidebar` into:
  - a truly generic `NavSidebar`
  - a chat-specific `ChatHistorySidebar`
- Unify footer “User” menu across ChatSidebar and ThreadsSidebar
- Consider code-splitting the main bundle (Vite warns about > 500 kB chunks)

