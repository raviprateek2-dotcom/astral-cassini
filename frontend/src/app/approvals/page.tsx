"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import JDEditor from "@/components/JDEditor";
import {
    auditLogEntriesFromUnknown,
    type JobDetail,
    type JobListItem,
    type WorkflowBlob,
} from "@/types/domain";

const stageLabels: Record<string, string> = {
    jd_review: "Job Description Review",
    shortlist_review: "Candidate Shortlist Review",
    hire_review: "Hire Decision Review",
};

export default function ApprovalsPage() {
    const [jobs, setJobs] = useState<JobListItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<Record<string, string>>({});
    const [details, setDetails] = useState<Record<string, JobDetail>>({});
    const [editedJDs, setEditedJDs] = useState<Record<string, string>>({});

    const loadJobs = async () => {
        try {
            const all = await api.listJobs();
            const pending = all.filter((j: JobListItem) =>
                ["jd_review", "shortlist_review", "hire_review"].includes(j.current_stage)
            );
            setJobs(pending);

            // Load details for each pending job
            for (const job of pending) {
                try {
                    const detail = await api.getJob(job.job_id);
                    setDetails((prev) => ({ ...prev, [job.job_id]: detail }));
                } catch { }
            }
        } catch { }
        setLoading(false);
    };

    useEffect(() => {
        let isMounted = true;
        const init = async () => {
            if (isMounted) await loadJobs();
        };
        init();
        return () => { isMounted = false; };
    }, []);

    async function handleApprove(jobId: string) {
        setActionLoading(jobId);
        try {
            await api.approveStage(jobId, feedback[jobId] || "", editedJDs[jobId]);
            await loadJobs();
        } catch { }
        setActionLoading(null);
    }

    async function handleReject(jobId: string) {
        if (!feedback[jobId]) {
            alert("Please provide feedback for rejection.");
            return;
        }
        setActionLoading(jobId);
        try {
            await api.rejectStage(jobId, feedback[jobId]);
            await loadJobs();
        } catch { }
        setActionLoading(null);
    }

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Approval Gates</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Human-in-the-loop checkpoints managed by Agent 2 (The Liaison)
            </p>

            {loading ? (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
                    <div className="spinner" />
                </div>
            ) : jobs.length === 0 ? (
                <div className="glass-card" style={{ padding: 60, textAlign: "center" }}>
                    <p style={{ fontSize: "3rem", margin: "0 0 12px" }}>✅</p>
                    <h2 style={{ fontSize: "1.2rem", margin: "0 0 8px" }}>All Clear!</h2>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
                        No pending approvals. All pipelines are progressing autonomously.
                    </p>
                </div>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    {jobs.map((job) => {
                        const rawState = details[job.job_id]?.state;
                        const detail: WorkflowBlob =
                            rawState && typeof rawState === "object" && !Array.isArray(rawState)
                                ? (rawState as WorkflowBlob)
                                : {};
                        const jobDescription =
                            typeof detail.job_description === "string" ? detail.job_description : "";
                        const scoredCandidates = Array.isArray(detail.scored_candidates)
                            ? detail.scored_candidates
                            : [];
                        const finalRecommendations = Array.isArray(detail.final_recommendations)
                            ? detail.final_recommendations
                            : [];
                        const topAuditLog = auditLogEntriesFromUnknown(
                            details[job.job_id]?.audit_log
                        );

                        return (
                            <div key={job.job_id} className="glass-card fade-in" style={{ padding: 28 }}>
                                {/* Header */}
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
                                    <div>
                                        <span className="badge badge-amber" style={{ marginBottom: 8, display: "inline-block" }}>
                                            {stageLabels[job.current_stage] || job.current_stage}
                                        </span>
                                        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "8px 0 0" }}>
                                            {job.job_title}
                                        </h2>
                                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "4px 0 0" }}>
                                            {job.department} • ID: {job.job_id}
                                        </p>
                                    </div>
                                    <span className="pulse-active" style={{
                                        display: "inline-block",
                                        width: 10,
                                        height: 10,
                                        borderRadius: "50%",
                                        background: "var(--accent-amber)",
                                    }} />
                                </div>

                                {/* Content to Approve */}
                                {job.current_stage === "jd_review" && jobDescription.length > 0 && (
                                    <div style={{ marginBottom: 24 }}>
                                        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-blue)", margin: "0 0 10px" }}>
                                            📝 Review & Refine JD
                                        </h3>
                                        <JDEditor 
                                            initialValue={jobDescription} 
                                            onChange={(val) => setEditedJDs(prev => ({ ...prev, [job.job_id]: val }))} 
                                        />
                                    </div>
                                )}

                                {job.current_stage === "shortlist_review" && scoredCandidates.length > 0 && (
                                    <div style={{ marginBottom: 20 }}>
                                        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-blue)", margin: "0 0 10px" }}>
                                            📊 Candidate Shortlist
                                        </h3>
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Candidate</th>
                                                    <th>Score</th>
                                                    <th>Strengths</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {scoredCandidates.map((raw, i) => {
                                                    const c = raw as Record<string, unknown>;
                                                    const name = typeof c.candidate_name === "string" ? c.candidate_name : "";
                                                    const score = Number(c.overall_score ?? 0);
                                                    const strengths = Array.isArray(c.strengths)
                                                        ? c.strengths.filter((s): s is string => typeof s === "string")
                                                        : [];
                                                    return (
                                                    <tr key={i}>
                                                        <td style={{ fontWeight: 600 }}>{name}</td>
                                                        <td>
                                                            <span style={{
                                                                fontWeight: 700,
                                                                color: score >= 80 ? "var(--accent-emerald)" : score >= 60 ? "var(--accent-amber)" : "var(--accent-rose)",
                                                            }}>
                                                                {Math.round(score)}/100
                                                            </span>
                                                        </td>
                                                        <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                                            {strengths.join(", ")}
                                                        </td>
                                                    </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}

                                {job.current_stage === "hire_review" && finalRecommendations.length > 0 && (
                                    <div style={{ marginBottom: 20 }}>
                                        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-blue)", margin: "0 0 10px" }}>
                                            ⚖️ Final Recommendations
                                        </h3>
                                        {finalRecommendations.map((raw, i) => {
                                            const r = raw as Record<string, unknown>;
                                            const name = typeof r.candidate_name === "string" ? r.candidate_name : "";
                                            const reasoning = typeof r.reasoning === "string" ? r.reasoning : "";
                                            const decision = typeof r.decision === "string" ? r.decision : "";
                                            const confidence = Number(r.confidence ?? 0);
                                            return (
                                            <div key={i} style={{
                                                padding: 16,
                                                borderRadius: 10,
                                                border: "1px solid var(--border-glass)",
                                                marginBottom: 8,
                                                display: "flex",
                                                justifyContent: "space-between",
                                                alignItems: "center",
                                            }}>
                                                <div>
                                                    <p style={{ fontWeight: 600, margin: 0 }}>{name}</p>
                                                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                                                        {reasoning.slice(0, 100)}...
                                                    </p>
                                                </div>
                                                <span className={`badge ${decision === "hire" ? "badge-emerald" :
                                                        decision === "maybe" ? "badge-amber" : "badge-rose"
                                                    }`}>
                                                    {decision.toUpperCase()} ({Math.round(confidence)}%)
                                                </span>
                                            </div>
                                            );
                                        })}
                                    </div>
                                )}

                                {/* Governance & ROI Section */}
                                <div style={{ 
                                    padding: 16, 
                                    borderRadius: 12, 
                                    background: "rgba(16, 185, 129, 0.05)", 
                                    border: "1px dashed rgba(16, 185, 129, 0.3)",
                                    marginBottom: 20 
                                }}>
                                    <h4 style={{ margin: "0 0 8px", fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-emerald)", display: "flex", alignItems: "center", gap: 6 }}>
                                        🛡️ Governance Audit Trail
                                    </h4>
                                    {topAuditLog
                                        .filter((l) => l.action === "bias_audit")
                                        .map((l, i) => (
                                            <div key={i} style={{ fontSize: "0.75rem", color: "var(--text-secondary)", display: "flex", gap: 8 }}>
                                                <span style={{ color: "var(--accent-emerald)" }}>•</span>
                                                <span>{l.details}</span>
                                            </div>
                                        ))}
                                    {!topAuditLog.some((l) => l.action === "bias_audit") && (
                                        <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>
                                            Waiting for agent compliance verification...
                                        </p>
                                    )}
                                </div>

                                {/* Feedback + Actions */}
                                <div>
                                    <textarea
                                        className="input"
                                        placeholder="Add feedback (required for rejection)..."
                                        value={feedback[job.job_id] || ""}
                                        onChange={(e) => setFeedback((f) => ({ ...f, [job.job_id]: e.target.value }))}
                                        style={{ marginBottom: 12, minHeight: 60 }}
                                    />
                                    <div style={{ display: "flex", gap: 12 }}>
                                        <button
                                            className="btn-success"
                                            onClick={() => handleApprove(job.job_id)}
                                            disabled={actionLoading === job.job_id}
                                        >
                                            {actionLoading === job.job_id ? "Processing..." : "✅ Approve & Continue"}
                                        </button>
                                        <button
                                            className="btn-danger"
                                            onClick={() => handleReject(job.job_id)}
                                            disabled={actionLoading === job.job_id}
                                        >
                                            ✕ Reject & Revise
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
