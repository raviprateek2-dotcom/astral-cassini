import { test as base, expect, type Page } from "@playwright/test";

/**
 * Stubs backend `/api/*` so Next does not proxy to a missing :8000 during smoke tests.
 * Critical: `/api/auth/me` must be 401 so the shell does not treat `{}` as a logged-in user.
 */
async function installApiStubs(page: Page): Promise<void> {
    await page.route("**/api/**", async (route) => {
        const url = route.request().url();
        if (url.includes("/api/auth/me")) {
            await route.fulfill({
                status: 401,
                contentType: "application/json",
                body: JSON.stringify({ detail: "Not authenticated" }),
            });
            return;
        }
        await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({}),
        });
    });
}

export const test = base.extend({
    page: async ({ page }, use) => {
        await installApiStubs(page);
        await use(page);
    },
});

export { expect };
