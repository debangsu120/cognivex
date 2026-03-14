// Dashboard API and hooks
import { API_BASE_URL } from '../lib/api';
import type { DashboardStats, CandidateStats, Job, Resume } from '../lib/api';

const getAuthHeaders = async () => {
  // This should get token from secure storage
  return {
    'Content-Type': 'application/json',
  };
};

// Dashboard API
export const dashboardApi = {
  // Get candidate dashboard
  getCandidateDashboard: async (): Promise<DashboardStats> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/dashboard/candidate`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard');
    }

    const result = await response.json();
    return result.data;
  },

  // Get recruiter dashboard
  getRecruiterDashboard: async (companyId: string): Promise<{
    stats: CandidateStats;
    recent_interviews: any[];
  }> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/dashboard/recruiter?company_id=${companyId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard');
    }

    const result = await response.json();
    return result.data;
  },

  // Get job recommendations for candidate
  getJobRecommendations: async (candidateId: string): Promise<Job[]> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/jobs/recommendations?candidate_id=${candidateId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch recommendations');
    }

    const result = await response.json();
    return result.data || [];
  },

  // Get all available jobs
  getJobs: async (filters?: {
    company_id?: string;
    status?: string;
    search?: string;
  }): Promise<Job[]> => {
    const headers = await getAuthHeaders();
    const params = new URLSearchParams();
    if (filters?.company_id) params.append('company_id', filters.company_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.search) params.append('search', filters.search);

    const response = await fetch(`${API_BASE_URL}/jobs?${params}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch jobs');
    }

    const result = await response.json();
    return result.data || [];
  },

  // Apply for a job
  applyForJob: async (jobId: string, candidateId: string): Promise<any> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/apply`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ candidate_id: candidateId }),
    });

    if (!response.ok) {
      throw new Error('Failed to apply for job');
    }

    const result = await response.json();
    return result.data;
  },
};

// Resume API
export const resumeApi = {
  // Get candidate's resume
  getResume: async (userId: string): Promise<Resume | null> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/resume/${userId}`, {
      method: 'GET',
      headers,
    });

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      throw new Error('Failed to fetch resume');
    }

    const result = await response.json();
    return result.data;
  },

  // Upload and parse resume
  uploadResume: async (userId: string, file: File): Promise<Resume> => {
    const headers = await getAuthHeaders();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/resume/upload?user_id=${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': headers.Authorization,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload resume');
    }

    const result = await response.json();
    return result.data;
  },
};

// Hook for candidate dashboard
export function useCandidateDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async (userId: string) => {
    setLoading(true);
    setError(null);

    try {
      const [statsData, jobsData, resumeData] = await Promise.all([
        dashboardApi.getCandidateDashboard(),
        dashboardApi.getJobRecommendations(userId),
        resumeApi.getResume(userId),
      ]);

      setStats(statsData);
      setJobs(jobsData);
      setResume(resumeData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  return {
    stats,
    jobs,
    resume,
    loading,
    error,
    fetchDashboard,
  };
}

// Hook for recruiter dashboard
export function useRecruiterDashboard(companyId: string) {
  const [stats, setStats] = useState<CandidateStats | null>(null);
  const [recentInterviews, setRecentInterviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    if (!companyId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await dashboardApi.getRecruiterDashboard(companyId);
      setStats(data.stats);
      setRecentInterviews(data.recent_interviews);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  return {
    stats,
    recentInterviews,
    loading,
    error,
    fetchDashboard,
  };
}
