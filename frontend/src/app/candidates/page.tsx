"use client";

import { useState, useEffect, useMemo } from "react";
import { api } from "@/lib/api";
import { CandidateTable } from "@/components/CandidateTable";
import { CandidateModal } from "@/components/CandidateModal";
import { Search, Download } from "lucide-react";
import { EmptyState } from "@/components/EmptyState";
import { useRouter } from "next/navigation";
import type { CandidateLike, JobListItem } from "@/types/domain";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function CandidatesPage() {
    const [jobs, setJobs] = useState<JobListItem[]>([]);
    const [selectedJobId, setSelectedJobId] = useState<string>("");
    const [candidates, setCandidates] = useState<CandidateLike[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedCandidate, setSelectedCandidate] = useState<CandidateLike | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [minScore, setMinScore] = useState<number>(0);
    const router = useRouter();
    
    const { heartbeat } = useWebSocket(selectedJobId || null);

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

    const mergedCandidates = useMemo(() => {
        const list = [...candidates];
        if (heartbeat?.state) {
            const hState = heartbeat.state as any;
            if (hState.candidates) list.push(...hState.candidates);
            if (hState.scored_candidates) list.push(...hState.scored_candidates);
            if (hState.final_recommendations) list.push(...hState.final_recommendations);
        }
        const unique = Array.from(new Map(list.map(c => [c.candidate_id || c.id, c])).values());
        return unique;
    }, [candidates, heartbeat]);

    const filteredCandidates = useMemo(() => {
        return mergedCandidates.filter(c => {
            if (searchQuery) {
                const searchLower = searchQuery.toLowerCase();
                const name = String(c.name || c.candidate_name || "").toLowerCase();
                const email = String(c.email || "").toLowerCase();
                if (!name.includes(searchLower) && !email.includes(searchLower)) return false;
            }
            if (minScore > 0) {
                const score = Number(c.overall_weighted_score || c.overall_score || c.relevance_score || 0);
                if (score < minScore) return false;
            }
            return true;
        });
    }, [mergedCandidates, searchQuery, minScore]);

    const exportCSV = () => {
        if (filteredCandidates.length === 0) return;
        const headers = ["ID", "Name", "Score", "Reasoning"];
        const rows = filteredCandidates.map(c => {
            const id = c.candidate_id || c.id || "";
            const name = c.candidate_name || c.name || "";
            const score = c.overall_weighted_score || c.overall_score || c.relevance_score || 0;
            const reasoning = String(c.reasoning || c.match_reason || "").replace(/"/g, '""');
            return `"${id}","${name}","${score}","${reasoning}"`;
        });
        const csv = [headers.join(","), ...rows].join("\n");
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `candidates_${selectedJobId}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const selectedJob = jobs.find(j => j.job_id === selectedJobId);

    return (
        <div className="fade-in">
            <div style={{ marginBottom: 32 }}>
                <h1 style={{ fontSize: "2.5rem", fontWeight: 900, margin: 0, letterSpacing: "-1px" }}>Pipeline Intelligence</h1>
                <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", marginTop: 4 }}>
                    Aggregated candidate analytics across all active neural pipelines.
                </p>
            </div>

            {jobs.length === 0 && !loading ? (
                <EmptyState 
                    icon="💼" 
                    title="No Pipelines Found" 
                    description="Start by creating an active recruitment requisition in the Intelligence Hub to see candidates." 
                    action={{ label: "Go to Jobs", onClick: () => router.push("/jobs") }} 
                />
            ) : (
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
                        <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Min Match Score</label>
                        <select className="input" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} style={{ height: "45px" }}>
                            <option value={0}>All Scores</option>
                            <option value={50}>&gt; 50</option>
                            <option value={70}>&gt; 70</option>
                            <option value={90}>&gt; 90</option>
                        </select>
                    </div>
                    
                    <div style={{ flex: 1 }}>
                        <label style={{ fontSize: "0.8rem", color: "var(--text-muted)", display: "block", marginBottom: 8, fontWeight: 600 }}>Quick Search</label>
                        <div style={{ position: "relative" }}>
                            <Search size={18} style={{ position: "absolute", left: 14, top: 13, color: "var(--text-muted)" }} />
                            <input 
                                className="input" 
                                placeholder="Search candidates..." 
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{ paddingLeft: 44, height: "45px" }} 
                            />
                        </div>
                    </div>
                </div>
            )}

            {loading && selectedJobId && (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "100px 0" }}>
                    <div className="spinner" style={{ width: 40, height: 40, marginBottom: 16 }} />
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Querying Vector Database...</p>
                </div>
            )}

            {!loading && selectedJobId && (
                <div className="stagger-1">
                    {filteredCandidates.length > 0 ? (
                        <>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                                <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
                                    {selectedJob?.job_title} Results
                                </h3>
                                <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                                    <button className="button button-outline" onClick={exportCSV} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 12px" }}>
                                        <Download size={16} /> Export CSV
                                    </button>
                                    <span className="badge badge-blue">{filteredCandidates.length} Profiles Found</span>
                                </div>
                            </div>
                            <CandidateTable 
                                candidates={filteredCandidates} 
                                onRowClick={setSelectedCandidate} 
                                stage={selectedJob?.current_stage || ""}
                            />
                        </>
                    ) : (
                        <div className="glass-card" style={{ padding: 80, textAlign: "center", opacity: 0.7 }}>
                            <p style={{ fontSize: "2.5rem", margin: "0 0 16px" }}>🔍</p>
                            <p style={{ fontSize: "1.1rem" }}>This pipeline has not generated candidate data yet.</p>
                            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Agent 3 (Scout) needs to finalize the RAG retrieval phase.</p>
                        </div>
                    )}
                </div>
            )}

            {!selectedJobId && !loading && jobs.length > 0 && (
                <EmptyState 
                    icon="🧬"
                    title="Select a Pipeline to Begin Analytics"
                    description="Choose an active recruitment requisition from the selector above to view deterministic scores, gap analysis, and system reasoning for each candidate."
                />
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
