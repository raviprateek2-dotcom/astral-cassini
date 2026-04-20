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

## Option C — Split cloud: backend on Render / Railway + UI on Vercel

### 1. Backend on [Render.com](https://render.com)
1. Create a **New > Web Service**.
2. Connect your GitHub repository.
3. **Root Directory**: `backend`
4. **Environment Variables**:
   - `OPENAI_API_KEY`: (Your key)
   - `SECRET_KEY`: (32+ character random string)
   - `FRONTEND_URL`: `https://YOUR_APP.vercel.app` (The URL your team will visit)
   - `AUTH_COOKIE_SECURE`: `true`
   - `AUTH_COOKIE_SAMESITE`: `none`
   - `SEED_DEMO_USERS`: `true`
   - `ALLOW_SEED_DEMO_USERS_OUTSIDE_DEV`: `true`
5. **Persistent Disk**: Go to **Disk** settings and add a disk mounted at `/app/data` (1GB). This ensures your resumes and users aren't deleted on restart.

### 2. Frontend on [Vercel.com](https://vercel.com)
1. Create a **New Project**.
2. Connect your GitHub repository.
3. **Root Directory**: `frontend`
4. **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend.onrender.com` (Your Render URL)
   - `NEXT_PUBLIC_WS_URL`: `wss://your-backend.onrender.com` (Your Render URL with `wss://`)
5. Click **Deploy**.

---

## Important Security Note
Because the UI and API are on different domains, the `AUTH_COOKIE_SAMESITE=none` and `AUTH_COOKIE_SECURE=true` settings are **mandatory**. Without them, browsers will block the session cookie and login will fail.

## What not to expect from Vercel alone

- **No** bundled Python orchestrator, **no** SQLite file on Vercel’s serverless filesystem as a durable app DB, **no** `uvicorn` process beside what Next exposes, unless you move the API to **Vercel Functions** / Edge (not supported by this codebase as‑is).

For **one vendor, full stack** without managing a VM, use **Option B** or **Option C** (API on a container host + Next on Vercel), or **Option A** (single VM + Compose).

---

## Related

- Root **README** → Docker Compose, environment table, Vercel section.
- **`docker-compose.yml`** and **`docker-compose.direct-api.yml`** for local / server layouts.
