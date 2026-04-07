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

export default function DashboardPage() {
  const {
    jobs,
    loading,
    refreshing,
    refetch,
    health,
    analytics,
    scoreDistribution,
    pendingApprovals,
    totalCandidates,
    completedJobs,
  } = useDashboardData();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <DashboardShell>
      <DashboardHeader onRefresh={() => void refetch()} refreshing={refreshing} />
      <MetricsGrid
        loading={loading}
        metrics={buildDashboardMetrics({
          activePipelines: jobs.length,
          totalCandidates,
          pendingApprovals,
          completedJobs,
        })}
      />
      <DashboardMainGrid
        main={
          <>
            <DashboardCharts mounted={mounted} analytics={analytics} scoreDistribution={scoreDistribution} />
            <ActivePipelines loading={loading} jobs={jobs} stageBadge={stageBadge} stageLabels={stageLabels} />
          </>
        }
        aside={<Sidebar agents={agents} health={health} />}
      />
    </DashboardShell>
  );
}
