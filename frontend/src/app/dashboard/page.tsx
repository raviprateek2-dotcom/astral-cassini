"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Skeleton, CardSkeleton } from "@/components/Skeleton";
import { toast } from "sonner";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

interface JobSummary {
  job_id: string;
  job_title: string;
  department: string;
  current_stage: string;
  candidates_count: number;
  created_at: string;
}

const stageLabels: Record<string, string> = {
  intake: "Intake",
  jd_drafting: "Drafting JD",
  jd_review: "JD Review",
  sourcing: "Sourcing",
  screening: "Screening",
  shortlist_review: "Shortlist Review",
  scheduling: "Scheduling",
  interviewing: "Interviewing",
  decision: "Decision",
  hire_review: "Hire Review",
  completed: "Completed",
};

const stageBadge: Record<string, string> = {
  intake: "badge-blue",
  jd_drafting: "badge-purple",
  jd_review: "badge-amber",
  sourcing: "badge-cyan",
  screening: "badge-blue",
  shortlist_review: "badge-amber",
  scheduling: "badge-purple",
  interviewing: "badge-cyan",
  decision: "badge-rose",
  hire_review: "badge-amber",
  completed: "badge-emerald",
};

const agents = [
  { name: "JD Architect", role: "Drafts job descriptions", icon: "📝", color: "#3b82f6" },
  { name: "The Liaison", role: "HITL approval gates", icon: "🤝", color: "#f59e0b" },
  { name: "The Scout", role: "Semantic resume search", icon: "🔍", color: "#06b6d4" },
  { name: "The Screener", role: "Gap analysis & scoring", icon: "📊", color: "#8b5cf6" },
  { name: "The Coordinator", role: "Interview scheduling", icon: "📅", color: "#10b981" },
  { name: "The Interviewer", role: "Transcript assessment", icon: "🎙️", color: "#ec4899" },
  { name: "The Decider", role: "Final recommendations", icon: "⚖️", color: "#f43f5e" },
];

// Mock data for the chart if real data isn't available from API yet
const velocityData = [
  { name: "Mon", count: 4 },
  { name: "Tue", count: 7 },
  { name: "Wed", count: 5 },
  { name: "Thu", count: 12 },
  { name: "Fri", count: 9 },
  { name: "Sat", count: 3 },
  { name: "Sun", count: 2 },
];

export default function DashboardPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [jobsData, healthData] = await Promise.all([
        api.listJobs().catch(() => []),
        api.health().catch(() => null),
      ]);
      setJobs(jobsData);
      setHealth(healthData);
      if (healthData) {
        toast.success("Intelligence Hub Synchronized", {
          description: "All agents are online and responsive."
        });
      }
    } catch (err: any) {
      toast.error("Network Error", {
        description: "Failed to establish secure hub connection."
      });
    } finally {
      setLoading(false);
    }
  }

  const pendingApprovals = jobs.filter((j) =>
    ["jd_review", "shortlist_review", "hire_review"].includes(j.current_stage)
  ).length;

  const totalCandidates = jobs.reduce((sum, j) => sum + (j.candidates_count || 0), 0);
  const completedJobs = jobs.filter((j) => j.current_stage === "completed").length;

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ marginBottom: 32 }} className="stagger-1">
        <h1
          style={{
            fontSize: "2rem",
            fontWeight: 800,
            letterSpacing: "-0.02em",
            margin: 0,
          }}
        >
          Recruitment Dashboard
        </h1>
        <p style={{ color: "var(--text-secondary)", marginTop: 4, fontSize: "0.9rem" }}>
          Monitor your autonomous multi-agent recruitment pipelines
        </p>
      </div>

      {/* Metric Cards */}
      <div
        className="stagger-2"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: 20,
          marginBottom: 32,
        }}
      >
        {loading ? (
          Array(4).fill(0).map((_, i) => (
            <div key={i} className="glass-card" style={{ padding: 24 }}>
              <Skeleton width="40%" height={12} style={{ marginBottom: 12 }} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
                <Skeleton width="50%" height={40} />
                <Skeleton width={32} height={32} borderRadius="50%" />
              </div>
            </div>
          ))
        ) : (
          [
            {
              label: "Active Pipelines",
              value: jobs.length,
              icon: "🚀",
              color: "var(--accent-blue)",
              bg: "rgba(59, 130, 246, 0.05)"
            },
            {
              label: "Candidates in Pipeline",
              value: totalCandidates,
              icon: "👥",
              color: "var(--accent-cyan)",
              bg: "rgba(6, 182, 212, 0.05)"
            },
            {
              label: "Pending Approvals",
              value: pendingApprovals,
              icon: "🔔",
              color: "var(--accent-amber)",
              bg: "rgba(245, 158, 11, 0.05)"
            },
            {
              label: "Positions Filled",
              value: completedJobs,
              icon: "✅",
              color: "var(--accent-emerald)",
              bg: "rgba(16, 185, 129, 0.05)"
            },
          ].map((metric) => (
            <div key={metric.label} className="glass-card" style={{ padding: 24, border: `1px solid ${metric.color}20`, background: metric.bg }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                }}
              >
                <div>
                  <p
                    style={{
                      fontSize: "0.7rem",
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      fontWeight: 700,
                      margin: 0,
                    }}
                  >
                    {metric.label}
                  </p>
                  <p
                    style={{
                      fontSize: "2.5rem",
                      fontWeight: 900,
                      margin: "8px 0 0",
                      color: metric.color,
                      letterSpacing: "-1px"
                    }}
                  >
                    {metric.value}
                  </p>
                </div>
                <div style={{
                  width: 44, height: 44, borderRadius: 12, background: "rgba(255,255,255,0.03)",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem"
                }}>
                  {metric.icon}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Main Content Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Chart Section */}
          <div className="glass-card stagger-3" style={{ padding: 24, height: 320 }}>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 20px" }}>Recruitment Velocity</h2>
            <div style={{ height: "calc(100% - 40px)", width: "100%" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={velocityData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15, 23, 42, 0.9)",
                      border: "1px solid var(--border-glass)",
                      borderRadius: "12px",
                      backdropFilter: "blur(10px)"
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="count"
                    stroke="var(--accent-blue)"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorCount)"
                    animationBegin={300}
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Pipelines */}
          <div className="glass-card stagger-4" style={{ padding: 24 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 20,
              }}
            >
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>
                Active Pipelines
              </h2>
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
              <div
                style={{
                  textAlign: "center",
                  padding: "48px 20px",
                  color: "var(--text-muted)",
                }}
              >
                <p style={{ fontSize: "2rem", margin: "0 0 12px" }}>💼</p>
                <p style={{ fontSize: "0.9rem", margin: "0 0 4px" }}>No active pipelines</p>
                <p style={{ fontSize: "0.8rem" }}>
                  Create a new job requisition to get started
                </p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {jobs.map((job) => (
                  <Link
                    key={job.job_id}
                    href={`/jobs?id=${job.job_id}`}
                    style={{ textDecoration: "none", color: "inherit" }}
                  >
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
                        <p style={{ fontWeight: 600, margin: 0, fontSize: "0.95rem" }}>
                          {job.job_title}
                        </p>
                        <p
                          style={{
                            color: "var(--text-muted)",
                            fontSize: "0.8rem",
                            margin: "4px 0 0",
                          }}
                        >
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
        </div>

        <div>
          {/* Agent Roster */}
          <div className="glass-card stagger-5" style={{ padding: 24, marginBottom: 24 }}>
            <h2
              style={{
                fontSize: "1.1rem",
                fontWeight: 700,
                margin: "0 0 20px",
              }}
            >
              Agent Roster
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {agents.map((agent, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "10px 14px",
                    borderRadius: 10,
                    border: "1px solid var(--border-glass)",
                  }}
                >
                  <span
                    style={{
                      fontSize: "1.3rem",
                      width: 36,
                      height: 36,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: 8,
                      background: `${agent.color}15`,
                    }}
                  >
                    {agent.icon}
                  </span>
                  <div>
                    <p
                      style={{
                        fontWeight: 600,
                        fontSize: "0.85rem",
                        margin: 0,
                        color: agent.color,
                      }}
                    >
                      Agent {i + 1}: {agent.name}
                    </p>
                    <p
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-muted)",
                        margin: "2px 0 0",
                      }}
                    >
                      {agent.role}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* System Status */}
          <div
            className="glass-card stagger-6"
            style={{
              padding: "24px",
              background: "rgba(16, 185, 129, 0.05)",
            }}
          >
            <p
              style={{
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                margin: "0 0 12px",
              }}
            >
              System Status
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                className={health ? "pulse-active" : ""}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: health ? "var(--accent-emerald)" : "var(--accent-rose)",
                }}
              />
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
        </div>
      </div>
    </div>
  );
}
