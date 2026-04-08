/**
 * Shared API/domain shapes used across pages (keeps eslint `no-explicit-any` off common paths).
 */

export type WorkflowBlob = Record<string, unknown>;

export type JobListItem = {
    job_id: string;
    job_title: string;
    department: string;
    current_stage: string;
    candidates_count?: number;
    created_at?: string;
};

/** Table/modal row: API returns CandidateProfile | ScoredCandidate | Recommendation variants. */
export type CandidateLike = Record<string, unknown> & {
    id?: string;
    candidate_id?: string;
    candidate_name?: string;
    name?: string;
    overall_score?: number;
    overall_weighted_score?: number;
    relevance_score?: number;
    skills?: string[];
    strengths?: unknown;
    gaps?: unknown;
    missing_skills?: unknown;
    reasoning?: string;
    match_reason?: string;
    thought_process?: string;
};

export type AuditLogEntry = {
    agent?: string;
    action?: string;
    details?: string;
    timestamp?: string;
    stage?: string;
    id?: string;
};

/** Narrow unknown API values to audit rows without assertion casts. */
export function isAuditLogEntry(value: unknown): value is AuditLogEntry {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function auditLogEntriesFromUnknown(value: unknown): AuditLogEntry[] {
    if (!Array.isArray(value)) return [];
    return value.filter(isAuditLogEntry);
}

/** Full job record from GET /api/jobs/:id */
export type JobDetail = JobListItem & {
    state?: WorkflowBlob;
    audit_log?: AuditLogEntry[];
};

export type InterviewRow = Record<string, unknown> & {
    candidate_name?: string;
    interview_type?: string;
    scheduled_time?: string;
    duration_minutes?: number;
    interviewers?: string[];
    status?: string;
    meeting_link?: string;
};

export type AssessmentRow = Record<string, unknown> & {
    candidate_name?: string;
    overall_score?: number;
};

export type InterviewsApiResponse = {
    scheduled_interviews?: InterviewRow[];
    interview_assessments?: AssessmentRow[];
};

export type RecommendationRow = Record<string, unknown> & {
    candidate_id?: string;
    candidate_name?: string;
    decision?: string;
};

export type RecommendationsApiResponse = {
    final_recommendations?: RecommendationRow[];
    decision_traces?: DecisionTraceRow[];
};

export type DecisionTraceRow = Record<string, unknown> & {
    candidate_id?: string;
    candidate_name?: string;
    screening_score?: number;
    interview_score_scaled?: number;
    concerns_count?: number;
    weighted_score?: number;
    decision?: string;
    rule_applied?: string;
};
