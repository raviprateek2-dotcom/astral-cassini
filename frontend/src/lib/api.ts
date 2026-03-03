/**
 * API client for PRO HR backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let currentAuthToken = "";

export function setAuthToken(token: string) {
    currentAuthToken = token;
}

async function fetchAPI(endpoint: string, options?: RequestInit) {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (currentAuthToken) {
        headers["Authorization"] = `Bearer ${currentAuthToken}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: { ...headers, ...options?.headers },
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        if (res.status === 401 && typeof window !== 'undefined') {
            // Token expired or invalid
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "/login";
        }
        throw new Error(err.detail || `API Error: ${res.status}`);
    }
    return res.json();
}

// --- Jobs ---
export interface CreateJobPayload {
    job_title: string;
    department: string;
    requirements: string[];
    preferred_qualifications?: string[];
    location?: string;
    salary_range?: string;
}

export const api = {
    setToken: setAuthToken,

    // Auth
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Login failed" }));
            throw new Error(err.detail || "Login failed");
        }
        return res.json();
    },

    // Analytics
    getAnalyticsSummary: () => fetchAPI("/api/analytics/summary"),
    getAnalyticsFunnel: () => fetchAPI("/api/analytics/funnel"),
    getAnalyticsRecent: () => fetchAPI("/api/analytics/recent_activity"),
    getAnalyticsDepartments: () => fetchAPI("/api/analytics/department_breakdown"),
    getAnalyticsTime: () => fetchAPI("/api/analytics/time_to_hire"),

    // Jobs
    createJob: (data: CreateJobPayload) =>
        fetchAPI("/api/jobs", { method: "POST", body: JSON.stringify(data) }),
    listJobs: () => fetchAPI("/api/jobs"),
    getJob: (id: string) => fetchAPI(`/api/jobs/${id}`),

    // Workflow
    approveStage: (id: string, feedback = "") =>
        fetchAPI(`/api/jobs/${id}/approve`, {
            method: "POST",
            body: JSON.stringify({ feedback }),
        }),
    rejectStage: (id: string, feedback: string) =>
        fetchAPI(`/api/jobs/${id}/reject`, {
            method: "POST",
            body: JSON.stringify({ feedback }),
        }),
    getStatus: (id: string) => fetchAPI(`/api/jobs/${id}/status`),
    getAudit: (id: string) => fetchAPI(`/api/jobs/${id}/audit`),
    getInterviews: (id: string) => fetchAPI(`/api/jobs/${id}/interviews`),
    getRecommendations: (id: string) => fetchAPI(`/api/jobs/${id}/recommendations`),

    // Candidates
    getCandidates: (jobId: string) => fetchAPI(`/api/jobs/${jobId}/candidates`),
    getResumeCount: () => fetchAPI("/api/resumes/count"),
    uploadResume: async (jobId: string, file: File) => {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/api/jobs/${jobId}/resumes`, {
            method: "POST",
            headers: {
                ...(currentAuthToken ? { "Authorization": `Bearer ${currentAuthToken}` } : {}),
            },
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Upload failed" }));
            throw new Error(err.detail || "Upload failed");
        }
        return res.json();
    },

    // Health
    health: () => fetchAPI("/api/health"),
};

// --- WebSocket ---
export function connectWebSocket(
    jobId: string,
    onMessage: (data: any) => void
): { close: () => void } {
    const wsUrl = `ws://localhost:8000/ws/${jobId}`;
    let socket: WebSocket | null = null;
    let reconnectAttempts = 0;
    let isClosedManually = false;

    function connect() {
        if (isClosedManually) return;

        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log(`WebSocket connected for job ${jobId}`);
            reconnectAttempts = 0;
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (err) {
                console.error("Failed to parse WS message", err);
            }
        };

        socket.onclose = () => {
            if (isClosedManually) return;

            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`WebSocket closed. Reconnecting in ${delay}ms... (Attempt ${reconnectAttempts + 1})`);

            setTimeout(() => {
                reconnectAttempts++;
                connect();
            }, delay);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
            socket?.close();
        };
    }

    connect();

    return {
        close: () => {
            isClosedManually = true;
            socket?.close();
        }
    };
}
