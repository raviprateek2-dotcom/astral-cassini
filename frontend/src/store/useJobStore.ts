import { create } from 'zustand';
import { api } from '@/lib/api';
import { toast } from 'sonner';

export interface JobState {
    job_id: string;
    job_title: string;
    department: string;
    current_stage: string;
    state: any;
}

interface JobStore {
    currentJob: JobState | null;
    jobsList: any[];
    loading: boolean;
    error: string | null;
    
    // Actions
    fetchJobsList: () => Promise<void>;
    fetchJobDetails: (jobId: string) => Promise<void>;
    setCurrentJob: (job: JobState | null) => void;
    updateJobStateFromSocket: (data: any) => void;
    
    // Command & Control
    approveStage: (feedback?: string, updatedJd?: string) => Promise<void>;
    rejectStage: (feedback: string) => Promise<void>;
    forceRunAgent: (action: string, stateUpdates?: any) => Promise<void>;
}

export const useJobStore = create<JobStore>((set, get) => ({
    currentJob: null,
    jobsList: [],
    loading: false,
    error: null,

    fetchJobsList: async () => {
        set({ loading: true, error: null });
        try {
            const jobs = await api.listJobs();
            set({ jobsList: jobs, loading: false });
        } catch (err: any) {
            set({ error: err.message, loading: false });
        }
    },

    fetchJobDetails: async (jobId: string) => {
        set({ loading: true, error: null });
        try {
            const jobDetails = await api.getJob(jobId);
            set({ currentJob: jobDetails, loading: false });
        } catch (err: any) {
            set({ error: err.message, loading: false });
            toast.error("Failed to load job details.");
        }
    },

    setCurrentJob: (job) => set({ currentJob: job }),

    updateJobStateFromSocket: (data) => {
        const currentJob = get().currentJob;
        if (!currentJob) return;

        // Merge incoming WebSocket heartbeat data into current job state
        set({
            currentJob: {
                ...currentJob,
                current_stage: data.current_stage || currentJob.current_stage,
                state: {
                    ...currentJob.state,
                    ...data.state,
                }
            }
        });
    },

    approveStage: async (feedback = "", updatedJd) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;
        
        set({ loading: true });
        try {
            await api.approveStage(jobId, feedback, updatedJd);
            toast.success("Stage approved! Advancing workflow.");
            await get().fetchJobDetails(jobId);
        } catch (err: any) {
            set({ error: err.message, loading: false });
            toast.error(err.message || "Failed to approve stage.");
        }
    },

    rejectStage: async (feedback) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;

        set({ loading: true });
        try {
            await api.rejectStage(jobId, feedback);
            toast.success("Feedback submitted. Re-running stage.");
            await get().fetchJobDetails(jobId);
        } catch (err: any) {
            set({ error: err.message, loading: false });
            toast.error(err.message || "Failed to reject stage.");
        }
    },

    forceRunAgent: async (action, stateUpdates = {}) => {
        const jobId = get().currentJob?.job_id;
        if (!jobId) return;

        set({ loading: true });
        try {
            await api.patchState(jobId, action, stateUpdates);
            toast.success(`Action '${action}' executed successfully.`);
            await get().fetchJobDetails(jobId);
        } catch (err: any) {
            set({ error: err.message, loading: false });
            toast.error(err.message || "Failed to execute action.");
        }
    }
}));
