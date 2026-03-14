// Interview API Service
import { API_BASE_URL } from './api';
import type { Interview, Question, Answer, Score } from './api';

const getAuthHeaders = async () => {
  // Get token from AsyncStorage or secure storage
  const token = await getToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

const getToken = async (): Promise<string | null> => {
  // This should be implemented with secure storage
  // For now, return null - will be handled by the auth context
  return null;
};

// Interview API functions
export const interviewApi = {
  // List all interviews for current user
  list: async (candidateId?: string, jobId?: string): Promise<Interview[]> => {
    const headers = await getAuthHeaders();
    const params = new URLSearchParams();
    if (candidateId) params.append('candidate_id', candidateId);
    if (jobId) params.append('job_id', jobId);

    const response = await fetch(`${API_BASE_URL}/interviews?${params}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch interviews');
    }

    const result = await response.json();
    return result.data || [];
  },

  // Get single interview by ID
  get: async (interviewId: string): Promise<Interview> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch interview');
    }

    const result = await response.json();
    return result.data;
  },

  // Start an interview
  start: async (interviewId: string): Promise<Interview> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/start`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to start interview');
    }

    const result = await response.json();
    return result.data;
  },

  // Get all questions for an interview
  getQuestions: async (interviewId: string): Promise<Question[]> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/questions`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch questions');
    }

    const result = await response.json();
    return result.data || [];
  },

  // Get next question
  getNextQuestion: async (interviewId: string): Promise<Question | null> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/next`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch next question');
    }

    const result = await response.json();
    return result.data;
  },

  // Submit text answer
  submitAnswer: async (
    interviewId: string,
    questionId: string,
    answerText: string
  ): Promise<Answer> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/evaluate`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question_id: questionId,
        answer_text: answerText,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to submit answer');
    }

    const result = await response.json();
    return result.data.answer;
  },

  // Upload audio answer
  submitAudioAnswer: async (
    interviewId: string,
    questionId: string,
    audioBlob: Blob
  ): Promise<Answer> => {
    const headers = await getAuthHeaders();
    const formData = new FormData();
    formData.append('question_id', questionId);
    formData.append('audio', audioBlob, 'recording.webm');

    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/audio`, {
      method: 'POST',
      headers: {
        'Authorization': headers.Authorization,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to submit audio answer');
    }

    const result = await response.json();
    return result.data;
  },

  // Get interview score
  getScore: async (interviewId: string): Promise<Score> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/score`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch score');
    }

    const result = await response.json();
    return result.data;
  },

  // Get interview state
  getState: async (interviewId: string) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/state`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch interview state');
    }

    const result = await response.json();
    return result.data;
  },

  // Complete interview manually
  complete: async (interviewId: string): Promise<Interview> => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/complete`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to complete interview');
    }

    const result = await response.json();
    return result.data;
  },

  // Get transcript
  getTranscript: async (interviewId: string) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/transcript`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch transcript');
    }

    const result = await response.json();
    return result.data;
  },

  // Get interview report
  getReport: async (
    interviewId: string,
    reportType: 'candidate' | 'recruiter' = 'recruiter',
    includeTranscript: boolean = true
  ) => {
    const headers = await getAuthHeaders();
    const params = new URLSearchParams({
      report_type: reportType,
      include_transcript: includeTranscript.toString(),
    });

    const response = await fetch(`${API_BASE_URL}/interviews/${interviewId}/report?${params}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to fetch report');
    }

    const result = await response.json();
    return result.data;
  },
};

export default interviewApi;
