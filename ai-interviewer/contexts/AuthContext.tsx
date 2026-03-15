// Authentication Context for CogniVex
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { supabase } from '../lib/api';
import type { User } from '../lib/api';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  session: any | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string, role: 'candidate' | 'recruiter') => Promise<void>;
  signOut: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  refreshSession: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Get access token for API calls
  const getAccessToken = async (): Promise<string | null> => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      return session?.access_token || null;
    } catch (error) {
      console.error('Error getting access token:', error);
      return null;
    }
  };

  // Refresh session
  const refreshSession = async (): Promise<void> => {
    try {
      const { data, error } = await supabase.auth.refreshSession();
      if (error) throw error;
      if (data.session) {
        setSession(data.session);
      }
    } catch (error) {
      console.error('Error refreshing session:', error);
      throw error;
    }
  };

  useEffect(() => {
    // Check current session
    const checkSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.user) {
          // Fetch user profile
          const { data: profile } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', session.user.id)
            .single();

          if (profile) {
            setUser({
              id: profile.id,
              email: session.user.email || '',
              full_name: profile.full_name,
              role: profile.role,
              avatar_url: profile.avatar_url,
              created_at: profile.created_at,
            });
          }
        }
      } catch (error) {
        console.error('Error checking session:', error);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      setSession(session);

      if (session?.user) {
        const { data: profile } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', session.user.id)
          .single();

        if (profile) {
          setUser({
            id: profile.id,
            email: session.user.email || '',
            full_name: profile.full_name,
            role: profile.role,
            avatar_url: profile.avatar_url,
            created_at: profile.created_at,
          });
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    if (data.user) {
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', data.user.id)
        .single();

      if (profile) {
        setUser({
          id: profile.id,
          email: data.user.email || '',
          full_name: profile.full_name,
          role: profile.role,
          avatar_url: profile.avatar_url,
          created_at: profile.created_at,
        });
      }
    }
  };

  const signUp = async (
    email: string,
    password: string,
    fullName: string,
    role: 'candidate' | 'recruiter'
  ) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
          role,
        },
      },
    });

    if (error) throw error;

    if (data.user) {
      // Create profile
      await supabase.from('profiles').insert({
        id: data.user.id,
        email,
        full_name: fullName,
        role,
      });

      setUser({
        id: data.user.id,
        email,
        full_name: fullName,
        role,
        created_at: new Date().toISOString(),
      });
    }
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    setUser(null);
  };

  const updateProfile = async (updates: Partial<User>) => {
    if (!user) throw new Error('No user logged in');

    const { error } = await supabase
      .from('profiles')
      .update(updates)
      .eq('id', user.id);

    if (error) throw error;

    setUser({ ...user, ...updates });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        session,
        signIn,
        signUp,
        signOut,
        updateProfile,
        refreshSession,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
