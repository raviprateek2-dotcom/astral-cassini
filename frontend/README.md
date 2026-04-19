# PRO HR Frontend

Next.js + React + TypeScript frontend for the PRO HR recruitment platform.

## Prerequisites

- Node.js 20+
- Backend API running (default: `http://127.0.0.1:8000`)

## Environment Setup

Copy `.env.example` to `.env.local` and update values as needed:

- `NEXT_PUBLIC_API_URL`: Optional absolute API base URL. Leave empty to use local `/api` rewrites.
- `NEXT_PUBLIC_WS_URL`: WebSocket base URL (default `ws://localhost:8000`).
- `BACKEND_URL`: Backend base used by Next.js rewrites in local development.

## Run Locally

```bash
npm ci
npm run dev
```

Frontend runs on `http://localhost:3000`.

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Create production build
- `npm run start` - Run production server
- `npm run lint` - Run ESLint
- `npm test` - Run Jest unit/component tests
- `npm run test:e2e` - Run Playwright smoke E2E (`pretest:e2e` runs `npm run build`, then Playwright starts **`next start`**, same as production/Vercel; `next dev` does not exercise auth middleware redirects reliably)
- `npm run test:e2e:ui` - Playwright UI mode

### E2E setup (first time)

```bash
npx playwright install chromium
npm run test:e2e
```

`npm run test:e2e` triggers a production build first. To iterate faster after a successful build, run `npx playwright test` (skips the lifecycle hook; ensure `.next` is current).

Full-stack (`npm run test:e2e:full`): backend must be **Python 3.11** (on Windows, Playwright starts **`py -3.11`**). Override with **`PLAYWRIGHT_BACKEND_PYTHON`**. SQLite for E2E defaults to the **OS temp directory** (set **`E2E_DATABASE_URL`** to force e.g. `sqlite:///./data/e2e.db`) so synced project folders do not block migrations.

Smoke tests live in `e2e/`. They do not require the backend; you may see Next.js rewrite warnings if nothing is listening on port 8000.

## Authentication Notes

- **Browser session**: Login sets an **HTTP-only `access_token` cookie** (JWT); `axios` is configured with `withCredentials: true` so authenticated API calls use the cookie.
- **WebSockets**: Before opening **`/ws/{job_id}`**, the client calls **`GET /api/auth/ws-ticket?job_id=`** (cookie auth) and passes the returned short-lived **ticket** as the `token` query param (`connectWebSocket` in `@/lib/api`). The login JSON `access_token` is not used for WS.
- **Vercel + separate API host** (`NEXT_PUBLIC_API_URL` set): the backend must allow your frontend origin (**`FRONTEND_URL`**, **`CORS_EXTRA_ORIGINS`**) and usually needs **`AUTH_COOKIE_SECURE=true`** with **`AUTH_COOKIE_SAMESITE=none`** so the session cookie works on cross-site XHR. Demo **`admin@prohr.ai` / `hr@prohr.ai`** only exist if the API is configured to seed them — see the root **README** environment table (**`SEED_DEMO_USERS`**, **`ALLOW_SEED_DEMO_USERS_OUTSIDE_DEV`**, **`DEMO_*_PASSWORD`**).
- Do not embed static credentials in UI defaults.
