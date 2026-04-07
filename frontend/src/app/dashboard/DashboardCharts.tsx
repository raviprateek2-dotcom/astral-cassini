"use client";

import { CardSkeleton } from "@/components/Skeleton";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import {
  dashboardAgentAccuracyAvgLabel,
  dashboardAgentAccuracyData,
  dashboardConversionData,
  dashboardVelocityData,
  jdEffectivenessInsight,
  jdEffectivenessMetrics,
} from "./dashboardCharts.constants";
import type { AnalyticsDashboard, ScoreDistributionResponse } from "./useDashboardData";

function buildRadarFromScoreDistribution(
  response: ScoreDistributionResponse | null | undefined,
): { agent: string; accuracy: number }[] | null {
  const rows = response?.distribution;
  if (!rows?.length) return null;
  const counts = new Map<string, number>();
  for (const row of rows) {
    counts.set(row.range, row.count ?? 0);
  }
  const sum = (...keys: string[]) => keys.reduce((s, k) => s + (counts.get(k) ?? 0), 0);
  const tiers = [
    { agent: "0-29", raw: sum("0-9", "10-19", "20-29") },
    { agent: "30-49", raw: sum("30-39", "40-49") },
    { agent: "50-69", raw: sum("50-59", "60-69") },
    { agent: "70+", raw: sum("70-79", "80-89", "90-99") },
  ];
  const total = tiers.reduce((s, t) => s + t.raw, 0);
  if (total === 0) return null;
  const maxRaw = Math.max(...tiers.map((t) => t.raw), 1);
  return tiers.map((t) => ({
    agent: t.agent,
    accuracy: Math.round((t.raw / maxRaw) * 100),
  }));
}

export function DashboardCharts({
  mounted,
  analytics,
  scoreDistribution,
}: {
  mounted: boolean;
  analytics?: AnalyticsDashboard | null;
  scoreDistribution?: ScoreDistributionResponse | null;
}) {
  const funnelColors = ["#3b82f6", "#06b6d4", "#8b5cf6", "#ec4899", "#10b981", "#14b8a6"];
  const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const velocityCounts = new Array(7).fill(0);
  for (const event of analytics?.recent ?? []) {
    const parsed = event.timestamp ? new Date(event.timestamp) : null;
    if (!parsed || Number.isNaN(parsed.getTime())) continue;
    const jsDay = parsed.getDay(); // 0=Sun ... 6=Sat
    const idx = jsDay === 0 ? 6 : jsDay - 1; // Mon-first
    velocityCounts[idx] += 1;
  }
  const velocityChartData =
    velocityCounts.some((count) => count > 0)
      ? weekdayLabels.map((name, index) => ({
          name,
          count: velocityCounts[index],
          time: dashboardVelocityData[index].time,
        }))
      : [...dashboardVelocityData];

  const conversionChartData =
    analytics?.funnel && analytics.funnel.length > 0
      ? analytics.funnel.map((item, index) => ({
          name: item.stage.replace("Pipelines Started", "Started").replace("Candidates Scored", "Scored"),
          value: item.count,
          fill: funnelColors[index % funnelColors.length],
        }))
      : [...dashboardConversionData];
  const averageLabel =
    typeof analytics?.summary?.average_screening_score === "number"
      ? `Avg Score: ${analytics.summary.average_screening_score}%`
      : dashboardAgentAccuracyAvgLabel;
  const averageScreening = analytics?.summary?.average_screening_score ?? jdEffectivenessMetrics[0].value;
  const totalScored = analytics?.summary?.total_candidates_scored ?? 0;
  const totalHires = analytics?.summary?.total_hires ?? 0;
  const culturalAlignmentLive =
    totalScored > 0 ? Math.round((totalHires / totalScored) * 100) : jdEffectivenessMetrics[1].value;
  const jdMetricsLive = [
    { label: "Technical Precision", value: Math.round(averageScreening), color: "var(--accent-blue)" },
    { label: "Cultural Alignment", value: culturalAlignmentLive, color: "var(--accent-cyan)" },
    { label: "Inclusive Language Score", value: jdEffectivenessMetrics[2].value, color: "var(--accent-emerald)" },
  ];
  const jdInsightLive =
    averageScreening >= 85
      ? "✨ Insight: Screening quality is strong and trending above benchmark."
      : jdEffectivenessInsight;

  const radarDataLive = buildRadarFromScoreDistribution(scoreDistribution);
  const radarChartData = radarDataLive ?? [...dashboardAgentAccuracyData];
  const radarTitle = radarDataLive
    ? "Screening score profile (by band)"
    : "Agent Accuracy (vs. Human Decision)";
  const radarSeriesName = radarDataLive ? "Relative mix" : "Agent Accuracy";

  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24 }}>
        <div className="glass-card stagger-3" style={{ padding: 24, height: 320 }}>
          <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 20px" }}>Recruitment Velocity</h3>
          <div style={{ height: "calc(100% - 40px)", width: "100%" }}>
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={velocityChartData}>
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
                      backdropFilter: "blur(10px)",
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
                <BarChart data={conversionChartData} layout="vertical" margin={{ left: 20 }}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" stroke="rgba(255,255,255,0.5)" fontSize={11} axisLine={false} tickLine={false} width={80} />
                  <Tooltip
                    cursor={{ fill: "rgba(255,255,255,0.05)" }}
                    contentStyle={{
                      background: "rgba(15, 23, 42, 0.9)",
                      border: "1px solid var(--border-glass)",
                      borderRadius: "12px",
                    }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                    {conversionChartData.map((entry, index) => (
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

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <div className="glass-card stagger-4" style={{ padding: 24, height: 340 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h3 style={{ fontSize: "1rem", fontWeight: 700, margin: 0 }}>{radarTitle}</h3>
            <span style={{ fontSize: "0.7rem", color: "var(--accent-emerald)", fontWeight: 600 }}>{averageLabel}</span>
          </div>
          <div style={{ height: "calc(100% - 40px)", width: "100%", display: "flex", justifyContent: "center" }}>
            {mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarChartData}>
                  <PolarGrid stroke="rgba(255,255,255,0.05)" />
                  <PolarAngleAxis dataKey="agent" stroke="rgba(255,255,255,0.5)" fontSize={10} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="rgba(255,255,255,0.2)" fontSize={8} />
                  <Radar
                    name={radarSeriesName}
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
            {jdMetricsLive.map((metric) => (
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
                {jdInsightLive}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
