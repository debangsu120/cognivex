// Interview API Service
import { apiClient } from './apiClient';
import { supabase } from './api';
import type { Interview, Question, Answer, Score } from './api';

// Interview API functions using centralized API client
export const interviewApi = {
  // List all interviews for current user
  list: async (candidateId?: string, jobId?: string): Promise<Interview[]> => {
    const params: Record<string, string> = {};
    if (candidateId) params.candidate_id = candidateId;
    if (jobId) params.job_id = jobId;

    return apiClient.get<Interview[]>('/interviews', params);
  },

  // Get single interview by ID
  get: async (interviewId: string): Promise<Interview> => {
    return apiClient.get<Interview>(`/interviews/${interviewId}`);
  },

  // Start an interview
  start: async (interviewId: string): Promise<Interview> => {
    return apiClient.post<Interview>(`/interviews/${interviewId}/start`);
  },

  // Get all questions for an interview
  getQuestions: async (interviewId: string): Promise<Question[]> => {
    return apiClient.get<Question[]>(`/interviews/${interviewId}/questions`);
  },

  // Get next question
  getNextQuestion: async (interviewId: string): Promise<Question | null> => {
    return apiClient.get<Question | null>(`/interviews/${interviewId}/next`);
  },

  // Submit text answer
  submitAnswer: async (
    interviewId: string,
    questionId: string,
    answerText: string
  ): Promise<any> => {
    return apiClient.post<any>(`/interviews/${interviewId}/evaluate`, {
      question_id: questionId,
      answer_text: answerText,
    });
  },

  // Upload audio answer (using FormData for file upload)
  submitAudioAnswer: async (
    interviewId: string,
    questionId: string,
    audioUri: string
  ): Promise<any> => {
    // Create form data for file upload
    const formData = new FormData();
    formData.append('question_id', questionId);

    // Append audio file
    const filename = audioUri.split('/').pop() || 'recording.m4a';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `audio/${match[1]}` : 'audio/m4a';

    formData.append('audio', {
      uri: audioUri,
      name: filename,
      type,
    } as any);

    // Use fetch directly for multipart form data
    const token = await getToken();
    const response = await fetch(`http://localhost:8000/api/v1/interviews/${interviewId}/audio`, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
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
    return apiClient.get<Score>(`/interviews/${interviewId}/score`);
  },

  // Get interview state
  getState: async (interviewId: string): Promise<any> => {
    return apiClient.get<any>(`/interviews/${interviewId}/state`);
  },

  // Complete interview manually
  complete: async (interviewId: string): Promise<Interview> => {
    return apiClient.post<Interview>(`/interviews/${interviewId}/complete`);
  },

  // Get transcript
  getTranscript: async (interviewId: string): Promise<any> => {
    return apiClient.get<any>(`/interviews/${interviewId}/transcript`);
  },

  // Get interview report
  getReport: async (
    interviewId: string,
    reportType: 'candidate' | 'recruiter' = 'recruiter',
    includeTranscript: boolean = true
  ): Promise<any> => {
    return apiClient.get<any>(`/interviews/${interviewId}/report`, {
      report_type: reportType,
      include_transcript: includeTranscript.toString(),
    });
  },

  // Get detailed evaluation
  getDetailedEvaluation: async (
    interviewId: string,
    questionId: string
  ): Promise<any> => {
    return apiClient.get<any>(`/interviews/${interviewId}/evaluate/detailed`, {
      question_id: questionId,
    });
  },

  // Get skill aggregates
  getSkillAggregates: async (interviewId: string): Promise<any> => {
    return apiClient.get<any>(`/interviews/${interviewId}/skills/aggregate`);
  },

  // Get comprehensive report
  getComprehensiveReport: async (
    interviewId: string,
    candidateName: string = 'Candidate'
  ): Promise<any> => {
    return apiClient.post<any>(`/interviews/${interviewId}/report/comprehensive`, {
      candidate_name: candidateName,
    });
  },
};

// Helper to get token for audio upload
async function getToken(): Promise<string | null> {
  try {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token || null;
  } catch {
    return null;
  }
}

export default interviewApi;
