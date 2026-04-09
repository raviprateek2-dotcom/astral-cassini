"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import { toast } from "sonner";
import { AgentThinking } from "@/components/AgentThinking";
import type { JobListItem } from "@/types/domain";

const STAGES = [
    { key: "intake", label: "Intake", color: "#64748b", icon: "📥" },
    { key: "jd_drafting", label: "Drafting JD", color: "#3b82f6", icon: "📝" },
    { key: "jd_review", label: "JD Review ⏳", color: "#f59e0b", icon: "🤝" },
    { key: "sourcing", label: "Sourcing", color: "#06b6d4", icon: "🔍" },
    { key: "screening", label: "Screening", color: "#8b5cf6", icon: "📊" },
    { key: "shortlist_review", label: "Shortlist ⏳", color: "#f59e0b", icon: "🤝" },
    { key: "outreach", label: "Outreach", color: "#0ea5e9", icon: "📣" },
    { key: "engagement", label: "Engagement", color: "#14b8a6", icon: "💬" },
    { key: "scheduling", label: "Scheduling", color: "#10b981", icon: "📅" },
    { key: "interviewing", label: "Interviews", color: "#ec4899", icon: "🎙️" },
    { key: "decision", label: "Decision", color: "#f43f5e", icon: "⚖️" },
    { key: "hire_review", label: "Hire Review ⏳", color: "#f59e0b", icon: "🤝" },
    { key: "offer", label: "Offer", color: "#22c55e", icon: "📄" },
    { key: "completed", label: "Completed", color: "#10b981", icon: "✅" },
];

type Job = JobListItem;

function JobCard({ job, isLive, onUpload }: { job: Job; isLive: boolean; onUpload: (job: Job) => void }) {
    return (
        <div style={{ position: "relative", marginBottom: 12 }}>
            <Link href={`/audit?id=${job.job_id}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div
                    className="glass-card"
                    style={{
                        padding: "16px",
                        border: isLive ? "1px solid rgba(59,130,246,0.3)" : "1px solid rgba(255,255,255,0.05)",
                        background: isLive ? "rgba(59,130,246,0.05)" : "rgba(15, 23, 42, 0.6)",
                        boxShadow: isLive ? "0 0 20px rgba(59,130,246,0.1)" : "none",
                        overflow: "hidden"
                    }}
                >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                        <h4 style={{ fontWeight: 800, fontSize: "0.9rem", margin: 0, letterSpacing: "-0.3px" }}>{job.job_title}</h4>
                        {isLive && (
                            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                                <span style={{ fontSize: "0.6rem", color: "var(--accent-emerald)", fontWeight: 700, textTransform: "uppercase" }}>Live</span>
                                <span
                                    style={{
                                        width: 6, height: 6, borderRadius: "50%",
                                        background: "var(--accent-emerald)",
                                        display: "inline-block",
                                        animation: "pulse-glow 2s infinite",
                                    }}
                                />
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", margin: "0 0 12px", fontWeight: 500 }}>
                        {job.department}
                    </p>
                    <div style={{ display: "flex", gap: 12, alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.03)", paddingTop: 12 }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                            👥 <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>{job.candidates_count || 0}</span>
                        </span>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
                            📅 <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                                {job.created_at
                                    ? new Date(job.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
                                    : "—"}
                            </span>
                        </span>
                    </div>
                </div>
            </Link>
            {["sourcing", "screening"].includes(job.current_stage) && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onUpload(job);
                    }}
                    style={{
                        position: "absolute",
                        right: 8,
                        bottom: 48,
                        background: "var(--accent-blue)",
                        border: "none",
                        borderRadius: "50%",
                        width: 24, height: 24,
                        color: "white",
                        fontSize: "0.8rem",
                        cursor: "pointer",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        boxShadow: "0 4px 12px rgba(59, 130, 246, 0.4)",
                        transition: "all 0.2s"
                    }}
                    title="Upload Resume"
                    onMouseEnter={(e) => { e.currentTarget.style.transform = "scale(1.1)"; e.currentTarget.style.background = "var(--accent-cyan)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = "scale(1)"; e.currentTarget.style.background = "var(--accent-blue)"; }}
                >
                    +
                </button>
            )}
        </div>
    );
}

export default function KanbanPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeJobId, setActiveJobId] = useState<string | null>(null);
    const { connected, events, heartbeat } = useWebSocket(activeJobId);

    // Upload Modal State
    const [uploadingJob, setUploadingJob] = useState<Job | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const loadJobs = useCallback(async () => {
        try {
            const data = await api.listJobs();
            setJobs(data);
            if (data.length > 0 && !activeJobId) {
                setActiveJobId(data[0].job_id);
            }
        } catch { }
        setLoading(false);
    }, [activeJobId]);

    useEffect(() => {
        loadJobs();
        const interval = setInterval(loadJobs, 15000); // refresh every 15s
        return () => clearInterval(interval);
    }, [loadJobs]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !uploadingJob) return;

        if (!file.name.endsWith(".pdf")) {
            toast.error("Invalid file format", { description: "Please upload a PDF resume." });
            return;
        }

        setIsUploading(true);
        const promise = api.uploadResume(uploadingJob.job_id, file);

        toast.promise(promise, {
            loading: "Agent 3 is parsing resume...",
            success: () => {
                setUploadingJob(null);
                loadJobs();
                return `Resume parsed & candidate added!`;
            },
            error: (err) => {
                console.error(err);
                return `Upload failed: ${err.message}`;
            },
            finally: () => setIsUploading(false)
        });
    };

    // Group jobs by current_stage
    const boardMap: Record<string, Job[]> = {};
    for (const stage of STAGES) boardMap[stage.key] = [];
    for (const job of jobs) {
        const key = job.current_stage || "intake";
        if (!boardMap[key]) boardMap[key] = [];
        boardMap[key].push(job);
    }

    // Only show stages that have jobs or are key pipeline stages
    const visibleStages = STAGES.filter(
        (s) => boardMap[s.key]?.length > 0 ||
            ["jd_drafting", "sourcing", "screening", "outreach", "engagement", "interviewing", "offer", "completed"].includes(s.key)
    );

    return (
        <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: 0 }}>Pipeline Kanban</h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.9rem" }}>
                        Live view of all recruitment pipelines across 11 stages
                    </p>
                </div>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <span
                        style={{
                            fontSize: "0.8rem",
                            color: connected ? "var(--accent-emerald)" : "var(--text-muted)",
                            display: "flex", alignItems: "center", gap: 6,
                        }}
                    >
                        <span style={{
                            width: 7, height: 7, borderRadius: "50%",
                            background: connected ? "var(--accent-emerald)" : "var(--text-muted)",
                            display: "inline-block",
                        }} />
                        {connected ? "Live" : "Offline"}
                    </span>
                    <Link href="/jobs">
                        <button className="btn-primary" style={{ fontSize: "0.8rem", padding: "8px 16px" }}>
                            + New Job
                        </button>
                    </Link>
                </div>
            </div>

            {/* WebSocket Event Feed */}
            {events.length > 0 && (
                <div
                    className="glass-card"
                    style={{ padding: "12px 20px", marginBottom: 20, display: "flex", gap: 16, alignItems: "center", overflowX: "auto" }}
                >
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        Live events:
                    </span>
                    {events.slice(0, 4).map((evt, i) => (
                        <span key={i} className="badge badge-blue" style={{ whiteSpace: "nowrap", fontSize: "0.7rem" }}>
                            {evt.type === "stage_change"
                                ? `🔄 ${evt.data.previous_stage} → ${evt.data.current_stage}`
                                : evt.type === "candidates_found"
                                    ? `🔍 ${evt.data.count} candidates found`
                                    : evt.type}
                        </span>
                    ))}
                </div>
            )}

            {/* Heartbeat Banner */}
            {heartbeat && (
                <div className="glass-card" style={{ padding: "10px 20px", marginBottom: 20 }}>
                    <div style={{ display: "flex", gap: 32 }}>
                        {[
                            { label: "Stage", value: heartbeat.current_stage?.replace(/_/g, " ") },
                            { label: "Candidates", value: heartbeat.candidates },
                            { label: "Scored", value: heartbeat.scored },
                            { label: "Interviews", value: heartbeat.interviews },
                        ].map((item) => (
                            <div key={item.label}>
                                <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", margin: 0, textTransform: "uppercase" }}>
                                    {item.label}
                                </p>
                                <p style={{ fontSize: "0.95rem", fontWeight: 700, margin: "2px 0 0", color: "var(--accent-blue)" }}>
                                    {item.value ?? "—"}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {loading ? (
                <div style={{ display: "flex", gap: 20, overflowX: "auto", paddingBottom: 20 }}>
                    {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} style={{ minWidth: 220, opacity: 1 - i * 0.15 }}>
                            <div className="skeleton" style={{ height: 40, marginBottom: 16, borderRadius: 10 }} />
                            <div className="skeleton" style={{ height: 100, marginBottom: 12 }} />
                            <div className="skeleton" style={{ height: 100, marginBottom: 12 }} />
                        </div>
                    ))}
                </div>
            ) : jobs.length === 0 ? (
                <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                    <p style={{ fontSize: "3rem", margin: "0 0 16px" }}>🚀</p>
                    <h2 style={{ margin: "0 0 8px" }}>No pipelines yet</h2>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: 20 }}>
                        Create your first job requisition to start the recruitment pipeline.
                    </p>
                    <Link href="/jobs">
                        <button className="btn-primary">+ Create First Job</button>
                    </Link>
                </div>
            ) : (
                /* Kanban Board */
                <div
                    style={{
                        display: "flex",
                        gap: 16,
                        overflowX: "auto",
                        paddingBottom: 16,
                        alignItems: "flex-start",
                    }}
                >
                    {visibleStages.map((stage) => {
                        const stageJobs = boardMap[stage.key] || [];
                        const isHITL = stage.key.includes("review");
                        return (
                            <div
                                key={stage.key}
                                style={{
                                    minWidth: 220,
                                    maxWidth: 240,
                                    flexShrink: 0,
                                }}
                            >
                                {/* Column header */}
                                <div
                                    style={{
                                        padding: "10px 14px",
                                        borderRadius: 10,
                                        marginBottom: 12,
                                        border: `1px solid ${stage.color}30`,
                                        background: `${stage.color}10`,
                                        display: "flex",
                                        justifyContent: "space-between",
                                        alignItems: "center",
                                    }}
                                >
                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                        <span style={{ fontSize: "1rem" }}>{stage.icon}</span>
                                        <span style={{ fontSize: "0.8rem", fontWeight: 700, color: stage.color }}>
                                            {stage.label}
                                        </span>
                                    </div>
                                    {stageJobs.length > 0 && (
                                        <span
                                            style={{
                                                background: stage.color,
                                                color: "white",
                                                borderRadius: "50%",
                                                width: 20, height: 20,
                                                display: "flex", alignItems: "center", justifyContent: "center",
                                                fontSize: "0.7rem", fontWeight: 700,
                                            }}
                                        >
                                            {stageJobs.length}
                                        </span>
                                    )}
                                </div>

                                {/* Job Cards Column */}
                                <div
                                    style={{
                                        minHeight: 80,
                                        padding: "4px 0",
                                        borderRadius: 10,
                                        border: isHITL && stageJobs.length > 0 ? "1px dashed var(--accent-amber)" : "1px dashed transparent",
                                    }}
                                >
                                    {stageJobs.length === 0 ? (
                                        <div
                                            style={{
                                                padding: 16,
                                                textAlign: "center",
                                                color: "var(--text-muted)",
                                                fontSize: "0.75rem",
                                                borderRadius: 10,
                                            }}
                                        >
                                            Empty
                                        </div>
                                    ) : (
                                        stageJobs.map((job) => (
                                            <JobCard
                                                key={job.job_id}
                                                job={job}
                                                isLive={connected && job.job_id === activeJobId}
                                                onUpload={(j) => setUploadingJob(j)}
                                            />
                                        ))
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Upload Modal */}
            {uploadingJob && (
                <div style={{
                    position: "fixed",
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: "rgba(0,0,0,0.7)",
                    backdropFilter: "blur(8px)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    zIndex: 1000,
                    padding: 20
                }}>
                    <div className="glass-card fade-in" style={{ padding: 40, maxWidth: 500, width: "100%", textAlign: "center" }}>
                        <h2 style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: 8 }}>Upload Resume</h2>
                        <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: "0.9rem" }}>
                            Manually add a candidate to the <strong>{uploadingJob.job_title}</strong> pipeline.
                        </p>

                        <div
                            style={{
                                border: "2px dashed var(--border-glass)",
                                borderRadius: 12,
                                padding: 40,
                                cursor: "pointer",
                                transition: "all 0.2s ease"
                            }}
                            onClick={() => !isUploading && fileInputRef.current?.click()}
                            onMouseEnter={(e) => e.currentTarget.style.borderColor = "var(--accent-blue)"}
                            onMouseLeave={(e) => e.currentTarget.style.borderColor = "var(--border-glass)"}
                        >
                            {isUploading ? (
                                <AgentThinking message="Agent Parser is reading..." />
                            ) : (
                                <>
                                    <p style={{ fontSize: "2rem", margin: 0 }}>📄</p>
                                    <p style={{ marginTop: 12, fontWeight: 600 }}>Click to select PDF</p>
                                    <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>Candidate details will be auto-extracted</p>
                                </>
                            )}
                        </div>

                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: "none" }}
                            accept=".pdf"
                            title="Upload resume PDF"
                            onChange={handleFileUpload}
                            disabled={isUploading}
                        />

                        <button
                            className="btn-outline"
                            style={{ marginTop: 24, width: "100%" }}
                            onClick={() => setUploadingJob(null)}
                            disabled={isUploading}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {/* Active Job Selector for WebSocket */}
            {jobs.length > 0 && (
                <div style={{ marginTop: 24 }}>
                    <div className="glass-card" style={{ padding: "16px 20px" }}>
                        <label style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "block", marginBottom: 8 }}>
                            Monitor Pipeline (WebSocket)
                        </label>
                        <select
                            className="input"
                            title="Select monitored pipeline"
                            value={activeJobId || ""}
                            onChange={(e) => setActiveJobId(e.target.value)}
                            style={{ maxWidth: 360 }}
                        >
                            <option value="">Select a pipeline to monitor...</option>
                            {jobs.map((j) => (
                                <option key={j.job_id} value={j.job_id}>
                                    {j.job_title} — {j.current_stage}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
}
