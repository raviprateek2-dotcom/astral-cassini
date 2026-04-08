"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import { Skeleton } from "@/components/Skeleton";

export interface JobSummary {
  job_id: string;
  job_title: string;
  department: string;
  current_stage: string;
  candidates_count?: number;
  created_at?: string;
}

export type MetricCard = {
  label: string;
  value: number;
  icon: string;
  color: string;
  bg: string;
};

type Agent = {
  name: string;
  role: string;
  icon: string;
  color: string;
};

type HealthStatus = {
  llm_model?: string;
  indexed_resumes?: number;
  observability?: Record<string, number>;
} | null;

export function DashboardShell({ children }: { children: ReactNode }) {
  return <div className="fade-in">{children}</div>;
}

export function DashboardPrimaryColumn({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {children}
    </div>
  );
}

export function DashboardMainGrid({ main, aside }: { main: ReactNode; aside: ReactNode }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
      <DashboardPrimaryColumn>{main}</DashboardPrimaryColumn>
      {aside}
    </div>
  );
}

export function DashboardHeader({
  onRefresh,
  refreshing = false,
}: {
  onRefresh?: () => void;
  refreshing?: boolean;
}) {
  return (
    <div
      style={{ marginBottom: 32, display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}
      className="stagger-1"
    >
      <div>
        <h1 style={{ fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.02em", margin: 0 }}>
          Recruitment Dashboard
        </h1>
        <p style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.9rem" }}>
          Monitor your autonomous multi-agent recruitment pipelines
        </p>
      </div>
      {onRefresh ? (
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          title="Refresh metrics and job list"
          className="glass-card"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "10px 16px",
            fontSize: "0.85rem",
            fontWeight: 600,
            cursor: refreshing ? "wait" : "pointer",
            opacity: refreshing ? 0.7 : 1,
            border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(255,255,255,0.04)",
            color: "var(--text-primary)",
          }}
        >
          <RefreshCw size={16} style={refreshing ? { animation: "spin 0.8s linear infinite" } : undefined} />
          Refresh
        </button>
      ) : null}
    </div>
  );
}

export function MetricsGrid({ loading, metrics }: { loading: boolean; metrics: MetricCard[] }) {
  return (
    <div className="stagger-2" style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20, marginBottom: 32 }}>
      {loading
        ? Array(4).fill(0).map((_, i) => (
            <div key={i} className="glass-card" style={{ padding: 24 }}>
              <Skeleton width="40%" height={12} style={{ marginBottom: 12 }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                <Skeleton width="50%" height={40} />
                <Skeleton width={32} height={32} borderRadius="50%" />
              </div>
            </div>
          ))
        : metrics.map((metric) => (
            <div
              key={metric.label}
              className="glass-card"
              style={{ padding: 24, border: `1px solid ${metric.color}20`, background: metric.bg }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 700, margin: 0 }}>
                    {metric.label}
                  </p>
                  <p style={{ fontSize: "2.5rem", fontWeight: 900, margin: "8px 0 0", color: metric.color, letterSpacing: "-1px" }}>
                    {metric.value}
                  </p>
                </div>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(255,255,255,0.03)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem" }}>
                  {metric.icon}
                </div>
              </div>
            </div>
          ))}
    </div>
  );
}

export function ActivePipelines({
  loading,
  jobs,
  stageBadge,
  stageLabels,
}: {
  loading: boolean;
  jobs: JobSummary[];
  stageBadge: Record<string, string>;
  stageLabels: Record<string, string>;
}) {
  return (
    <div className="glass-card stagger-4" style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>Active Pipelines</h2>
        <Link href="/jobs">
          <button className="btn-primary" style={{ fontSize: "0.8rem", padding: "8px 16px" }}>
            + New Job
          </button>
        </Link>
      </div>

      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {Array(3).fill(0).map((_, i) => (
            <div key={i} style={{ padding: "16px 20px", border: "1px solid var(--border-glass)", borderRadius: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ flex: 1 }}>
                  <Skeleton width="180px" height={16} style={{ marginBottom: 8 }} />
                  <Skeleton width="120px" height={12} />
                </div>
                <Skeleton width="80px" height={24} borderRadius={99} />
              </div>
            </div>
          ))}
        </div>
      ) : jobs.length === 0 ? (
        <div style={{ textAlign: "center", padding: "48px 20px", color: "var(--text-muted)" }}>
          <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>💼</p>
          <p style={{ fontSize: "0.9rem", margin: "0 0 4px" }}>No active pipelines</p>
          <p style={{ fontSize: "0.8rem" }}>Create a new job requisition to get started</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {jobs.map((job) => (
            <Link key={job.job_id} href={`/jobs?id=${job.job_id}`} style={{ textDecoration: "none", color: "inherit" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "16px 20px",
                  borderRadius: 12,
                  border: "1px solid var(--border-glass)",
                  transition: "all 0.2s ease",
                  cursor: "pointer",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-hover)";
                  e.currentTarget.style.background = "rgba(59, 130, 246, 0.05)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--border-glass)";
                  e.currentTarget.style.background = "transparent";
                }}
              >
                <div>
                  <p style={{ fontWeight: 600, margin: 0, fontSize: "0.95rem" }}>{job.job_title}</p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", margin: "4px 0 0" }}>
                    {job.department} • {job.candidates_count} candidates
                  </p>
                </div>
                <span className={`badge ${stageBadge[job.current_stage] || "badge-blue"}`}>
                  {stageLabels[job.current_stage] || job.current_stage}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function Sidebar({ agents, health }: { agents: Agent[]; health: HealthStatus }) {
  const metrics = health?.observability ?? {};
  const durationSum = metrics.agent_duration_ms_sum ?? 0;
  const durationCount = metrics.agent_duration_ms_count ?? 0;
  const avgDuration = durationCount > 0 ? (durationSum / durationCount).toFixed(1) : "0.0";

  return (
    <div>
      <div className="glass-card stagger-5" style={{ padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>Agent Roster</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {agents.map((agent, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", borderRadius: 10, border: "1px solid var(--border-glass)" }}>
              <span style={{ fontSize: "1.3rem", width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 8, background: `${agent.color}15` }}>
                {agent.icon}
              </span>
              <div>
                <p style={{ fontWeight: 600, fontSize: "0.85rem", margin: 0, color: agent.color }}>
                  Agent {i + 1}: {agent.name}
                </p>
                <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: "2px 0 0" }}>{agent.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card stagger-6" style={{ padding: "24px", background: "rgba(16, 185, 129, 0.05)" }}>
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 12px" }}>
          System Status
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div className={health ? "pulse-active" : ""} style={{ width: 10, height: 10, borderRadius: "50%", background: health ? "var(--accent-emerald)" : "var(--accent-rose)" }} />
          <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>
            {health ? "All Systems Operational" : "Backend Offline"}
          </span>
        </div>
        {health && (
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 4 }}>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Model:</span> {health.llm_model}
            </p>
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>Index:</span> {health.indexed_resumes} resumes indexed
            </p>
          </div>
        )}
      </div>

      <div className="glass-card" style={{ padding: "20px", marginTop: 24, background: "rgba(59, 130, 246, 0.06)" }}>
        <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 12px" }}>
          Agent Reliability (SLI)
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <MiniMetric label="Success" value={metrics.agent_runs_success ?? 0} />
          <MiniMetric label="Failed" value={metrics.agent_runs_failed ?? 0} />
          <MiniMetric label="Avg ms" value={avgDuration} />
          <MiniMetric label="WS OK" value={metrics.ws_connect_success ?? 0} />
        </div>
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number | string }) {
  return (
    <div style={{ border: "1px solid var(--border-glass)", borderRadius: 8, padding: "8px 10px", background: "rgba(255,255,255,0.02)" }}>
      <p style={{ fontSize: "0.65rem", color: "var(--text-muted)", margin: 0 }}>{label}</p>
      <p style={{ fontSize: "0.9rem", fontWeight: 700, margin: "4px 0 0" }}>{value}</p>
    </div>
  );
}
