"use client";

import { Suspense, useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { CreateJobPayload, api } from "@/lib/api";
import { useJobStore } from "@/store/useJobStore";
import {
    auditLogEntriesFromUnknown,
    type AuditLogEntry,
    type CandidateLike,
    type WorkflowBlob,
} from "@/types/domain";
import { useWebSocket } from "@/hooks/useWebSocket";
import { toast } from "sonner";
import { AgentThinking } from "@/components/AgentThinking";
import { PipelineSteps } from "@/components/PipelineSteps";
import { CandidateTable } from "@/components/CandidateTable";
import { CandidateModal } from "@/components/CandidateModal";
import { AuditTimeline } from "@/components/AuditTimeline";
import { ControlPanel } from "@/components/ControlPanel";
import { CardSkeleton, TableSkeleton } from "@/components/Skeleton";
import JDEditor from "@/components/JDEditor";
import { ChevronLeft, Plus, Send, CheckCircle, XCircle } from "lucide-react";

function candidateListFromState(value: unknown): CandidateLike[] {
    if (!Array.isArray(value)) return [];
    return value as CandidateLike[];
}

function auditLogForJob(
    job: { audit_log?: AuditLogEntry[]; state?: WorkflowBlob } | null
): AuditLogEntry[] {
    if (!job) return [];
    if (Array.isArray(job.audit_log)) return job.audit_log;
    return auditLogEntriesFromUnknown(job.state?.audit_log);
}

function JobsPageContent() {
    const { 
        currentJob, 
        jobsList, 
        loading: storeLoading, 
        fetchJobsList, 
        fetchJobDetails, 
        setCurrentJob,
        approveStage,
        rejectStage
    } = useJobStore();
    
    const searchParams = useSearchParams();
    const jobIdParam = searchParams.get("id");

    const [showForm, setShowForm] = useState(false);
    const [creationLoading, setCreationLoading] = useState(false);
    const [selectedCandidate, setSelectedCandidate] = useState<CandidateLike | null>(null);
    const [jdDraft, setJdDraft] = useState("");

    // Form Local State
    const [form, setForm] = useState<CreateJobPayload>({
        job_title: "",
        department: "",
        requirements: [],
        preferred_qualifications: [],
        location: "Remote",
        salary_range: "",
    });
    const [reqInput, setReqInput] = useState("");

    // WebSocket hook integrates with the store
    const { connected, tokenStream } = useWebSocket(currentJob?.job_id || null);

    useEffect(() => {
        fetchJobsList();
        if (jobIdParam) {
            fetchJobDetails(jobIdParam);
        }
    }, [fetchJobsList, fetchJobDetails, jobIdParam]);

    useEffect(() => {
        const maybeDraft = currentJob?.state?.job_description;
        if (typeof maybeDraft === "string" && maybeDraft.length > 0) {
            setJdDraft(maybeDraft);
        }
    }, [currentJob?.state?.job_description]);

    const handleCreateJob = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreationLoading(true);
        try {
            const data = await api.createJob(form);
            setShowForm(false);
            toast.success("Job Requisition Initialized", {
                description: "Deterministic pipeline has been triggered."
            });
            await fetchJobDetails(data.job_id);
            fetchJobsList();
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : "Unknown error";
            toast.error("Initialization Failed", { description: message });
        } finally {
            setCreationLoading(false);
        }
    };

    const addListItem = (input: string, setInput: React.Dispatch<React.SetStateAction<string>>, list: string[], setList: (newList: string[]) => void) => {
        if (input.trim()) {
            setList([...list, input.trim()]);
            setInput("");
        }
    };

    if (currentJob) {
        const stage = currentJob.current_stage;
        const isJDReview = stage === "jd_review" || stage === "jd_drafting";
        const hasCandidates = ["screening", "shortlist_review", "interviewing", "decision", "hire_review", "completed"].includes(stage);
        
        const displayJD = tokenStream || jdDraft || "Agent Architect is finalizing the draft...";

        return (
            <div className="fade-in">
                {/* Dashboard Sub-Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                    <button 
                        className="btn-outline" 
                        onClick={() => setCurrentJob(null)}
                        style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 16px" }}
                    >
                        <ChevronLeft size={16} /> Back to List
                    </button>
                    
                    <div style={{ textAlign: "right" }}>
                        <h1 style={{ fontSize: "1.5rem", fontWeight: 800, margin: 0 }}>{currentJob.job_title}</h1>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", margin: 0 }}>
                            {currentJob.department} • {connected ? "🟢 Linked to Vector Node" : "🔴 Reconnecting..."}
                        </p>
                    </div>
                </div>

                {/* Core Pipeline Tracker */}
                <PipelineSteps currentStage={stage} />

                {/* Control Panel */}
                <ControlPanel />

                <div style={{ display: "grid", gridTemplateColumns: "1fr 350px", gap: "24px", alignItems: "start" }}>
                    
                    {/* Main Workspace */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                        
                        {/* JD Editor Workspace (When in review or drafting) */}
                        {isJDReview && (
                            <div className="glass-card stagger-1" style={{ padding: "32px" }}>
                                <div style={{ marginBottom: 24 }}>
                                    <h2 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "0 0 8px" }}>Job Description Architecture</h2>
                                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: 0 }}>
                                        Review and refine the draft generated by Agent 1. Approval triggers Agent 3 (The Scout).
                                    </p>
                                </div>

                                <JDEditor initialValue={displayJD} onChange={setJdDraft} />

                                {stage === "jd_review" && (
                                    <div style={{ marginTop: 24, display: "flex", gap: 12, justifyContent: "flex-end", borderTop: "1px solid var(--border-glass)", paddingTop: 24 }}>
                                        <button 
                                            className="btn-outline" 
                                            onClick={() => rejectStage("The JD needs more technical depth in section 2.")}
                                            style={{ borderColor: "var(--accent-rose)", color: "var(--accent-rose)", display: "flex", alignItems: "center", gap: 8 }}
                                        >
                                            <XCircle size={18} /> Request Revision
                                        </button>
                                        <button 
                                            className="btn-primary" 
                                            onClick={() => approveStage("JD looks perfect, proceed to sourcing.", jdDraft)}
                                            style={{ display: "flex", alignItems: "center", gap: 8 }}
                                        >
                                            <CheckCircle size={18} /> Approve & Source
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Candidate Workspace */}
                        {hasCandidates && (
                            <div className="stagger-1">
                                {storeLoading ? (
                                    <TableSkeleton rows={8} />
                                ) : (
                                    <>
                                        <CandidateTable
                                            candidates={
                                                stage === "hire_review" || stage === "completed"
                                                    ? candidateListFromState(currentJob.state.final_recommendations)
                                                    : stage === "shortlist_review" || stage === "interviewing" || stage === "decision"
                                                        ? candidateListFromState(currentJob.state.scored_candidates)
                                                        : candidateListFromState(currentJob.state.candidates)
                                            }
                                            onRowClick={setSelectedCandidate}
                                            stage={stage}
                                        />
                                        
                                        {stage === "shortlist_review" && (
                                            <div className="glass-card" style={{ marginTop: 24, padding: 24, display: "flex", justifyContent: "space-between", alignItems: "center", border: "1px solid var(--accent-amber)30" }}>
                                                <div style={{ maxWidth: "60%" }}>
                                                    <h4 style={{ margin: "0 0 4px", fontSize: "1rem" }}>Shortlist Approval Required</h4>
                                                    <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                                                        Verify the deterministic scores above. Approval will trigger Agent 5 (Coordinator) to schedule interviews.
                                                    </p>
                                                </div>
                                                <div style={{ display: "flex", gap: 12 }}>
                                                    <button className="btn-outline" onClick={() => rejectStage("Please find candidates with more specific AWS experience.")}>Refine Search</button>
                                                    <button className="btn-primary" onClick={() => approveStage("Shortlist approved.")}>Confirm & Schedule</button>
                                                </div>
                                            </div>
                                        )}

                                        {stage === "hire_review" && (
                                            <div className="glass-card" style={{ marginTop: 24, padding: 24, display: "flex", justifyContent: "space-between", alignItems: "center", border: "1px solid var(--accent-emerald)30" }}>
                                                <div>
                                                    <h4 style={{ margin: "0 0 4px", fontSize: "1rem" }}>Final Hiring Decision</h4>
                                                    <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                                                        Agent Decider has provided weighted recommendations. Select &apos;Approve&apos; to generate the offer letter.
                                                    </p>
                                                </div>
                                                <button className="btn-primary" onClick={() => approveStage("Hiring decision confirmed.")}>Finalize Selection</button>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Right Sidebar: Logs Panel */}
                    <div style={{ position: "sticky", top: "24px", height: "calc(100vh - 150px)" }}>
                        <AuditTimeline logs={auditLogForJob(currentJob)} />
                    </div>
                </div>

                {selectedCandidate && (
                    <CandidateModal 
                        candidate={selectedCandidate} 
                        onClose={() => setSelectedCandidate(null)} 
                    />
                )}
            </div>
        );
    }

    return (
        <div className="fade-in">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
                <div>
                    <h1 style={{ fontSize: "2.5rem", fontWeight: 900, margin: 0, letterSpacing: "-1.5px" }}>Intelligence Hub</h1>
                    <p style={{ color: "var(--text-secondary)", marginTop: 6, fontSize: "1rem" }}>
                        Manage your autonomous multi-agent recruitment pipelines
                    </p>
                </div>
                <button 
                    className="btn-primary" 
                    onClick={() => setShowForm(!showForm)}
                    style={{ padding: "14px 28px", borderRadius: "12px", display: "flex", alignItems: "center", gap: 8 }}
                >
                    {showForm ? "✕ Close Form" : <><Plus size={20} /> New Position</>}
                </button>
            </div>

            {showForm && (
                <div className="glass-card fade-in stagger-1" style={{ padding: 40, marginBottom: 48, position: "relative", overflow: "hidden" }}>
                    <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 4, background: "var(--gradient-primary)" }} />
                    <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "0 0 32px" }}>Strategic Requisition Intake</h2>
                    
                    <form onSubmit={handleCreateJob}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
                            <div>
                                <label style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Role Title</label>
                                <input 
                                    className="input" 
                                    placeholder="e.g. Lead Artificial Intelligence Engineer"
                                    value={form.job_title}
                                    onChange={e => setForm({...form, job_title: e.target.value})}
                                    required
                                />
                            </div>
                            <div>
                                <label style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Department</label>
                                <input 
                                    className="input" 
                                    placeholder="e.g. Core Research Lab"
                                    value={form.department}
                                    onChange={e => setForm({...form, department: e.target.value})}
                                    required
                                />
                            </div>
                        </div>

                        <div style={{ marginBottom: 32 }}>
                            <label style={{ fontSize: "0.85rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Core Technical Requirements</label>
                            <div style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                                <input 
                                    className="input" 
                                    placeholder="Add skill (e.g. PyTorch, Kubernetes...)" 
                                    value={reqInput}
                                    onChange={e => setReqInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addListItem(reqInput, setReqInput, form.requirements, (l) => setForm({...form, requirements: l})))}
                                />
                                <button type="button" className="btn-outline" onClick={() => addListItem(reqInput, setReqInput, form.requirements, (l) => setForm({...form, requirements: l}))}>Add</button>
                            </div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                                {form.requirements.map((r, i) => (
                                    <span key={i} className="badge badge-blue" style={{ padding: "6px 12px", borderRadius: "8px" }}>{r}</span>
                                ))}
                            </div>
                        </div>

                        <button className="btn-primary" type="submit" disabled={creationLoading} style={{ padding: "16px 40px", fontSize: "1.1rem" }}>
                            {creationLoading ? <AgentThinking message="Initializing Agent Protocol..." size="sm" /> : <><Send size={18} style={{ marginRight: 8 }} /> Bootstrap Autonomous Pipeline</>}
                        </button>
                    </form>
                </div>
            )}

            <div className="stagger-2">
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: 20 }}>Active Neural Pipelines</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: 20 }}>
                    {storeLoading ? (
                        Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)
                    ) : (
                        jobsList.map(job => (
                            <div 
                                key={job.job_id} 
                                className="glass-card shadow-hover" 
                                style={{ padding: 24, cursor: "pointer", border: "1px solid var(--border-glass)", transition: "all 0.3s ease" }}
                                onClick={() => fetchJobDetails(job.job_id)}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                                    <div>
                                        <h4 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>{job.job_title}</h4>
                                        <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "var(--text-muted)" }}>{job.department}</p>
                                    </div>
                                    <span className="badge badge-purple" style={{ textTransform: "uppercase", fontSize: "0.65rem", letterSpacing: "1px" }}>
                                        {job.current_stage}
                                    </span>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: 16, borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 16 }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 4 }}>Candidates</div>
                                        <div style={{ fontWeight: 700 }}>{job.candidates_count || 0}</div>
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: 4 }}>Last Activity</div>
                                                    <div style={{ fontWeight: 700 }}>
                                                        {job.created_at ? new Date(job.created_at).toLocaleDateString() : "-"}
                                                    </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                    {jobsList.length === 0 && !storeLoading && (
                        <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: 80, opacity: 0.5 }}>
                            <p>No neural pipelines detected. Start a new requisition to begin.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function JobsPage() {
    return (
        <Suspense fallback={<div className="spinner" style={{ margin: "100px auto" }} />}>
            <JobsPageContent />
        </Suspense>
    );
}
