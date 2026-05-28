"use client";

import { useState, useEffect } from "react";
import {
  ActivePipelines,
  DashboardHeader,
  DashboardMainGrid,
  DashboardShell,
  MetricsGrid,
  Sidebar,
} from "./DashboardSections";
import { DashboardCharts } from "./DashboardCharts";
import { agents, buildDashboardMetrics, stageBadge, stageLabels } from "./dashboard.constants";
import { useDashboardData } from "./useDashboardData";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function DashboardPage() {
  const {
    jobs,
    loading,
    refreshing,
    refetch,
    silentRefetch,
    health,
    analytics,
    scoreDistribution,
    pendingApprovals,
    totalCandidates,
    completedJobs,
  } = useDashboardData();
  const [mounted, setMounted] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const activeJobId = jobs.length > 0 ? jobs[0].job_id : null;
  const { events } = useWebSocket(activeJobId);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (events.length > 0) {
      silentRefetch();
    }
  }, [events, silentRefetch]);

  const filteredJobs = jobs.filter(job => 
    job.job_title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    job.department.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleExportCSV = () => {
    const header = ["Job ID", "Title", "Department", "Stage", "Candidates", "Created At"];
    const rows = filteredJobs.map(j => [
        j.job_id,
        j.job_title,
        j.department,
        j.current_stage,
        j.candidates_count?.toString() || "0",
        j.created_at ? new Date(j.created_at).toISOString() : ""
    ]);
    const csvContent = [header, ...rows].map(e => e.map(item => `"${(item || "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dashboard_metrics_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
  };

  return (
    <DashboardShell>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <DashboardHeader onRefresh={() => void refetch()} refreshing={refreshing} />
        <div style={{ display: "flex", gap: 12, alignItems: "center", marginTop: 8 }}>
            <input 
                type="text" 
                placeholder="Global Filter..." 
                className="input" 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{ maxWidth: 200, fontSize: "0.8rem", padding: "8px 12px" }}
            />
            <button className="btn-outline" onClick={handleExportCSV} style={{ fontSize: "0.8rem", padding: "8px 16px" }}>
                Export CSV
            </button>
        </div>
      </div>
      <MetricsGrid
        loading={loading}
        metrics={buildDashboardMetrics({
          activePipelines: filteredJobs.length,
          totalCandidates,
          pendingApprovals,
          completedJobs,
        })}
      />
      <DashboardMainGrid
        main={
          <>
            <DashboardCharts mounted={mounted} analytics={analytics} scoreDistribution={scoreDistribution} />
            <ActivePipelines loading={loading} jobs={filteredJobs} stageBadge={stageBadge} stageLabels={stageLabels} />
          </>
        }
        aside={<Sidebar agents={agents} health={health} />}
      />
    </DashboardShell>
  );
}
