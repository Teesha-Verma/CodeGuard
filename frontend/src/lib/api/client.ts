import { ReviewReport, ReviewStatusResponse } from '@/types';

export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) ||
  'http://localhost:8000';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export type ReviewFetchResult =
  | { status: 'completed'; report: ReviewReport }
  | { status: 'running'; message?: string }
  | { status: 'failed'; error: string }
  | { status: 'not_found'; error: string };

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  public setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  async checkHealth(): Promise<HealthResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    try {
      const res = await fetch(`${this.baseUrl}/health`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' },
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        throw new Error(`Health check failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      const message = err instanceof Error ? err.message : 'Backend unreachable';
      throw new Error(message);
    }
  }

  async submitPrReview(repoUrl: string, prNumber: number): Promise<ReviewStatusResponse> {
    const res = await fetch(`${this.baseUrl}/review/pr`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        repo_url: repoUrl,
        pr_number: Number(prNumber),
      }),
    });

    if (!res.ok) {
      let detail = 'Failed to submit pull request review';
      try {
        const errorData = await res.json();
        if (errorData.detail) detail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } catch {
        // use default error message
      }
      throw new Error(detail);
    }

    return await res.json();
  }

  async submitSnippetReview(code: string, language: string = 'python', filename: string = 'snippet.py'): Promise<ReviewStatusResponse> {
    const res = await fetch(`${this.baseUrl}/review/snippet`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        code,
        language,
        filename,
      }),
    });

    if (!res.ok) {
      let detail = 'Failed to submit snippet review';
      try {
        const errorData = await res.json();
        if (errorData.detail) detail = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      } catch {
        // use default error message
      }
      throw new Error(detail);
    }

    return await res.json();
  }

  async getReview(reviewId: string): Promise<ReviewFetchResult> {
    try {
      const res = await fetch(`${this.baseUrl}/review/${encodeURIComponent(reviewId)}`, {
        headers: { 'Accept': 'application/json' },
      });

      if (res.status === 200) {
        const report: ReviewReport = await res.json();
        return { status: 'completed', report };
      }

      if (res.status === 202) {
        let msg = 'Review is still processing.';
        try {
          const body = await res.json();
          if (body.detail) msg = body.detail;
        } catch {
          // fallback msg
        }
        return { status: 'running', message: msg };
      }

      if (res.status === 404) {
        return { status: 'not_found', error: 'Review not found on backend.' };
      }

      if (res.status === 500) {
        let detail = 'Review pipeline execution encountered an error.';
        try {
          const body = await res.json();
          if (body.detail) detail = body.detail;
        } catch {
          // fallback detail
        }
        return { status: 'failed', error: detail };
      }

      return { status: 'failed', error: `Unexpected backend response status: ${res.status}` };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Network error communicating with backend';
      return { status: 'failed', error: message };
    }
  }
}

export const apiClient = new ApiClient();
