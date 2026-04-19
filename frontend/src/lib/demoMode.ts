/**
 * When true (build-time env), the UI skips real API login/session checks so a
 * deployed demo can open without a live backend cookie. Never enable on a real production site.
 */
export function isFrontendDemoMode(): boolean {
    const v = process.env.NEXT_PUBLIC_DEMO_MODE;
    return v === "1" || (typeof v === "string" && v.toLowerCase() === "true");
}
