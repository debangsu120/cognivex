/**
 * Recruiter Hook - Phase 4 & 6
 * Provides hooks for recruiter-specific operations with centralized API client
 */

import { useState, useCallback } from 'react';
import { apiClient } from '../lib/apiClient';
import type { JobWithStats, RankedCandidate, CandidateReport, JobAnalytics, RecruiterDashboard } from '../lib/api';

/**
 * Hook for recruiter dashboard data
 */
export function useRecruiterDashboard() {
  const [dashboard, setDashboard] = useState<RecruiterDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<RecruiterDashboard>('/recruiter/dashboard');
      setDashboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  return { dashboard, loading, error, fetchDashboard };
}

/**
 * Hook for recruiter jobs with stats
 */
export function useRecruiterJobs() {
  const [jobs, setJobs] = useState<JobWithStats[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async (companyId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const params = companyId ? { company_id: companyId } : undefined;
      const data = await apiClient.get<JobWithStats[]>('/recruiter/jobs', params);
      setJobs(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  }, []);

  return { jobs, loading, error, fetchJobs };
}

/**
 * Hook for ranked candidates for a job
 */
export function useJobCandidates(jobId: string) {
  const [candidates, setCandidates] = useState<RankedCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCandidates = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<{ job_id: string; candidates: RankedCandidate[] }>(
        `/recruiter/jobs/${jobId}/candidates/ranked`
      );
      setCandidates(data?.candidates || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch candidates');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  return { candidates, loading, error, fetchCandidates };
}

/**
 * Hook for candidate report
 */
export function useCandidateReport(interviewId: string) {
  const [report, setReport] = useState<CandidateReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    if (!interviewId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<CandidateReport>(
        `/recruiter/candidates/${interviewId}/report`
      );
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report');
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  return { report, loading, error, fetchReport };
}

/**
 * Hook for job analytics
 */
export function useJobAnalytics(jobId: string) {
  const [analytics, setAnalytics] = useState<JobAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<JobAnalytics>(
        `/recruiter/jobs/${jobId}/analytics`
      );
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  return { analytics, loading, error, fetchAnalytics };
}

/**
 * Hook for shortlisting candidates
 */
export function useShortlistCandidate() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateStatus = useCallback(async (
    interviewId: string,
    status: 'pending' | 'shortlisted' | 'rejected' | 'offered'
  ) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.post<{ id: string; candidate_status: string }>(
        `/recruiter/candidates/${interviewId}/status?status=${status}`
      );
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update status';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const shortlist = useCallback(
    (interviewId: string) => updateStatus(interviewId, 'shortlisted'),
    [updateStatus]
  );

  const reject = useCallback(
    (interviewId: string) => updateStatus(interviewId, 'rejected'),
    [updateStatus]
  );

  const offer = useCallback(
    (interviewId: string) => updateStatus(interviewId, 'offered'),
    [updateStatus]
  );

  return { shortlist, reject, offer, loading, error };
}

/**
 * Hook for overview analytics
 */
export function useOverviewAnalytics() {
  const [analytics, setAnalytics] = useState<{
    total_candidates: number;
    total_completed_interviews: number;
    average_score: number | null;
    candidates_by_status: Record<string, number>;
    jobs_count: number;
    active_jobs: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<any>('/recruiter/analytics/overview');
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  return { analytics, loading, error, fetchAnalytics };
}
