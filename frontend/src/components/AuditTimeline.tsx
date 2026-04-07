import React, { useState } from 'react';
import { Activity, Clock, ShieldCheck, Cpu } from 'lucide-react';
import type { AuditLogEntry } from '@/types/domain';

interface AuditTimelineProps {
    logs: AuditLogEntry[];
}

export function AuditTimeline({ logs }: AuditTimelineProps) {
    const [expanded, setExpanded] = useState(false);

    if (!logs || logs.length === 0) {
        return (
            <div className="glass-card" style={{ padding: "20px", color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center" }}>
                <Activity size={24} style={{ opacity: 0.5, margin: "0 auto 8px", display: "block" }} />
                No audit logs available yet.
            </div>
        );
    }

    const displayLogs = expanded ? logs : logs.slice(-5); // Show last 5 by default

    const formatTime = (iso: string) => {
        try {
            const d = new Date(iso);
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        } catch {
            return iso;
        }
    };

    return (
        <div className="glass-card fade-in" style={{ padding: "24px", height: "100%", display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                    <ShieldCheck size={18} color="var(--accent-emerald)" />
                    System Audit Trail
                </h3>
                <span className="badge badge-purple" style={{ fontSize: "0.7rem" }}>{logs.length} Operations</span>
            </div>

            <div style={{ flex: 1, overflowY: "auto", paddingRight: "10px" }}>
                <div style={{ borderLeft: "2px solid rgba(255,255,255,0.05)", marginLeft: "12px", paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "24px" }}>
                    {displayLogs.map((log, i) => {
                        const agent = log.agent ?? "";
                        const timestamp = log.timestamp ?? "";
                        const details = log.details ?? "";
                        const action = log.action ?? "";
                        return (
                        <div key={i} style={{ position: "relative" }}>
                            <div style={{ 
                                position: "absolute", left: "-27px", top: 0, 
                                width: 12, height: 12, borderRadius: "50%", 
                                background: agent.includes("Guardian") ? "var(--accent-emerald)" : agent.includes("Coordinator") ? "var(--accent-purple)" : "var(--accent-blue)",
                                border: "2px solid #0f172a",
                                boxShadow: `0 0 10px ${agent.includes("Guardian") ? "var(--accent-emerald)" : "var(--accent-blue)"}`
                            }} />

                            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4, marginBottom: 4 }}>
                                <Clock size={12} /> {formatTime(timestamp)}
                            </div>
                            
                            <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: 4, display: "flex", alignItems: "center", gap: 6 }}>
                                <Cpu size={14} color="var(--text-secondary)" />
                                {agent || "System"}
                            </div>

                            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                                {details}
                            </div>
                            
                            <div style={{ marginTop: 6 }}>
                                <span style={{ fontSize: "0.65rem", padding: "2px 6px", background: "rgba(255,255,255,0.05)", borderRadius: 4, color: "var(--text-muted)", textTransform: "uppercase" }}>
                                    {action}
                                </span>
                            </div>
                        </div>
                        );
                    })}
                </div>
            </div>

            {logs.length > 5 && (
                <button 
                    className="btn-outline" 
                    onClick={() => setExpanded(!expanded)}
                    style={{ width: "100%", marginTop: "20px", padding: "8px", fontSize: "0.8rem" }}
                >
                    {expanded ? "Collapse Trail" : `View All (${logs.length})`}
                </button>
            )}
        </div>
    );
}
