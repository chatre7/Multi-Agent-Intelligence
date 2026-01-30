# Multi-Agent Intelligence Frontend

React + Vite + TailwindCSS frontend for the Multi-Agent Intelligence Platform.

## Key UI decisions (important)

- **Tailwind CSS v3**
- **No dark mode** by policy (no `dark:*` utilities and no `prefers-color-scheme` CSS)
- Consistent “layout routes” using React Router `Outlet` so pages render content only and shells live in shared layouts

For the detailed UI architecture guide, see `../UI_GUIDE.md`.

## Features

- 🔐 JWT authentication
- 💬 Real-time chat with WebSocket streaming
- 🔀 Domain & agent selection
- 🧵 Threads (list + deep-link `/threads/:id`)
- 🧭 Workflow visualizer (route: `/visualizer`, lazy-loaded)
- 🛠️ Admin panel (route: `/admin`)

## Tech stack

- **Framework**: React 19 + TypeScript
- **Build tool**: Vite 7
- **Styling**: Tailwind CSS 3
- **Routing**: `react-router` v7
- **State management**: Zustand
- **API client**: Axios
- **WebSocket**: Native WebSocket + custom client
- **Icons**: Lucide React

## Setup

### Prerequisites

- Node.js 20+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open `http://localhost:5173`:
- `/login`
- `/`
- `/chat`
- `/threads`
- `/visualizer`
- `/admin`

### Build / Preview

```bash
npm run build
npm run preview
```

## Routing & layout routes

Routes are defined in `src/App.tsx`.

Current map:
- `/login` (public)
- `/` (Home placeholder, under a generic left-nav shell)
- `/chat` (Chat section)
- `/threads` and `/threads/:id` (Threads section)
- `/visualizer` (Visualizer, lazy-loaded)
- `/admin` (Admin)
- unknown → redirected to `/chat`

Layout route components live in `src/presentation/routes/` and provide consistent shells:
- `HomeRouteLayout` → `PageLayout`
- `ChatRouteLayout` → `ChatLayout`
- `ThreadsRouteLayout` → `ThreadsLayout`
- `AdminRouteLayout` → `PageLayout`

## Project structure (relevant UI parts)

```
frontend/
├── src/
│   ├── assets/                       # Bundled images/icons (Vite fingerprints on build)
│   ├── infrastructure/
│   │   ├── api/apiClient.ts          # Axios HTTP client
│   │   ├── stores/                   # Zustand stores
│   │   └── websocket/                # WebSocket client for streaming
│   ├── presentation/
│   │   ├── components/
│   │   │   ├── chat/                 # Chat UI components (sidebar/header/container)
│   │   │   ├── threads/              # Threads sidebar + thread views
│   │   │   └── layout/               # AppHeader + layouts (ChatLayout/ThreadsLayout/PageLayout)
│   │   ├── pages/                    # Route-level pages (Home/Chat/Threads/Admin/Visualizer/Login)
│   │   └── routes/                   # Layout-route wrappers (Outlet-based)
│   ├── App.tsx                       # Routing entry
│   └── index.css                     # Tailwind directives (no dark mode)
└── package.json
```

## Images (where to put them)

Recommended: put UI images in `src/assets/` and import them in TSX.
Example: `src/assets/myai.png` used in `src/presentation/pages/HomePage.tsx`.

## Troubleshooting

### Styles don’t apply
- Ensure Tailwind config is loaded and `src/index.css` includes Tailwind directives.
- Run `npm run build` to confirm no Tailwind/PostCSS errors.

### Login redirects / route confusion
- Chat lives at `/chat` (not `/`).
- Unknown routes redirect to `/chat`.
