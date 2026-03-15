/**
 * Centralized API Client
 * Handles authentication, retry logic, and error handling
 */

import { supabase } from './api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_TIMEOUT = 30000;
const MAX_RETRIES = 3;

export interface ApiClientConfig {
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

class ApiClient {
  private baseUrl: string;
  private timeout: number;
  private maxRetries: number;

  constructor(config: ApiClientConfig = {}) {
    this.baseUrl = config.baseUrl || API_BASE_URL;
    this.timeout = config.timeout || API_TIMEOUT;
    this.maxRetries = config.maxRetries || MAX_RETRIES;
  }

  /**
   * Get authentication token from Supabase session
   */
  private async getToken(): Promise<string | null> {
    try {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token || null;
    } catch (error) {
      console.error('Error getting session:', error);
      return null;
    }
  }

  /**
   * Refresh authentication token
   */
  private async refreshToken(): Promise<void> {
    try {
      const { error } = await supabase.auth.refreshSession();
      if (error) {
        console.error('Token refresh failed:', error);
        throw error;
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  }

  /**
   * Check if error is a network error
   */
  private isNetworkError(error: any): boolean {
    return !error.response && !error.status;
  }

  /**
   * Delay utility for retry backoff
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Make API request with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    const token = await this.getToken();

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      // Handle 401 Unauthorized - try to refresh token
      if (response.status === 401 && retryCount < this.maxRetries) {
        try {
          await this.refreshToken();
          return this.request(endpoint, options, retryCount + 1);
        } catch (refreshError) {
          // Token refresh failed, clear session
          await supabase.auth.signOut();
          throw new Error('Session expired. Please log in again.');
        }
      }

      // Handle other error responses
      if (!response.ok) {
        let errorMessage = `API Error: ${response.status}`;

        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          // Response is not JSON
        }

        throw new Error(errorMessage);
      }

      // Parse JSON response
      const data = await response.json();

      // Handle API response wrapper format
      if (data.data !== undefined) {
        return data.data as T;
      }

      return data as T;

    } catch (error: any) {
      clearTimeout(timeoutId);

      // Handle abort timeout
      if (error.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }

      // Handle network errors with retry
      if (this.isNetworkError(error) && retryCount < this.maxRetries) {
        const backoffTime = Math.pow(2, retryCount) * 1000;
        console.log(`Network error, retrying in ${backoffTime}ms...`);
        await this.delay(backoffTime);
        return this.request(endpoint, options, retryCount + 1);
      }

      // Re-throw original error
      throw error;
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }
    return this.request<T>(url, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * Upload file with progress
   */
  async uploadFile<T>(
    endpoint: string,
    file: Blob | FormData,
    fileName: string,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const token = await this.getToken();

    const formData = new FormData();
    if (file instanceof Blob) {
      formData.append('file', file, fileName);
    } else {
      formData.append('file', file as any);
    }

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data.data || data);
          } catch {
            resolve(xhr.responseText as any);
          }
        } else {
          reject(new Error(`Upload failed: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed: Network error'));
      });

      xhr.open('POST', `${this.baseUrl}${endpoint}`);
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.send(formData);
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom configurations
export { ApiClient };
