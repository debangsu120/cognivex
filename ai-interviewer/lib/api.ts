// API Configuration for CogniVex
import { createClient } from '@supabase/supabase-js';

// Supabase configuration - Replace with your actual Supabase credentials
export const SUPABASE_URL = 'https://eueojlhqdrcuzpkndwye.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1ZW9qbGhxZHJjdXpwa25kd3llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxNjMxNjEsImV4cCI6MjA4ODczOTE2MX0.8Q-MwPEzwtje8vog1LwWADsPkzT3vhoND3YPraqTkFc';

// API Base URL for FastAPI backend
export const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create Supabase client
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// API Response types
export interface APIResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// Interview types
export interface Interview {
  id: string;
  job_id: string;
  candidate_id: string;
  created_by: string;
  status: 'created' | 'ready' | 'in_progress' | 'completed' | 'timeout' | 'cancelled';
  difficulty: string;
  duration_minutes: number;
  max_questions: number;
  current_question_index: number;
  started_at: string | null;
  completed_at: string | null;
  jobs?: Job;
  interview_questions?: Question[];
  interview_answers?: Answer[];
  interview_scores?: Score[];
}

export interface Job {
  id: string;
  company_id: string;
  title: string;
  description: string;
  skills_required: string[];
  experience_level: string;
  location: string;
  job_type: string;
  status: string;
  companies?: Company;
}

export interface Company {
  id: string;
  name: string;
  logo_url?: string;
}

export interface Question {
  id: string;
  interview_id: string;
  question_text: string;
  question_order: number;
  skill?: string;
  category: string;
  difficulty: string;
  time_limit_seconds: number;
}

export interface Answer {
  id: string;
  question_id: string;
  answer_text?: string;
  audio_url?: string;
  transcript?: string;
  score: number;
  feedback: string;
  technical_accuracy?: number;
  communication_clarity?: number;
  interview_questions?: Question;
}

export interface Score {
  id: string;
  interview_id: string;
  overall_score: number;
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  cultural_fit_score: number;
  strengths: string[];
  weaknesses: string[];
  summary: string;
  recommendation: string;
}

// User types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'candidate' | 'recruiter' | 'admin';
  avatar_url?: string;
  created_at: string;
}

// Resume types
export interface Resume {
  id: string;
  user_id: string;
  file_url: string;
  extracted_skills: string[];
  experience_years: number;
  education: string[];
  summary?: string;
  parsed_data?: any;
  created_at: string;
}

// Dashboard types
export interface DashboardStats {
  total_interviews: number;
  completed_interviews: number;
  pending_interviews: number;
  average_score?: number;
  total_applications: number;
  shortlisted: number;
}

export interface CandidateStats {
  total_candidates: number;
  interviewed: number;
  shortlisted: number;
  rejected: number;
}
