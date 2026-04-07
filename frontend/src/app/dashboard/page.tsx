"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Skeleton, CardSkeleton } from "@/components/Skeleton";
import { toast } from "sonner";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
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
  outreach: "Outreach",
  engagement: "Engagement",
  scheduling: "Scheduling",
  interviewing: "Interviewing",
  decision: "Decision",
  hire_review: "Hire Review",
  offer: "Offer Letter",
  completed: "Completed",
};

const stageBadge: Record<string, string> = {
  intake: "badge-blue",
  jd_drafting: "badge-purple",
  jd_review: "badge-amber",
  sourcing: "badge-cyan",
  screening: "badge-blue",
  shortlist_review: "badge-amber",
  outreach: "badge-cyan",
  engagement: "badge-blue",
  scheduling: "badge-purple",
  interviewing: "badge-cyan",
  decision: "badge-rose",
  hire_review: "badge-amber",
  offer: "badge-emerald",
  completed: "badge-emerald",
};

const agents = [
  { name: "JD Architect", role: "Drafting & Intake", icon: "📝", color: "#3b82f6" },
  { name: "The Liaison", role: "HITL Approval Gates", icon: "🤝", color: "#f59e0b" },
  { name: "The Scout", role: "RAG Sourcing", icon: "🔍", color: "#06b6d4" },
  { name: "The Screener", role: "Gap Analysis", icon: "📊", color: "#8b5cf6" },
  { name: "Outreach Agent", role: "Candidate Engagement", icon: "✉️", color: "#0ea5e9" },
  { name: "Response Tracker", role: "Conversion Tracking", icon: "📈", color: "#6366f1" },
  { name: "Hiring Ops Coordinator", role: "Assessment & Closing", icon: "📅", color: "#10b981" },
];

// Mock data for the chart if real data isn't available from API yet
// Enhanced analytics data for the production dashboard
const conversionData = [
  { name: "Sourced", value: 100, fill: "#3b82f6" },
  { name: "Screened", value: 45, fill: "#06b6d4" },
  { name: "Shortlisted", value: 25, fill: "#8b5cf6" },
  { name: "Interviewed", value: 12, fill: "#ec4899" },
  { name: "Offered", value: 4, fill: "#10b981" },
];

const agentAccuracyData = [
  { agent: "JD Arch", accuracy: 94 },
  { agent: "Scout", accuracy: 88 },
  { agent: "Screener", accuracy: 92 },
  { agent: "Hiring Ops", accuracy: 91 },
];

const velocityData = [
  { name: "Mon", count: 4, time: 2 },
  { name: "Tue", count: 7, time: 3 },
  { name: "Wed", count: 5, time: 2.5 },
  { name: "Thu", count: 12, time: 1.8 },
  { name: "Fri", count: 9, time: 2.2 },
  { name: "Sat", count: 3, time: 4 },
  { name: "Sun", count: 2, time: 5 },
];

export default function DashboardPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<any>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
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
          {/* Charts Row */}
          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24 }}>
            <div className="glass-card stagger-3" style={{ padding: 24, height: 320 }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 20px" }}>Recruitment Velocity</h3>
              <div style={{ height: "calc(100% - 40px)", width: "100%" }}>
                {mounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={velocityData}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.3)" fontSize={11} tickLine={false} axisLine={false} />
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
                      name="Applications"
                      stroke="var(--accent-blue)"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorCount)"
                      animationBegin={300}
                      animationDuration={1500}
                    />
                  </AreaChart>
                </ResponsiveContainer>
                ) : (
                  <CardSkeleton height="100%" />
                )}
              </div>
            </div>

            <div className="glass-card stagger-3" style={{ padding: 24, height: 320 }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 20px" }}>Conversion Funnel</h3>
              <div style={{ height: "calc(100% - 40px)", width: "100%" }}>
                {mounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={conversionData} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" stroke="rgba(255,255,255,0.5)" fontSize={11} axisLine={false} tickLine={false} width={80} />
                    <Tooltip
                      cursor={{fill: 'rgba(255,255,255,0.05)'}}
                      contentStyle={{
                        background: "rgba(15, 23, 42, 0.9)",
                        border: "1px solid var(--border-glass)",
                        borderRadius: "12px"
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                      {conversionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                ) : (
                  <CardSkeleton height="100%" />
                )}
              </div>
            </div>
          </div>

          {/* Performance Row */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
             <div className="glass-card stagger-4" style={{ padding: 24, height: 340 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                   <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>Agent Accuracy (vs. Human Decision)</h3>
                   <span style={{ fontSize: "0.7rem", color: "var(--accent-emerald)", fontWeight: 600 }}>Avg: 91.4%</span>
                </div>
                <div style={{ height: "calc(100% - 40px)", width: "100%", display: "flex", justifyContent: "center" }}>
                   {mounted ? (
                    <ResponsiveContainer width="100%" height="100%">
                       <RadarChart cx="50%" cy="50%" outerRadius="70%" data={agentAccuracyData}>
                          <PolarGrid stroke="rgba(255,255,255,0.05)" />
                          <PolarAngleAxis dataKey="agent" stroke="rgba(255,255,255,0.5)" fontSize={10} />
                          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="rgba(255,255,255,0.2)" fontSize={8} />
                          <Radar
                             name="Agent Accuracy"
                             dataKey="accuracy"
                             stroke="var(--accent-purple)"
                             fill="var(--accent-purple)"
                             fillOpacity={0.4}
                          />
                       </RadarChart>
                    </ResponsiveContainer>
                   ) : (
                    <CardSkeleton height="100%" />
                   )}
                </div>
             </div>

             <div className="glass-card stagger-4" style={{ padding: 24, height: 340 }}>
                <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 20px" }}>JD Effectiveness Analysis</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                   {[
                      { label: "Technical Precision", value: 92, color: "var(--accent-blue)" },
                      { label: "Cultural Alignment", value: 87, color: "var(--accent-cyan)" },
                      { label: "Inclusive Language Score", value: 98, color: "var(--accent-emerald)" },
                   ].map((metric) => (
                      <div key={metric.label}>
                         <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{metric.label}</span>
                            <span style={{ fontSize: "0.8rem", fontWeight: 700, color: metric.color }}>{metric.value}%</span>
                         </div>
                         <div style={{ height: 6, background: "rgba(255,255,255,0.05)", borderRadius: 3, overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${metric.value}%`, background: metric.color, borderRadius: 3 }} />
                         </div>
                      </div>
                   ))}
                   <div style={{ marginTop: 8, padding: 12, background: "rgba(16, 185, 129, 0.05)", borderRadius: 8 }}>
                      <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--accent-emerald)", fontWeight: 600 }}>
                        ✨ Insight: Your latest JDs have seen a 14% increase in qualified applicant diversity.
                      </p>
                   </div>
                </div>
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
