// Hook for fetching interview list
import { useState, useEffect, useCallback } from 'react';
import interviewApi from '../lib/interviewApi';
import type { Interview } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export function useInterviews() {
  const { user } = useAuth();
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInterviews = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.list(user.id);
      setInterviews(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch interviews');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchInterviews();
  }, [fetchInterviews]);

  // Filter helpers
  const pendingInterviews = interviews.filter(i => i.status === 'ready' || i.status === 'created');
  const inProgressInterviews = interviews.filter(i => i.status === 'in_progress');
  const completedInterviews = interviews.filter(i => i.status === 'completed');

  return {
    interviews,
    pendingInterviews,
    inProgressInterviews,
    completedInterviews,
    loading,
    error,
    refetch: fetchInterviews,
  };
}

export function useInterviewDetails(interviewId: string) {
  const [interview, setInterview] = useState<Interview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInterview = useCallback(async () => {
    if (!interviewId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.get(interviewId);
      setInterview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch interview');
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  useEffect(() => {
    fetchInterview();
  }, [fetchInterview]);

  return {
    interview,
    loading,
    error,
    refetch: fetchInterview,
  };
}

export default useInterviews;
