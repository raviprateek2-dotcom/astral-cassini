import type { MetricCard } from "./DashboardSections";

export const stageLabels: Record<string, string> = {
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

export const stageBadge: Record<string, string> = {
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

export const agents = [
  { name: "JD Architect", role: "Drafting & Intake", icon: "📝", color: "#3b82f6" },
  { name: "The Liaison", role: "HITL Approval Gates", icon: "🤝", color: "#f59e0b" },
  { name: "The Scout", role: "RAG Sourcing", icon: "🔍", color: "#06b6d4" },
  { name: "The Screener", role: "Gap Analysis", icon: "📊", color: "#8b5cf6" },
  { name: "Outreach Agent", role: "Candidate Engagement", icon: "✉️", color: "#0ea5e9" },
  { name: "Response Tracker", role: "Conversion Tracking", icon: "📈", color: "#6366f1" },
  { name: "Hiring Ops Coordinator", role: "Assessment & Closing", icon: "📅", color: "#10b981" },
];

export function buildDashboardMetrics({
  activePipelines,
  totalCandidates,
  pendingApprovals,
  completedJobs,
}: {
  activePipelines: number;
  totalCandidates: number;
  pendingApprovals: number;
  completedJobs: number;
}): MetricCard[] {
  return [
    {
      label: "Active Pipelines",
      value: activePipelines,
      icon: "🚀",
      color: "var(--accent-blue)",
      bg: "rgba(59, 130, 246, 0.05)",
    },
    {
      label: "Candidates in Pipeline",
      value: totalCandidates,
      icon: "👥",
      color: "var(--accent-cyan)",
      bg: "rgba(6, 182, 212, 0.05)",
    },
    {
      label: "Pending Approvals",
      value: pendingApprovals,
      icon: "🔔",
      color: "var(--accent-amber)",
      bg: "rgba(245, 158, 11, 0.05)",
    },
    {
      label: "Positions Filled",
      value: completedJobs,
      icon: "✅",
      color: "var(--accent-emerald)",
      bg: "rgba(16, 185, 129, 0.05)",
    },
  ];
}
