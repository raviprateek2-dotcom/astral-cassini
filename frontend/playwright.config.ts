import path from "node:path";

import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.PORT) || 3000;
const baseURL = `http://127.0.0.1:${PORT}`;
const backendURL = process.env.PLAYWRIGHT_BACKEND_URL ?? "http://127.0.0.1:8000";
const backendPort = (() => {
    try {
        const p = new URL(backendURL).port;
        return p || "8000";
    } catch {
        return "8000";
    }
})();
const fullStack = process.env.PLAYWRIGHT_FULL_STACK === "1";
const frontendDir = process.cwd();
const backendDir = path.join(frontendDir, "..", "backend");
const authStatePath = path.join(frontendDir, "e2e", ".auth", "user.json");

/**
 * Default: smoke tests only (mocked API). Set PLAYWRIGHT_FULL_STACK=1 (see npm run test:e2e:full)
 * to run global.setup.ts (real register/login) and app.authenticated.spec.ts against the backend +
 * production Next (`npm run start`). Run `npm run build` first so the UI matches the repo (stale .next
 * will fail assertions). Optional: PLAYWRIGHT_BACKEND_URL (default http://127.0.0.1:8000) and matching
 * uvicorn port when 8000 is already taken.
 */
export default defineConfig({
    testDir: "./e2e",
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: process.env.CI ? "list" : [["list"], ["html", { open: "never" }]],
    use: {
        baseURL,
        trace: "on-first-retry",
        screenshot: "only-on-failure",
    },
    projects: [
        {
            name: "chromium-smoke",
            testMatch: /smoke\.spec\.ts$/,
            use: { ...devices["Desktop Chrome"] },
        },
        ...(fullStack
            ? [
                  { name: "setup", testMatch: /global\.setup\.ts$/ },
                  {
                      name: "chromium-authed",
                      dependencies: ["setup"],
                      testMatch: /app\.authenticated\.spec\.ts$/,
                      use: {
                          ...devices["Desktop Chrome"],
                          storageState: authStatePath,
                      },
                  },
              ]
            : []),
    ],
    webServer: fullStack
        ? [
              {
                  command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
                  cwd: backendDir,
                  // Root avoids importing RAG/embeddings (see /api/health → get_collection_count).
                  url: `${backendURL}/`,
                  reuseExistingServer: !process.env.CI,
                  timeout: 120_000,
                  env: {
                      ...process.env,
                      SECRET_KEY: process.env.SECRET_KEY ?? "local-dev-secret-key-must-be-32chars-long",
                      DATABASE_URL: process.env.E2E_DATABASE_URL ?? "sqlite:///./data/e2e.db",
                      APP_ENV: "development",
                  },
              },
              {
                  command: `npm run start -- -p ${PORT}`,
                  cwd: frontendDir,
                  url: baseURL,
                  reuseExistingServer: !process.env.CI,
                  timeout: 180_000,
                  env: {
                      ...process.env,
                      BACKEND_URL: backendURL,
                  },
              },
          ]
        : {
              command: process.env.CI ? `npm run start -- -p ${PORT}` : `npm run dev -- -p ${PORT}`,
              cwd: frontendDir,
              url: baseURL,
              reuseExistingServer: !process.env.CI,
              timeout: 180_000,
          },
});
