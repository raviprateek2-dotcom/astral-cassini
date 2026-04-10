"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type {
    AssessmentRow,
    InterviewsApiResponse,
    InterviewRow,
    JobListItem,
} from "@/types/domain";

export default function InterviewsPage() {
    const [jobs, setJobs] = useState<JobListItem[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [data, setData] = useState<InterviewsApiResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [jobStage, setJobStage] = useState("");
    const [inviteBusy, setInviteBusy] = useState(false);
    const [offerBusy, setOfferBusy] = useState(false);
    const [inviteForm, setInviteForm] = useState({
        candidate_id: "",
        candidate_name: "",
        to_email: "",
        meeting_link: "",
        interview_type: "technical",
        scheduled_time: "",
        duration_minutes: 60,
    });

    useEffect(() => {
        api.listJobs().then(setJobs).catch(() => { }).finally(() => setLoading(false));
    }, []);

    async function loadInterviews(jobId: string) {
        setSelectedJob(jobId);
        setLoading(true);
        try {
            const [res, job] = await Promise.all([api.getInterviews(jobId), api.getJob(jobId)]);
            setData(res);
            setJobStage(job.current_stage ?? "");
        } catch { }
        setLoading(false);
    }

    async function handleSendInvite() {
        if (!selectedJob) return;
        if (!inviteForm.candidate_name || !inviteForm.to_email || !inviteForm.meeting_link) {
            alert("Candidate name, email, and meeting link are required.");
            return;
        }
        setInviteBusy(true);
        try {
            await api.sendInterviewInvite(selectedJob, inviteForm);
            await loadInterviews(selectedJob);
            setInviteForm((p) => ({ ...p, candidate_id: "", candidate_name: "", to_email: "", meeting_link: "" }));
        } catch {
            alert("Failed to send interview invite.");
        }
        setInviteBusy(false);
    }

    async function handleInterviewDecision(int: InterviewRow, selected: boolean) {
        if (!selectedJob) return;
        const candidateId = String(int.candidate_id ?? int.candidate_name ?? "");
        const candidateName = String(int.candidate_name ?? "");
        if (!candidateId || !candidateName) {
            alert("Candidate details missing for this row.");
            return;
        }
        try {
            await api.completeInterview(selectedJob, {
                candidate_id: candidateId,
                candidate_name: candidateName,
                selected,
                technical_score: 8.0,
                communication_score: 8.0,
                problem_solving_score: 8.0,
                cultural_fit_score: 8.0,
                observations: selected ? ["Selected by HR after interview."] : ["Not selected by HR."],
                concerns: selected ? [] : ["Not selected"],
            });
            await loadInterviews(selectedJob);
        } catch {
            alert("Failed to save interview outcome.");
        }
    }

    async function handleGenerateOffer() {
        if (!selectedJob) return;
        setOfferBusy(true);
        try {
            await api.generateOffer(selectedJob);
            await loadInterviews(selectedJob);
            alert("Offer generation triggered.");
        } catch {
            alert("Offer generation failed. Ensure pipeline is at hire_review.");
        }
        setOfferBusy(false);
    }

    const interviews = data?.scheduled_interviews || [];
    const assessments = data?.interview_assessments || [];

    return (
        <div className="fade-in">
            <h1 style={{ fontSize: "2rem", fontWeight: 800, margin: "0 0 4px" }}>Interview Management</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: "0 0 32px" }}>
                Hiring Ops Coordinator (Agent 7) schedules interviews and records assessments
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

            {selectedJob && (
                <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                    <h2 style={{ fontSize: "1rem", margin: "0 0 12px" }}>HR Interview Control</h2>
                    <p style={{ margin: "0 0 12px", color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        Create meeting links and send to students. Pipeline moves ahead only after interview completion and selection.
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <input className="input" placeholder="Candidate ID (optional)" value={inviteForm.candidate_id} onChange={(e) => setInviteForm((p) => ({ ...p, candidate_id: e.target.value }))} />
                        <input className="input" placeholder="Candidate Name" value={inviteForm.candidate_name} onChange={(e) => setInviteForm((p) => ({ ...p, candidate_name: e.target.value }))} />
                        <input className="input" placeholder="Student Email" value={inviteForm.to_email} onChange={(e) => setInviteForm((p) => ({ ...p, to_email: e.target.value }))} />
                        <input className="input" placeholder="Meeting Link" value={inviteForm.meeting_link} onChange={(e) => setInviteForm((p) => ({ ...p, meeting_link: e.target.value }))} />
                        <input className="input" type="datetime-local" value={inviteForm.scheduled_time} onChange={(e) => setInviteForm((p) => ({ ...p, scheduled_time: e.target.value }))} />
                        <input className="input" type="number" min={15} value={inviteForm.duration_minutes} onChange={(e) => setInviteForm((p) => ({ ...p, duration_minutes: Number(e.target.value) }))} />
                    </div>
                    <div style={{ marginTop: 12, display: "flex", gap: 10 }}>
                        <button className="btn-primary" onClick={() => void handleSendInvite()} disabled={inviteBusy}>
                            {inviteBusy ? "Sending..." : "Send Meeting Link to Student"}
                        </button>
                        <span className="badge badge-blue">Stage: {jobStage || "unknown"}</span>
                    </div>
                </div>
            )}

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
                                <th>Meeting</th>
                                <th>Status</th>
                                <th>HR Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {interviews.map((int: InterviewRow, i: number) => (
                                <tr key={i}>
                                    <td style={{ fontWeight: 600 }}>{int.candidate_name}</td>
                                    <td>
                                        <span className={`badge ${int.interview_type === "technical" ? "badge-blue" : "badge-purple"}`}>
                                            {int.interview_type}
                                        </span>
                                    </td>
                                    <td style={{ fontSize: "0.85rem" }}>
                                        {int.scheduled_time
                                            ? new Date(String(int.scheduled_time)).toLocaleDateString("en-IN", {
                                            day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
                                            })
                                            : "—"}
                                    </td>
                                    <td>{int.duration_minutes}m</td>
                                    <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                        {(Array.isArray(int.interviewers)
                                            ? int.interviewers
                                            : []
                                        ).join(", ")}
                                    </td>
                                    <td style={{ fontSize: "0.8rem" }}>
                                        {typeof int.meeting_link === "string" && int.meeting_link ? (
                                            <a href={int.meeting_link} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent-cyan)" }}>
                                                Join
                                            </a>
                                        ) : (
                                            "—"
                                        )}
                                    </td>
                                    <td><span className="badge badge-emerald">{int.status}</span></td>
                                    <td>
                                        <div style={{ display: "flex", gap: 8 }}>
                                            <button className="btn-success" onClick={() => void handleInterviewDecision(int, true)}>Select</button>
                                            <button className="btn-danger" onClick={() => void handleInterviewDecision(int, false)}>Reject</button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {selectedJob && jobStage === "hire_review" && (
                <div className="glass-card" style={{ padding: 20, marginBottom: 24 }}>
                    <h2 style={{ marginTop: 0 }}>Offer Letter</h2>
                    <p style={{ color: "var(--text-muted)" }}>
                        HR can generate offer letter after selecting candidate(s) from interviews.
                    </p>
                    <button className="btn-success" onClick={() => void handleGenerateOffer()} disabled={offerBusy}>
                        {offerBusy ? "Generating..." : "Generate Offer Letter"}
                    </button>
                </div>
            )}

            {/* Assessments */}
            {assessments.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                    <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>
                        🎙️ Interview Assessments
                    </h2>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {assessments.map((a: AssessmentRow, i: number) => {
                            const overall = Number(a.overall_score ?? 0);
                            return (
                            <div key={i} style={{
                                padding: 20, borderRadius: 12, border: "1px solid var(--border-glass)",
                                background: "rgba(15, 23, 42, 0.4)",
                            }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                                    <h3 style={{ margin: 0, fontSize: "1rem" }}>{a.candidate_name}</h3>
                                    <span style={{
                                        fontSize: "1.5rem", fontWeight: 800,
                                        color: overall >= 8 ? "var(--accent-emerald)" : overall >= 6 ? "var(--accent-amber)" : "var(--accent-rose)",
                                    }}>
                                        {overall}/10
                                    </span>
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
                                    {[
                                        { label: "Technical", value: Number(a.technical_score), color: "#3b82f6" },
                                        { label: "Communication", value: Number(a.communication_score), color: "#8b5cf6" },
                                        { label: "Problem Solving", value: Number(a.problem_solving_score), color: "#06b6d4" },
                                        { label: "Cultural Fit", value: Number(a.cultural_fit_score), color: "#10b981" },
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

                                {Array.isArray(a.key_observations) && a.key_observations.length > 0 && (
                                    <div style={{ marginBottom: 8 }}>
                                        <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-emerald)", margin: "0 0 4px" }}>Key Observations</p>
                                        {a.key_observations.map((o: unknown, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>• {String(o)}</p>
                                        ))}
                                    </div>
                                )}

                                {Array.isArray(a.concerns) && a.concerns.length > 0 && (
                                    <div>
                                        <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--accent-amber)", margin: "0 0 4px" }}>Concerns</p>
                                        {a.concerns.map((c: unknown, j: number) => (
                                            <p key={j} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0" }}>⚠ {String(c)}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                        })}
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
