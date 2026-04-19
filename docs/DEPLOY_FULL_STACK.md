# Deploy the full PRO HR stack (frontend + backend)

Vercel runs **Next.js** well, but this repo’s **FastAPI** backend (Python 3.11, SQLite/FAISS, long‑running `uvicorn`, WebSockets) is not a drop‑in Vercel “serverless function” without a large rewrite. To deploy **the entire project**, use one of the patterns below.

---

## Option A — One server: Docker Compose (simplest full stack)

Same flow as local development, on any Linux VM (DigitalOcean, AWS EC2, Azure VM, Hetzner, etc.):

1. Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/).
2. Clone the repo and create **`backend/.env`** from **`backend/.env.example`** (set at least **`SECRET_KEY`**, **`OPENAI_API_KEY`**, **`FRONTEND_URL`** to the URL users will open, e.g. `https://app.example.com` or `http://YOUR_SERVER_IP:3000`).
3. From the **repository root**:

   ```bash
   docker compose up --build -d
   ```

4. Open **`http://<host>:3000`** (or put a reverse proxy + TLS in front of ports **3000** and **8000** as needed).

The default compose file wires the **frontend** to the **backend** over the Docker network (`BACKEND_URL=http://backend:8000` at build). The browser uses **same-origin** `/api` on port **3000**; Next rewrites to the backend. WebSockets use **`NEXT_PUBLIC_WS_URL`** (see compose comments — often `ws://<host>:8000` until you terminate TLS).

**Persist data:** `./backend/data` is mounted for SQLite and FAISS; back up that directory for production.

---

## Option B — Split cloud: backend anywhere + frontend on Vercel

1. **Deploy the backend** using **`backend/Dockerfile`** (or `uvicorn` on a VM) so you get a public HTTPS origin, e.g. `https://api.yourdomain.com`.
2. Set **`FRONTEND_URL`** and **`CORS_EXTRA_ORIGINS`** on the API to your **Vercel** origin.
3. On **Vercel** (frontend project, root **`frontend/`** or repo root per README):
   - **`NEXT_PUBLIC_API_URL`** = your API origin (browser calls API directly).
   - **`NEXT_PUBLIC_WS_URL`** = `wss://…` matching your API WebSocket endpoint.
   - Cookie/CORS: if the UI and API are on **different sites**, use **`AUTH_COOKIE_SECURE=true`** and **`AUTH_COOKIE_SAMESITE=none`** on the API (see root README).

This is a full product deploy; only the **hosting** is split across two services.

---

## Option C — Split cloud: backend on Render / Railway / Fly.io + UI on same or Vercel

Same as **Option B**, but the API is a **Web Service** built from **`backend/Dockerfile`**. After the API has a stable URL, configure the frontend build/runtime env vars as above.

- **Render:** create a **Web Service** → Docker, root directory **`backend`**, set env vars in the dashboard; attach a **persistent disk** on `/app/data` if you keep SQLite/FAISS on disk.
- **Railway / Fly.io:** add a service from **`backend/`** with the same Dockerfile; set **`PORT`** / listen host per their docs.

---

## What not to expect from Vercel alone

- **No** bundled Python orchestrator, **no** SQLite file on Vercel’s serverless filesystem as a durable app DB, **no** `uvicorn` process beside what Next exposes, unless you move the API to **Vercel Functions** / Edge (not supported by this codebase as‑is).

For **one vendor, full stack** without managing a VM, use **Option B** or **Option C** (API on a container host + Next on Vercel), or **Option A** (single VM + Compose).

---

## Related

- Root **README** → Docker Compose, environment table, Vercel section.
- **`docker-compose.yml`** and **`docker-compose.direct-api.yml`** for local / server layouts.
