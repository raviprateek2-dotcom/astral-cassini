/** Mock / placeholder series for dashboard Recharts until wired to analytics API. */

export const dashboardConversionData = [
  { name: "Sourced", value: 100, fill: "#3b82f6" },
  { name: "Screened", value: 45, fill: "#06b6d4" },
  { name: "Shortlisted", value: 25, fill: "#8b5cf6" },
  { name: "Interviewed", value: 12, fill: "#ec4899" },
  { name: "Offered", value: 4, fill: "#10b981" },
] as const;

export const dashboardAgentAccuracyData = [
  { agent: "JD Arch", accuracy: 94 },
  { agent: "Scout", accuracy: 88 },
  { agent: "Screener", accuracy: 92 },
  { agent: "Hiring Ops", accuracy: 91 },
] as const;

export const dashboardVelocityData = [
  { name: "Mon", count: 4, time: 2 },
  { name: "Tue", count: 7, time: 3 },
  { name: "Wed", count: 5, time: 2.5 },
  { name: "Thu", count: 12, time: 1.8 },
  { name: "Fri", count: 9, time: 2.2 },
  { name: "Sat", count: 3, time: 4 },
  { name: "Sun", count: 2, time: 5 },
] as const;

export const dashboardAgentAccuracyAvgLabel = "Avg: 91.4%";

export const jdEffectivenessMetrics = [
  { label: "Technical Precision", value: 92, color: "var(--accent-blue)" },
  { label: "Cultural Alignment", value: 87, color: "var(--accent-cyan)" },
  { label: "Inclusive Language Score", value: 98, color: "var(--accent-emerald)" },
] as const;

export const jdEffectivenessInsight =
  "✨ Insight: Your latest JDs have seen a 14% increase in qualified applicant diversity.";
