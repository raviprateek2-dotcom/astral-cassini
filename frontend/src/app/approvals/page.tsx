"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

const stageLabels: Record<string, string> = {
    jd_review: "Job Description Review",
    shortlist_review: "Candidate Shortlist Review",
    hire_review: "Hire Decision Review",
};

export default function ApprovalsPage() {
    const [jobs, setJobs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<Record<string, string>>({});
    const [details, setDetails] = useState<Record<string, any>>({});

    useEffect(() => {
        loadJobs();
    }, []);

    async function loadJobs() {
        try {
            const all = await api.listJobs();
            const pending = all.filter((j: any) =>
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
    }

    async function handleApprove(jobId: string) {
        setActionLoading(jobId);
        try {
            await api.approveStage(jobId, feedback[jobId] || "");
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
                        const detail = details[job.job_id]?.state || {};
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
                                {job.current_stage === "jd_review" && detail.job_description && (
                                    <div style={{ marginBottom: 20 }}>
                                        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-blue)", margin: "0 0 10px" }}>
                                            📝 Generated Job Description
                                        </h3>
                                        <div
                                            style={{
                                                padding: 20,
                                                borderRadius: 12,
                                                border: "1px solid var(--border-glass)",
                                                background: "rgba(15, 23, 42, 0.6)",
                                                fontSize: "0.85rem",
                                                lineHeight: 1.7,
                                                whiteSpace: "pre-wrap",
                                                maxHeight: 400,
                                                overflowY: "auto",
                                            }}
                                        >
                                            {detail.job_description}
                                        </div>
                                    </div>
                                )}

                                {job.current_stage === "shortlist_review" && (detail.scored_candidates || []).length > 0 && (
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
                                                {detail.scored_candidates.map((c: any, i: number) => (
                                                    <tr key={i}>
                                                        <td style={{ fontWeight: 600 }}>{c.candidate_name}</td>
                                                        <td>
                                                            <span style={{
                                                                fontWeight: 700,
                                                                color: c.overall_score >= 80 ? "var(--accent-emerald)" : c.overall_score >= 60 ? "var(--accent-amber)" : "var(--accent-rose)",
                                                            }}>
                                                                {Math.round(c.overall_score)}/100
                                                            </span>
                                                        </td>
                                                        <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                                            {(c.strengths || []).join(", ")}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}

                                {job.current_stage === "hire_review" && (detail.final_recommendations || []).length > 0 && (
                                    <div style={{ marginBottom: 20 }}>
                                        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--accent-blue)", margin: "0 0 10px" }}>
                                            ⚖️ Final Recommendations
                                        </h3>
                                        {detail.final_recommendations.map((r: any, i: number) => (
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
                                                    <p style={{ fontWeight: 600, margin: 0 }}>{r.candidate_name}</p>
                                                    <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0" }}>
                                                        {r.reasoning?.slice(0, 100)}...
                                                    </p>
                                                </div>
                                                <span className={`badge ${r.decision === "hire" ? "badge-emerald" :
                                                        r.decision === "maybe" ? "badge-amber" : "badge-rose"
                                                    }`}>
                                                    {r.decision.toUpperCase()} ({Math.round(r.confidence)}%)
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}

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
