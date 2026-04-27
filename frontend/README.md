# PRO HR Frontend

Next.js frontend for PRO HR.

## Prerequisites

- Node.js 20+
- Backend API running (default: `http://127.0.0.1:8000`)

## Setup

```bash
cp .env.example .env.local
npm ci
```

## Run (development)

```bash
npm run dev -- -p 3000
```

App URL: `http://localhost:3000`

## Environment Variables

From `.env.example`:

- `BACKEND_URL` - Next rewrite target for `/api/*` in local dev
- `NEXT_PUBLIC_API_URL` - optional absolute API base; leave empty for same-origin rewrites
- `NEXT_PUBLIC_WS_URL` - websocket base URL
- `NEXT_PUBLIC_DEMO_MODE` - optional UI-only demo mode (`1`/`true`), not for real production

## Scripts

- `npm run dev` - development server
- `npm run build` - production build
- `npm run start` - production server
- `npm run lint` - ESLint
- `npm test` - Jest
- `npm run test:e2e` - Playwright smoke (includes prebuild)
- `npm run test:e2e:full` - Playwright full-stack
- `npm run test:e2e:ui` - Playwright UI mode

## Authentication Note

Backend auth behavior is controlled in `backend/.env` with `AUTH_DISABLED`.

- `AUTH_DISABLED=true` -> open-access API locally
- `AUTH_DISABLED=false` -> login/session checks enforced

For full project instructions, use the root `README.md`.
