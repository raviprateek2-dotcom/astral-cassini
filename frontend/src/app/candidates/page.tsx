"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { CandidateTable } from "@/components/CandidateTable";
import { CandidateModal } from "@/components/CandidateModal";
import { Search } from "lucide-react";

interface Job {
    job_id: string;
    job_title: string;
    department: string;
    current_stage: string;
}

export default function CandidatesPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [selectedJobId, setSelectedJobId] = useState<string>("");
    const [candidates, setCandidates] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);

    useEffect(() => {
        api.listJobs()
            .then(setJobs)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    async function handleJobSelect(jobId: string) {
        setSelectedJobId(jobId);
        if (!jobId) {
            setCandidates([]);
            return;
        }
        
        setLoading(true);
        try {
            const data = await api.getCandidates(jobId);
            // Harmonize candidate list from potential backend variations
            const list = [
                ...(data.scored_candidates || []),
                ...(data.candidates || []),
                ...(data.final_recommendations || [])
            ];
            
            // Deduplicate by ID if necessary
            const unique = Array.from(new Map(list.map(c => [c.candidate_id || c.id, c])).values());
            setCandidates(unique);
        } catch (err) {
            console.error("Failed to load candidates", err);
            setCandidates([]);
        } finally {
            setLoading(false);
        }
    }

    const selectedJob = jobs.find(j => j.job_id === selectedJobId);

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 32 }}>
                <h1 style={{ fontSize: "2.5rem", fontWeight: 900, margin: 0, letterSpacing: "-1px" }}>Pipeline Intelligence</h1>
                <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", marginTop: 4 }}>
                    Aggregated candidate analytics across all active neural pipelines.
                </p>
            </div>

            {/* Filter Bar */}
            <div className="glass-card" style={{ padding: "24px", marginBottom: "32px", display: "flex", gap: "24px", alignItems: "flex-end" }}>
                <div style={{ flex: 1 }}>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Active Neural Pipeline</label>
                    <select
                        className="input"
                        value={selectedJobId}
                        onChange={(e) => handleJobSelect(e.target.value)}
                        style={{ height: "45px" }}
                    >
                        <option value="">Select a specific pipeline to analyze...</option>
                        {jobs.map((j) => (
                            <option key={j.job_id} value={j.job_id}>
                                {j.job_title} — {j.department} ({j.current_stage})
                            </option>
                        ))}
                    </select>
                </div>
                
                <div style={{ flex: 1 }}>
                    <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Quick Search</label>
                    <div style={{ position: "relative" }}>
                        <Search size={18} style={{ position: "absolute", left: 14, top: 13, color: "var(--text-muted)" }} />
                        <input className="input" placeholder="Global search disabled in summary view..." disabled style={{ paddingLeft: 44, height: "45px", opacity: 0.5 }} />
                    </div>
                </div>
            </div>

            {loading && selectedJobId && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "100px 0" }}>
                    <div className="spinner" style={{ width: 40, height: 40, marginBottom: 16 }} />
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Querying Vector Database...</p>
                </div>
            )}

            {!loading && selectedJobId && (
                <div className="stagger-1">
                    {candidates.length > 0 ? (
                        <>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                                <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
                                    {selectedJob?.job_title} Results
                                </h3>
                                <span className="badge badge-blue">{candidates.length} Profiles Found</span>
                            </div>
                            <CandidateTable 
                                candidates={candidates} 
                                onRowClick={setSelectedCandidate} 
                                stage={selectedJob?.current_stage || ""}
                            />
                        </>
                    ) : (
                        <div className="glass-card" style={{ padding: 80, textAlign: "center", opacity: 0.7 }}>
                            <p style={{ fontSize: "2.5rem", margin: "0 0 16px" }}>🔍</p>
                            <p style={{ fontSize: "1.1rem" }}>This pipeline hasn't generated candidate data yet.</p>
                            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Agent 3 (Scout) needs to finalize the RAG retrieval phase.</p>
                        </div>
                    )}
                </div>
            )}

            {!selectedJobId && !loading && (
                <div className="glass-card stagger-1" style={{ padding: "100px 40px", textAlign: "center", background: "rgba(15, 23, 42, 0.4)" }}>
                    <div style={{ fontSize: "3rem", marginBottom: 20 }}>🧬</div>
                    <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 12 }}>Select a Pipeline to Begin Analytics</h2>
                    <p style={{ color: "var(--text-muted)", maxWidth: "500px", margin: "0 auto", lineHeight: 1.6 }}>
                        Choose an active recruitment requisition from the selector above to view deterministic scores, gap analysis, and system reasoning for each candidate.
                    </p>
                </div>
            )}

            {selectedCandidate && (
                <CandidateModal 
                    candidate={selectedCandidate} 
                    onClose={() => setSelectedCandidate(null)} 
                />
            )}
        </div>
    );
}
