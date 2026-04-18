import { expect, test } from "./fixtures";

test.describe("smoke", () => {
    test("landing page loads", async ({ page }) => {
        await page.goto("/");
        await expect(page).toHaveTitle(/PRO HR/i);
        await expect(page).toHaveURL(/\/$|\/login$/);
    });

    test("login page loads", async ({ page }) => {
        await page.goto("/login");
        await expect(page.getByRole("heading", { name: /AGENT/i })).toBeVisible();
        await expect(page.getByText("Multi-Agent Recruitment Ecosystem")).toBeVisible();
    });

    test("login route is directly reachable", async ({ page }) => {
        await page.goto("/login");
        await expect(page).toHaveURL(/\/login$/);
    });

    test("protected route redirects before app shell without session cookie", async ({ page, context }) => {
        await context.clearCookies();
        await page.goto("/jobs");
        await expect(page).toHaveURL(/\/\?next=/);
        const u = new URL(page.url());
        expect(u.searchParams.get("next")).toBeTruthy();
    });
});
