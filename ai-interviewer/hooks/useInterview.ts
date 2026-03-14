// Interview Hook for managing interview state
import { useState, useEffect, useCallback } from 'react';
import interviewApi from '../lib/interviewApi';
import type { Interview, Question, Answer, Score } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export function useInterview(interviewId?: string) {
  const { user } = useAuth();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [score, setScore] = useState<Score | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);

  // Load interview data
  const loadInterview = useCallback(async () => {
    if (!interviewId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.get(interviewId);
      setInterview(data);
      setQuestions(data.interview_questions || []);
      setAnswers(data.interview_answers || []);
      if (data.interview_scores?.length) {
        setScore(data.interview_scores[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load interview');
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  // Start interview
  const startInterview = useCallback(async () => {
    if (!interviewId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.start(interviewId);
      setInterview(data);
      if (data.interview_questions?.length) {
        setCurrentQuestion(data.interview_questions[0]);
      }
      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to start interview');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  // Submit text answer
  const submitAnswer = useCallback(async (questionId: string, answerText: string) => {
    if (!interviewId) return;

    setLoading(true);
    setError(null);
    try {
      const answer = await interviewApi.submitAnswer(interviewId, questionId, answerText);
      setAnswers(prev => [...prev, answer]);

      // Get next question
      const nextQ = await interviewApi.getNextQuestion(interviewId);
      setCurrentQuestion(nextQ);

      return answer;
    } catch (err: any) {
      setError(err.message || 'Failed to submit answer');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  // Submit audio answer
  const submitAudioAnswer = useCallback(async (questionId: string, audioBlob: Blob) => {
    if (!interviewId) return;

    setIsRecording(true);
    setLoading(true);
    setError(null);
    try {
      const answer = await interviewApi.submitAudioAnswer(interviewId, questionId, audioBlob);
      setAnswers(prev => [...prev, answer]);

      // Get next question
      const nextQ = await interviewApi.getNextQuestion(interviewId);
      setCurrentQuestion(nextQ);

      return answer;
    } catch (err: any) {
      setError(err.message || 'Failed to submit audio answer');
      throw err;
    } finally {
      setIsRecording(false);
      setLoading(false);
    }
  }, [interviewId]);

  // Get next question
  const getNextQuestion = useCallback(async () => {
    if (!interviewId) return;

    try {
      const nextQ = await interviewApi.getNextQuestion(interviewId);
      setCurrentQuestion(nextQ);
      return nextQ;
    } catch (err: any) {
      setError(err.message || 'Failed to get next question');
      throw err;
    }
  }, [interviewId]);

  // Get score
  const getScore = useCallback(async () => {
    if (!interviewId) return;

    try {
      const scoreData = await interviewApi.getScore(interviewId);
      setScore(scoreData);
      return scoreData;
    } catch (err: any) {
      setError(err.message || 'Failed to get score');
      throw err;
    }
  }, [interviewId]);

  // Complete interview
  const completeInterview = useCallback(async () => {
    if (!interviewId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await interviewApi.complete(interviewId);
      setInterview(data);

      // Get final score
      const scoreData = await interviewApi.getScore(interviewId);
      setScore(scoreData);

      return data;
    } catch (err: any) {
      setError(err.message || 'Failed to complete interview');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [interviewId]);

  // Get interview state
  const getState = useCallback(async () => {
    if (!interviewId) return;

    try {
      return await interviewApi.getState(interviewId);
    } catch (err: any) {
      setError(err.message || 'Failed to get interview state');
      throw err;
    }
  }, [interviewId]);

  // Load interview on mount
  useEffect(() => {
    if (interviewId) {
      loadInterview();
    }
  }, [interviewId, loadInterview]);

  return {
    interview,
    questions,
    currentQuestion,
    answers,
    score,
    loading,
    error,
    isRecording,
    loadInterview,
    startInterview,
    submitAnswer,
    submitAudioAnswer,
    getNextQuestion,
    getScore,
    completeInterview,
    getState,
  };
}

export default useInterview;
