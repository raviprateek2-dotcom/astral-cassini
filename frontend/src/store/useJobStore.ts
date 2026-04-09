import { create } from 'zustand';
import { api } from '@/lib/api';
import { fetchWithCache, invalidateCache } from "@/lib/dataCache";
import { toast } from 'sonner';
import type { AuditLogEntry, JobDetail, JobListItem, WorkflowBlob } from "@/types/domain";

export type JobState = JobListItem & {
    state: WorkflowBlob;
    audit_log?: AuditLogEntry[];
};

type HeartbeatState = {
    current_stage?: string;
    state?: WorkflowBlob;
};

function normalizeJob(detail: JobDetail): JobState {
    return {
        ...detail,
        state: detail.state ?? {},
    };
}

interface JobStore {
    currentJob: JobState | null;
    jobsList: JobState[];
    loading: boolean;
    error: string | null;
    
    // Actions
    fetchJobsList: () => Promise<void>;
    fetchJobDetails: (jobId: string) => Promise<void>;
    setCurrentJob: (job: JobState | null) => void;
    updateJobStateFromSocket: (data: HeartbeatState) => void;
    
    // Command & Control
    approveStage: (feedback?: string, updatedJd?: string) => Promise<void>;
    rejectStage: (feedback: string) => Promise<void>;
    forceRunAgent: (action: string, stateUpdates?: WorkflowBlob) => Promise<void>;
}

export const useJobStore = create<JobStore>((set, get) => ({
    currentJob: null,
    jobsList: [],
    loading: false,
    error: null,

    fetchJobsList: async () => {
        set({ loading: true, error: null });
        try {
            const jobs = await fetchWithCache("jobs:list", () => api.listJobs(), { ttlMs: 10_000 });
            set({
                jobsList: jobs.map((j) => ({ ...j, state: {} as WorkflowBlob })),
                loading: false,
            });
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to load jobs.";
            set({ error: message, loading: false });
        }
    },

    fetchJobDetails: async (jobId: string) => {
        set({ loading: true, error: null });
        try {
            const jobDetails = await fetchWithCache(`jobs:${jobId}`, () => api.getJob(jobId), { ttlMs: 5_000 });
            set({ currentJob: normalizeJob(jobDetails), loading: false });
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to load job details.";
            set({ error: message, loading: false });
            toast.error("Failed to load job details.");
        }
    },

    setCurrentJob: (job) => set({ currentJob: job }),

    updateJobStateFromSocket: (data) => {
        const currentJob = get().currentJob;
        if (!currentJob) return;

        set({
            currentJob: {
                ...currentJob,
                current_stage: data.current_stage || currentJob.current_stage,
                state: {
                    ...currentJob.state,
                    ...(data.state ?? {}),
                },
            },
        });
    },

    approveStage: async (feedback = "", updatedJd) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;
        
        set({ loading: true });
        try {
            await api.approveStage(jobId, feedback, updatedJd);
            invalidateCache(`jobs:${jobId}`);
            invalidateCache("jobs:list");
            toast.success("Stage approved! Advancing workflow.");
            await get().fetchJobDetails(jobId);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to approve stage.";
            set({ error: message, loading: false });
            toast.error(message);
        }
    },

    rejectStage: async (feedback) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;

        set({ loading: true });
        try {
            await api.rejectStage(jobId, feedback);
            invalidateCache(`jobs:${jobId}`);
            invalidateCache("jobs:list");
            toast.success("Feedback submitted. Re-running stage.");
            await get().fetchJobDetails(jobId);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to reject stage.";
            set({ error: message, loading: false });
            toast.error(message);
        }
    },

    forceRunAgent: async (action, stateUpdates = {}) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;

        set({ loading: true });
        try {
            await api.patchState(jobId, action, stateUpdates);
            invalidateCache(`jobs:${jobId}`);
            invalidateCache("jobs:list");
            toast.success(`Action '${action}' executed successfully.`);
            await get().fetchJobDetails(jobId);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Failed to execute action.";
            set({ error: message, loading: false });
            toast.error(message);
        }
    }
}));
