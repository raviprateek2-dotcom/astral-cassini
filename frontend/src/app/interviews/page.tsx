"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function InterviewsPage() {
    const [jobs, setJobs] = useState<any[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.listJobs().then(setJobs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    async function loadInterviews(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const res = await api.getInterviews(jobId);
            setData(res);
        } catch { }
        setLoading(false);
    }

    const interviews = data?.scheduled_interviews || [];
    const assessments = data?.interview_assessments || [];
    const assessmentMap = Object.fromEntries(assessments.map((a: any) => [a.candidate_id, a]));

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Interview Management</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Agent 5 (Coordinator) schedules • Agent 6 (Interviewer) assesses
            </p>

            <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                <select
                    className="input"
                    value={selectedJob}
                    onChange={(e) => loadInterviews(e.target.value)}
                    style={{ maxWidth: 400 }}
                >
                    <option value="">Select pipeline...</option>
                    {jobs.map((j) => (
                        <option key={j.job_id} value={j.job_id}>{j.job_title} — {j.department}</option>
                    ))}
                </select>
            </div>

            {loading && selectedJob && (
                <div style={{ display: "flex", justifyContent: "center", padding: 60 }}><div className="spinner" /></div>
            )}

            {/* Scheduled Interviews */}
            {interviews.length > 0 && (
                <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>
                        📅 Scheduled Interviews ({interviews.length})
                    </h2>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Candidate</th>
                                <th>Type</th>
                                <th>Scheduled</th>
                                <th>Duration</th>
                                <th>Interviewers</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {interviews.map((int: any, i: number) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 600 }}>{int.candidate_name}</td>
                                    <td>
                                        <span className={`badge ${int.interview_type === "technical" ? "badge-blue" : "badge-purple"}`}>
                                            {int.interview_type}
                                        </span>
                                    </td>
                                    <td style={{ fontSize: "0.85rem" }}>
                                        {new Date(int.scheduled_time).toLocaleDateString("en-IN", {
                                            day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
                                        })}
                                    </td>
                                    <td>{int.duration_minutes}m</td>
                                    <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                        {(int.interviewers || []).join(", ")}
                                    </td>
                                    <td><span className="badge badge-emerald">{int.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Assessments */}
            {assessments.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>
                        🎙️ Interview Assessments
                    </h2>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {assessments.map((a: any, i: number) => (
                            <div key={i} style={{
                                padding: 20, borderRadius: 12, border: "1px solid var(--border-glass)",
                                background: "rgba(15, 23, 42, 0.4)",
                            }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                                    <h3 style={{ margin: 0, fontSize: "1rem" }}>{a.candidate_name}</h3>
                                    <span style={{
                                        fontSize: "1.5rem", fontWeight: 800,
                                        color: a.overall_score >= 8 ? "var(--accent-emerald)" : a.overall_score >= 6 ? "var(--accent-amber)" : "var(--accent-rose)",
                                    }}>
                                        {a.overall_score}/10
                                    </span>
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
                                    {[
                                        { label: "Technical", value: a.technical_score, color: "#3b82f6" },
                                        { label: "Communication", value: a.communication_score, color: "#8b5cf6" },
                                        { label: "Problem Solving", value: a.problem_solving_score, color: "#06b6d4" },
                                        { label: "Cultural Fit", value: a.cultural_fit_score, color: "#10b981" },
                                    ].map((dim) => (
                                        <div key={dim.label} style={{ textAlign: "center" }}>
                                            <div style={{
                                                width: 56, height: 56, borderRadius: "50%", margin: "0 auto 8px",
                                                display: "flex", alignItems: "center", justifyContent: "center",
                                                border: `3px solid ${dim.color}`,
                                                fontSize: "1rem", fontWeight: 700,
                                            }}>
                                                {dim.value}
                                            </div>
                                            <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>{dim.label}</p>
                                        </div>
                                    ))}
                                </div>

                                {a.key_observations?.length > 0 && (
                                    <div style={{ marginBottom: 8 }}>
                                        <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-emerald)", margin: "0 0 4px" }}>Key Observations</p>
                                        {a.key_observations.map((o: string, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>• {o}</p>
                                        ))}
                                    </div>
                                )}

                                {a.concerns?.length > 0 && (
                                    <div>
                                        <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-amber)", margin: "0 0 4px" }}>Concerns</p>
                                        {a.concerns.map((c: string, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>⚠ {c}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {selectedJob && !loading && interviews.length === 0 && (
                <div className="glass-card" style={{ padding: 40, textAlign: "center" }}>
                    <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>📅</p>
                    <p style={{ color: "var(--text-muted)" }}>No interviews scheduled yet for this pipeline.</p>
                </div>
            )}
        </div>
    );
}
