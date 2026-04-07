/**
 * API client for PRO HR backend using Axios.
 */
import axios from 'axios';

const API_BASE = ""; // Handled by Next.js rewrites in development

export const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to inject the token
apiClient.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = localStorage.getItem("token");
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
    }
    return config;
});

// Response interceptor to handle unauth
apiClient.interceptors.response.use(
    (response) => response.data,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.location.href = "/login";
        }
        return Promise.reject(new Error(error.response?.data?.detail || error.message || "API Error"));
    }
);

export function setAuthToken(token: string) {
    if (typeof window !== "undefined") {
        if (token) {
            localStorage.setItem("token", token);
        } else {
            localStorage.removeItem("token");
        }
    }
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

export const api = {
    setToken: setAuthToken,

    // Auth
    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const res = await apiClient.post("/api/auth/login", formData, {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
        });
        return res;
    },

    // Analytics
    getAnalyticsDepartments: () => apiClient.get("/api/analytics/department_breakdown"),
    getAnalyticsDashboard: () => apiClient.get("/api/analytics/dashboard"),

    // Jobs
    createJob: (data: CreateJobPayload) => apiClient.post("/api/jobs", data),
    listJobs: () => apiClient.get("/api/jobs"),
    getJob: (id: string) => apiClient.get(`/api/jobs/${id}`),

    // Workflow
    approveStage: (id: string, feedback = "", updatedJD?: string) =>
        apiClient.post(`/api/workflow/${id}/approve`, { feedback, updated_jd: updatedJD }),
    rejectStage: (id: string, feedback: string) =>
        apiClient.post(`/api/workflow/${id}/reject`, { feedback }),
    patchState: (id: string, action: string, stateUpdates: any = {}) => 
        apiClient.patch(`/api/workflow/${id}/state`, { action, state_updates: stateUpdates }),
    getStatus: (id: string) => apiClient.get(`/api/workflow/${id}/status`),
    getAudit: (id: string) => apiClient.get(`/api/workflow/${id}/audit`),
    getInterviews: (id: string) => apiClient.get(`/api/workflow/${id}/interviews`),
    getRecommendations: (id: string) => apiClient.get(`/api/workflow/${id}/recommendations`),

    // Candidates
    getCandidates: (jobId: string) => apiClient.get(`/api/jobs/${jobId}/candidates`),
    getResumeCount: () => apiClient.get("/api/resumes/count"),
    uploadResume: async (jobId: string, file: File) => {
        const formData = new FormData();
        formData.append("file", file);
        return apiClient.post(`/api/jobs/${jobId}/resumes`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
        });
    },

    // Health
    health: () => apiClient.get("/api/health"),
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
            setTimeout(() => {
                reconnectAttempts++;
                connect();
            }, delay);
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
