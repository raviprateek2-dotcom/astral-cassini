"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import {
  api,
  type AnalyticsDashboardPayload,
  type HealthResponse,
  type ScoreDistributionPayload,
} from "@/lib/api";
import { fetchWithCache, invalidateCache } from "@/lib/dataCache";
import type { JobSummary } from "./DashboardSections";

type HealthStatus = HealthResponse | null;
export type AnalyticsDashboard = AnalyticsDashboardPayload;
export type ScoreDistributionResponse = ScoreDistributionPayload;

export function useDashboardData() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState<HealthStatus>(null);
  const [analytics, setAnalytics] = useState<AnalyticsDashboard | null>(null);
  const [scoreDistribution, setScoreDistribution] = useState<ScoreDistributionResponse | null>(null);
  const firstLoadRef = useRef(true);

  const loadData = useCallback(async (mode: "initial" | "silent" | "manual" = "silent") => {
    if (mode === "initial") setLoading(true);
    if (mode === "manual") setRefreshing(true);
    try {
      const force = mode === "manual";
      const [jobsData, healthData, analyticsData, scoreData] = await Promise.all([
        fetchWithCache("jobs:list", () => api.listJobs(), { ttlMs: 10_000, force }).catch(() => []),
        fetchWithCache("health", () => api.health(), { ttlMs: 10_000, force }).catch((): null => null),
        fetchWithCache("analytics:dashboard", () => api.getAnalyticsDashboard(), { ttlMs: 10_000, force }).catch(
          (): null => null
        ),
        fetchWithCache(
          "analytics:score_distribution",
          () => api.getAnalyticsScoreDistribution(),
          { ttlMs: 10_000, force }
        ).catch((): null => null),
      ]);
      setJobs(jobsData);
      setHealth(healthData);
      setAnalytics(analyticsData);
      setScoreDistribution(scoreData);
      if (healthData && firstLoadRef.current) {
        firstLoadRef.current = false;
        toast.success("Intelligence Hub Synchronized", {
          description: "All agents are online and responsive.",
        });
      }
      if (mode === "manual") {
        invalidateCache("jobs:");
        invalidateCache("analytics:");
        toast.success("Dashboard updated");
      }
    } catch {
      toast.error("Network Error", {
        description: "Failed to establish secure hub connection.",
      });
    } finally {
      if (mode === "initial") setLoading(false);
      if (mode === "manual") setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadData("initial");
  }, [loadData]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "visible") void loadData("silent");
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [loadData]);

  const pendingApprovals = useMemo(
    () => jobs.filter((j) => ["jd_review", "shortlist_review", "hire_review"].includes(j.current_stage)).length,
    [jobs],
  );

  const totalCandidates = useMemo(
    () => jobs.reduce((sum, j) => sum + (j.candidates_count || 0), 0),
    [jobs],
  );

  const completedJobs = useMemo(
    () => jobs.filter((j) => j.current_stage === "completed").length,
    [jobs],
  );

  return {
    jobs,
    loading,
    refreshing,
    refetch: () => loadData("manual"),
    health,
    analytics,
    scoreDistribution,
    pendingApprovals,
    totalCandidates,
    completedJobs,
  };
}
