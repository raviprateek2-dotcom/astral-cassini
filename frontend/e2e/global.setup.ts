import fs from "node:fs";
import path from "node:path";

import { test as setup } from "@playwright/test";

const authDir = path.join(__dirname, ".auth");
const authFile = path.join(authDir, "user.json");

/**
 * Registers (if needed) and logs in via same-origin /api (Next rewrite → backend).
 * Persists HttpOnly session cookie for chromium-authed tests.
 */
setup("authenticate", async ({ request }) => {
    fs.mkdirSync(authDir, { recursive: true });

    // Avoid .test / example.* TLDs — Pydantic EmailStr treats them as reserved.
    const email = process.env.E2E_USER_EMAIL ?? "e2e-viewer@prohr-e2e.xyz";
    const password = process.env.E2E_USER_PASSWORD ?? "E2E-viewer-Passw0rd!Long";

    const reg = await request.post("/api/auth/register", {
        headers: { "Content-Type": "application/json" },
        data: JSON.stringify({
            email,
            full_name: "Playwright E2E",
            password,
            department: "E2E",
        }),
    });
    if (!reg.ok() && reg.status() !== 400) {
        throw new Error(`E2E register failed: ${reg.status()} ${await reg.text()}`);
    }

    const login = await request.post("/api/auth/login", {
        form: { username: email, password },
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    if (!login.ok()) {
        throw new Error(`E2E login failed: ${login.status()} ${await login.text()}`);
    }

    await request.storageState({ path: authFile });
});
