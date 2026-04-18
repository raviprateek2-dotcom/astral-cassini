import { expect, test } from "@playwright/test";

/**
 * Requires PLAYWRIGHT_FULL_STACK=1: real backend + session cookie from global.setup.ts.
 * Lets /api/auth/me reach the backend (session cookie). Stubs only GET /api/jobs and
 * workflow endpoints so UI data stay deterministic.
 */
function pathname(url: string): string {
    try {
        return new URL(url).pathname.replace(/\/$/, "") || "/";
    } catch {
        return "";
    }
}

test.describe("authenticated app", () => {
    test("interviews page shows meeting link", async ({ page }) => {
        await page.route("**/api/**", async (route) => {
            const url = route.request().url();
            const method = route.request().method();
            const path = pathname(url);
            if (url.includes("/api/auth/") && !url.includes("/api/auth/me")) {
                await route.fallback();
                return;
            }
            if (method === "GET" && path === "/api/jobs") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([
                        {
                            job_id: "e2e-job",
                            job_title: "E2E Role",
                            department: "QA",
                            current_stage: "interviewing",
                        },
                    ]),
                });
                return;
            }
            if (method === "GET" && path === "/api/workflow/e2e-job/interviews") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        job_id: "e2e-job",
                        scheduled_interviews: [
                            {
                                candidate_name: "Test Candidate",
                                interview_type: "technical",
                                scheduled_time: new Date("2030-01-15T14:00:00Z").toISOString(),
                                duration_minutes: 60,
                                interviewers: [],
                                status: "scheduled",
                                meeting_link: "https://meet.example.com/room-e2e",
                            },
                        ],
                        interview_assessments: [],
                    }),
                });
                return;
            }
            if (method === "GET" && path === "/api/jobs/e2e-job") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        job_id: "e2e-job",
                        job_title: "E2E Role",
                        department: "QA",
                        current_stage: "interviewing",
                        state: {},
                    }),
                });
                return;
            }
            await route.fallback();
        });

        await page.goto("/interviews");
        await expect(page.getByRole("heading", { name: /Interview Management/i })).toBeVisible();
        await expect(page.getByRole("option", { name: /E2E Role/i })).toBeAttached();
        await page.getByRole("combobox").selectOption({ value: "e2e-job" });
        await expect(page.getByRole("link", { name: /Join/i })).toHaveAttribute(
            "href",
            "https://meet.example.com/room-e2e",
        );
    });

    test("decisions page shows decision trace", async ({ page }) => {
        await page.route("**/api/**", async (route) => {
            const url = route.request().url();
            const method = route.request().method();
            const path = pathname(url);
            if (url.includes("/api/auth/") && !url.includes("/api/auth/me")) {
                await route.fallback();
                return;
            }
            if (method === "GET" && path === "/api/jobs") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([
                        {
                            job_id: "e2e-dec",
                            job_title: "E2E Decisions",
                            department: "QA",
                            current_stage: "decision",
                        },
                    ]),
                });
                return;
            }
            if (method === "GET" && path === "/api/workflow/e2e-dec/recommendations") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        job_id: "e2e-dec",
                        final_recommendations: [
                            {
                                candidate_id: "c-e2e",
                                candidate_name: "Trace Person",
                                decision: "hire",
                                confidence: 82,
                                screening_weight: 33,
                                interview_weight: 49,
                                overall_weighted_score: 82,
                                reasoning: "Deterministic test reasoning.",
                                risk_factors: [],
                            },
                        ],
                        decision_traces: [
                            {
                                candidate_id: "c-e2e",
                                candidate_name: "Trace Person",
                                screening_score: 80,
                                interview_score_scaled: 83,
                                concerns_count: 0,
                                weighted_score: 82,
                                decision: "hire",
                                rule_applied: "weighted>=75&&concerns<3=>hire",
                            },
                        ],
                    }),
                });
                return;
            }
            await route.fallback();
        });

        await page.goto("/decisions");
        await expect(page.getByRole("heading", { name: /Final Decisions/i })).toBeVisible();
        await expect(page.getByRole("option", { name: /E2E Decisions/i })).toBeAttached();
        await page.getByRole("combobox").selectOption({ value: "e2e-dec" });
        await expect(page.getByText(/Trace Person/i).first()).toBeVisible();
        await expect(page.getByText(/Decision Trace/i)).toBeVisible();
        await expect(page.getByText(/weighted>=75&&concerns<3=>hire/)).toBeVisible();
    });

    const compliantJDForApprovals = [
        "Role Summary: E2E approval role.",
        "Core Responsibilities: Run Playwright and verify gates.",
        "Required Qualifications: TypeScript",
        "Preferred Qualifications: Testing mindset",
        "Compensation & Benefits: Competitive",
        "Interview Process: Two rounds",
        "Equal Opportunity Statement: We are an equal opportunity employer.",
    ].join("\n\n");

    test("approvals page shows JD gate and clears after approve", async ({ page }) => {
        let approved = false;
        await page.route("**/api/**", async (route) => {
            const url = route.request().url();
            const method = route.request().method();
            const path = pathname(url);
            if (url.includes("/api/auth/") && !url.includes("/api/auth/me")) {
                await route.fallback();
                return;
            }
            if (method === "GET" && path === "/api/jobs") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify(
                        approved
                            ? []
                            : [
                                  {
                                      job_id: "e2e-approval",
                                      job_title: "E2E Approvals",
                                      department: "QA",
                                      current_stage: "jd_review",
                                  },
                              ],
                    ),
                });
                return;
            }
            if (method === "GET" && path === "/api/jobs/e2e-approval") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        job_id: "e2e-approval",
                        job_title: "E2E Approvals",
                        department: "QA",
                        current_stage: "jd_review",
                        state: {
                            jd_approval: "pending",
                            job_description: compliantJDForApprovals,
                        },
                        audit_log: [],
                    }),
                });
                return;
            }
            if (method === "POST" && path === "/api/workflow/e2e-approval/approve") {
                approved = true;
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({ ok: true }),
                });
                return;
            }
            await route.fallback();
        });

        await page.goto("/approvals");
        await expect(page.getByRole("heading", { name: /Approval Gates/i })).toBeVisible();
        await expect(page.getByText(/E2E Approvals/i)).toBeVisible();
        await page.getByRole("button", { name: /Approve & Continue/i }).click();
        await expect(page.getByRole("heading", { name: /All Clear!/i })).toBeVisible();
    });

    test("audit page shows timeline entries", async ({ page }) => {
        await page.route("**/api/**", async (route) => {
            const url = route.request().url();
            const method = route.request().method();
            const path = pathname(url);
            if (url.includes("/api/auth/") && !url.includes("/api/auth/me")) {
                await route.fallback();
                return;
            }
            if (method === "GET" && path === "/api/jobs") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify([
                        {
                            job_id: "e2e-audit",
                            job_title: "E2E Audit Job",
                            department: "QA",
                            current_stage: "completed",
                        },
                    ]),
                });
                return;
            }
            if (method === "GET" && path === "/api/workflow/e2e-audit/audit") {
                await route.fulfill({
                    status: 200,
                    contentType: "application/json",
                    body: JSON.stringify({
                        audit_log: [
                            {
                                agent: "JD Architect",
                                action: "jd_drafted",
                                details: "Deterministic audit row for E2E.",
                                timestamp: "2030-02-01T12:00:00.000Z",
                                stage: "jd_drafting",
                            },
                        ],
                    }),
                });
                return;
            }
            await route.fallback();
        });

        await page.goto("/audit");
        await expect(page.getByRole("heading", { name: /Audit Trail/i })).toBeVisible();
        await page.getByTitle("Select pipeline for audit trail").selectOption("e2e-audit");
        await expect(page.getByText(/Deterministic audit row for E2E/i)).toBeVisible();
        await expect(page.getByText(/jd drafted/i)).toBeVisible();
    });
});
