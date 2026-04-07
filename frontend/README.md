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
- `npm run test:e2e` - Run Playwright E2E (starts Next automatically; use `CI=true` for production `next start`, otherwise `next dev`)
- `npm run test:e2e:ui` - Playwright UI mode

### E2E setup (first time)

```bash
npx playwright install chromium
npm run build   # required when running E2E with CI=true (matches GitHub Actions)
npm run test:e2e
```

Smoke tests live in `e2e/`. They do not require the backend; you may see Next.js rewrite warnings if nothing is listening on port 8000.

## Authentication Notes

- **Browser session**: Login sets an **HTTP-only `access_token` cookie** (JWT); `axios` is configured with `withCredentials: true` so authenticated API calls use the cookie.
- **WebSockets**: Before opening **`/ws/{job_id}`**, the client calls **`GET /api/auth/ws-ticket?job_id=`** (cookie auth) and passes the returned short-lived **ticket** as the `token` query param (`connectWebSocket` in `@/lib/api`). The login JSON `access_token` is not used for WS.
- Do not embed static credentials in UI defaults.
