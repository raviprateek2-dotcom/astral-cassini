import { test as base, expect, type Page } from "@playwright/test";

/**
 * Stubs backend `/api/*` so Next does not proxy to a missing :8000 during smoke tests.
 * Critical: `/api/auth/me` must be 401 so the shell does not treat `{}` as a logged-in user.
 */
function apiPathname(url: string): string {
    try {
        return new URL(url).pathname;
    } catch {
        return "";
    }
}

async function installApiStubs(page: Page): Promise<void> {
    await page.route("**/api/**", async (route) => {
        const url = route.request().url();
        const method = route.request().method();
        if (url.includes("/api/auth/me")) {
            await route.fulfill({
                status: 401,
                contentType: "application/json",
                body: JSON.stringify({ detail: "Not authenticated" }),
            });
            return;
        }
        const path = apiPathname(url);
        if (method === "GET" && path === "/api/jobs") {
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify([]),
            });
            return;
        }
        const interviewsMatch = path.match(/^\/api\/workflow\/([^/]+)\/interviews$/);
        if (method === "GET" && interviewsMatch) {
            const jobId = interviewsMatch[1];
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    job_id: jobId,
                    scheduled_interviews: [],
                    interview_assessments: [],
                }),
            });
            return;
        }
        const recsMatch = path.match(/^\/api\/workflow\/([^/]+)\/recommendations$/);
        if (method === "GET" && recsMatch) {
            const jobId = recsMatch[1];
            await route.fulfill({
                status: 200,
                contentType: "application/json",
                body: JSON.stringify({
                    job_id: jobId,
                    final_recommendations: [],
                    decision_traces: [],
                }),
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
