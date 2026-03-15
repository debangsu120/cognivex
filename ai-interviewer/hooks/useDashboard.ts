// Dashboard API and hooks
import { useState, useCallback } from 'react';
import { apiClient } from '../lib/apiClient';
import { supabase } from '../lib/api';
import type { DashboardStats, CandidateStats, Job, Resume } from '../lib/api';

// Job recommendation type
export interface JobRecommendation {
  job: Job;
  job_id: string;
  job_title: string;
  company_name: string;
  match_score: number;
  skills_match_score: number;
  experience_match_score: number;
  matched_skills: string[];
  missing_skills: string[];
}

// Dashboard API using centralized client
export const dashboardApi = {
  // Get candidate dashboard
  getCandidateDashboard: async (): Promise<DashboardStats> => {
    return apiClient.get<DashboardStats>('/dashboard/candidate');
  },

  // Get recruiter dashboard
  getRecruiterDashboard: async (companyId?: string): Promise<any> => {
    const params = companyId ? { company_id: companyId } : undefined;
    return apiClient.get<any>('/recruiter/dashboard', params);
  },

  // Get job recommendations for current user
  getJobRecommendations: async (limit: number = 10, useAi: boolean = false): Promise<JobRecommendation[]> => {
    return apiClient.get<JobRecommendation[]>('/jobs/recommendations/for-me', {
      limit: limit.toString(),
      use_ai: useAi.toString(),
    });
  },

  // Get all available jobs
  getJobs: async (filters?: {
    company_id?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<Job[]> => {
    const params: Record<string, string> = {};
    if (filters?.company_id) params.company_id = filters.company_id;
    if (filters?.is_active !== undefined) params.is_active = filters.is_active.toString();
    if (filters?.page) params.page = filters.page.toString();
    if (filters?.page_size) params.page_size = filters.page_size.toString();

    return apiClient.get<Job[]>('/jobs', params);
  },

  // Get single job
  getJob: async (jobId: string): Promise<Job> => {
    return apiClient.get<Job>(`/jobs/${jobId}`);
  },
};

// Resume API using centralized client
export const resumeApi = {
  // Get current user's resumes
  listResumes: async (): Promise<Resume[]> => {
    return apiClient.get<Resume[]>('/resume');
  },

  // Get single resume
  getResume: async (resumeId: string): Promise<Resume | null> => {
    try {
      return await apiClient.get<Resume>(`/resume/${resumeId}`);
    } catch (error: any) {
      if (error.message?.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  // Upload and parse resume
  uploadResume: async (file: File): Promise<Resume> => {
    const { data: { session } } = await supabase.auth.getSession();

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Use fetch for multipart upload
    const token = session?.access_token;
    const response = await fetch('http://localhost:8000/api/v1/resume/upload', {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload resume');
    }

    const result = await response.json();
    return result.data;
  },

  // Delete resume
  deleteResume: async (resumeId: string): Promise<void> => {
    return apiClient.delete<void>(`/resume/${resumeId}`);
  },
};

// Hook for candidate dashboard
export function useCandidateDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch in parallel
      const [jobsData, resumes] = await Promise.all([
        dashboardApi.getJobRecommendations(10, false).catch(err => {
          console.log('Job recommendations error:', err.message);
          return [];
        }),
        resumeApi.listResumes().catch(err => {
          console.log('Resumes error:', err.message);
          return [];
        }),
      ]);

      setJobs(jobsData || []);
      if (resumes?.length > 0) {
        setResume(resumes[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await fetchDashboard();
  }, [fetchDashboard]);

  return {
    stats,
    jobs,
    resume,
    loading,
    error,
    fetchDashboard,
    refresh,
  };
}

// Hook for recruiter dashboard
export function useRecruiterDashboard(companyId?: string) {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch dashboard and jobs in parallel
      const [dashboard, jobsData] = await Promise.all([
        dashboardApi.getRecruiterDashboard(companyId).catch(err => {
          console.log('Dashboard error:', err.message);
          return null;
        }),
        apiClient.get<any[]>('/recruiter/jobs').catch(err => {
          console.log('Jobs error:', err.message);
          return [];
        }),
      ]);

      setDashboardData(dashboard);
      setJobs(jobsData || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  const refresh = useCallback(async () => {
    await fetchDashboard();
  }, [fetchDashboard]);

  return {
    dashboard: dashboardData,
    jobs,
    loading,
    error,
    fetchDashboard,
    refresh,
  };
}
