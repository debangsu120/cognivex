export interface Interview {
  id: string;
  company: string;
  role: string;
  status: "applied" | "interview" | "pending" | "passed" | "failed" | "closed";
  stage: number;
  totalStages: number;
  deadline?: string;
  scheduledDate?: string;
  score?: number;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role?: string;
  avatar_url?: string;
  created_at?: string;
}

export interface Candidate {
  id: string;
  name: string;
  role: string;
  avatar?: string;
  score: number;
  status: "shortlisted" | "in_review" | "interview" | "rejected";
  stage: number;
}

export interface Skill {
  name: string;
  level: number;
}

export interface Question {
  id: string;
  question: string;
  answer?: string;
}

export interface InterviewResult {
  id: string;
  totalScore: number;
  skills: Skill[];
  questions: Question[];
  insight: string;
}
