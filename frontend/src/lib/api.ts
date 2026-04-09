/**
 * API client for PRO HR backend using Axios.
 */
import axios from 'axios';
import type {
    AuditLogEntry,
    CandidateLike,
    InterviewsApiResponse,
    JobDetail,
    JobListItem,
    RecommendationsApiResponse,
} from "@/types/domain";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const apiClient = axios.create({
    baseURL: API_BASE,
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

type DataClient = Omit<typeof apiClient, "get" | "post" | "patch"> & {
    get<T = unknown>(...args: Parameters<typeof apiClient.get>): Promise<T>;
    post<T = unknown>(...args: Parameters<typeof apiClient.post>): Promise<T>;
    patch<T = unknown>(...args: Parameters<typeof apiClient.patch>): Promise<T>;
};

const dataClient = apiClient as unknown as DataClient;

// Response interceptor to handle unauth
apiClient.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem("user");
            sessionStorage.removeItem("ws_token");
            // Stay on login (wrong-password 401) or landing; otherwise send users to the landing page.
            const p = window.location.pathname;
            if (p !== "/login" && p !== "/") {
                window.location.href = "/";
            }
        }
        return Promise.reject(new Error(error.response?.data?.detail || error.message || "API Error"));
    }
);

export function setAuthToken(token: string) {
    // Legacy no-op for old call sites. Auth now uses secure HTTP-only cookies.
    void token;
}

// --- Types ---
export interface CreateJobPayload {
    job_title: string;
    department: string;
    requirements: string[];
    preferred_qualifications?: string[];
    location?: string;
    salary_range?: string;
}

export interface AuthUser {
    role: string;
    full_name: string;
    email?: string;
}

/** GET /api/auth/me — matches backend UserResponse. */
export type MeResponse = {
    id: number;
    email: string;
    full_name: string;
    role: string;
    department?: string | null;
    is_active?: boolean;
};

export type WsTicketResponse = {
    ticket: string;
    aud: string;
    expires_in_seconds: number;
};

export interface LoginResponse {
    user: AuthUser;
    access_token: string;
}

export interface CreateJobResponse {
    job_id: string;
}

export type CandidatesApiResponse = {
    scored_candidates?: CandidateLike[];
    candidates?: CandidateLike[];
    final_recommendations?: CandidateLike[];
};

export type HealthResponse = {
    status?: string;
    llm_model?: string;
    embedding_model?: string;
    indexed_resumes?: number;
    openai_configured?: boolean;
    observability?: Record<string, number>;
};

export type AnalyticsDashboardPayload = {
    summary?: {
        average_screening_score?: number;
        total_candidates_scored?: number;
        total_hires?: number;
    };
    funnel?: Array<{ stage: string; count: number }>;
    recent?: Array<{ timestamp?: string }>;
    time_to_hire?: Array<{ department: string; avg_days: number }>;
};

export type ScoreDistributionPayload = {
    distribution: Array<{ range: string; count: number }>;
};

export type WorkflowStateUpdates = Record<string, unknown>;

export interface PipelineEvent {
    type: string;
    job_id: string;
    data: Record<string, unknown>;
}

export const api = {
    setToken: setAuthToken,

    // Auth
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        return dataClient.post<LoginResponse>("/api/auth/login", formData, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        });
    },
    logout: async () => dataClient.post("/api/auth/logout"),
    me: async () => dataClient.get<MeResponse>("/api/auth/me"),
    getWsTicket: (jobId: string) =>
        dataClient.get<WsTicketResponse>("/api/auth/ws-ticket", { params: { job_id: jobId } }),

    // Analytics
    getAnalyticsDepartments: () => dataClient.get("/api/analytics/department_breakdown"),
    getAnalyticsDashboard: () => dataClient.get<AnalyticsDashboardPayload>("/api/analytics/dashboard"),
    getAnalyticsScoreDistribution: () =>
        dataClient.get<ScoreDistributionPayload>("/api/analytics/score_distribution"),

    // Jobs
    createJob: (data: CreateJobPayload) => dataClient.post<CreateJobResponse>("/api/jobs", data),
    listJobs: () => dataClient.get<JobListItem[]>("/api/jobs"),
    getJob: (id: string) => dataClient.get<JobDetail>(`/api/jobs/${id}`),
    deleteJob: (id: string) => dataClient.delete<{ status: string; job_id: string }>(`/api/jobs/${id}`),

    // Workflow
    approveStage: (id: string, feedback = "", updatedJD?: string) =>
        dataClient.post(`/api/workflow/${id}/approve`, { feedback, updated_jd: updatedJD }),
    rejectStage: (id: string, feedback: string) =>
        dataClient.post(`/api/workflow/${id}/reject`, { feedback }),
    patchState: (id: string, action: string, stateUpdates: WorkflowStateUpdates = {}) =>
        dataClient.patch(`/api/workflow/${id}/state`, { action, state_updates: stateUpdates }),
    getStatus: (id: string) => dataClient.get(`/api/workflow/${id}/status`),
    getAudit: (id: string) => dataClient.get<{ audit_log?: AuditLogEntry[] }>(`/api/workflow/${id}/audit`),
    getInterviews: (id: string) => dataClient.get<InterviewsApiResponse>(`/api/workflow/${id}/interviews`),
    getRecommendations: (id: string) =>
        dataClient.get<RecommendationsApiResponse>(`/api/workflow/${id}/recommendations`),
    sendInterviewInvite: (id: string, payload: Record<string, unknown>) =>
        dataClient.post(`/api/workflow/${id}/interview-invite`, payload),
    completeInterview: (id: string, payload: Record<string, unknown>) =>
        dataClient.post(`/api/workflow/${id}/interview-complete`, payload),
    generateOffer: (id: string) => dataClient.post(`/api/workflow/${id}/generate-offer`),

    // Candidates
    getCandidates: (jobId: string) =>
        dataClient.get<CandidatesApiResponse>(`/api/jobs/${jobId}/candidates`),
    getResumeCount: () => dataClient.get("/api/resumes/count"),
    /** Job-scoped upload (canonical). For job-agnostic indexing see POST /api/resumes/upload on the backend. */
    uploadResume: async (jobId: string, file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        return dataClient.post(`/api/jobs/${jobId}/resumes`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
        });
    },

    // Health
    health: () => dataClient.get<HealthResponse>("/api/health"),
};

// --- WebSocket ---
/** Fetches a short-lived WS ticket (cookie session) before connecting; refreshes ticket on reconnect. */
export async function connectWebSocket(
    jobId: string,
    onMessage: (data: PipelineEvent) => void
): Promise<{ close: () => void }> {
    let socket: WebSocket | null = null;
    let reconnectAttempts = 0;
    let isClosedManually = false;

    const scheduleReconnect = () => {
        if (isClosedManually) return;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        reconnectAttempts++;
        setTimeout(() => void openConnection(), delay);
    };

    async function openConnection() {
        if (isClosedManually) return;
        let ticket: string;
        try {
            ({ ticket } = await api.getWsTicket(jobId));
        } catch {
            scheduleReconnect();
            return;
        }
        if (isClosedManually) return;
        const wsUrl = `${WS_BASE}/ws/${jobId}?token=${encodeURIComponent(ticket)}`;
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log(`WebSocket connected for job ${jobId}`);
            reconnectAttempts = 0;
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as PipelineEvent;
                onMessage(data);
            } catch (err) {
                console.error("Failed to parse WS message", err);
            }
        };

        socket.onclose = () => {
            if (isClosedManually) return;
            scheduleReconnect();
        };
    }

    await openConnection();

    return {
        close: () => {
            isClosedManually = true;
            socket?.close();
        }
    };
}
