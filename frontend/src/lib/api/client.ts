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

  async getReviewStatus(reviewId: string, signal?: AbortSignal): Promise<ReviewStatusResponse> {
    const res = await fetch(`${this.baseUrl}/review/${encodeURIComponent(reviewId)}/status`, {
      headers: { 'Accept': 'application/json' },
      signal,
    });

    if (res.status === 404) {
      return { review_id: reviewId, status: 'not_found', message: 'Review not found.' };
    }

    if (!res.ok) {
      throw new Error(`Failed to fetch review status (${res.status})`);
    }

    return await res.json();
  }

  async getReview(reviewId: string, signal?: AbortSignal): Promise<ReviewFetchResult> {
    try {
      const res = await fetch(`${this.baseUrl}/review/${encodeURIComponent(reviewId)}`, {
        headers: { 'Accept': 'application/json' },
        signal,
      });

      if (res.status === 200) {
        const body = await res.json();
        if (body.status === 'failed') {
          return {
            status: 'failed',
            error: body.error_message || body.message || 'Review pipeline failed during execution.',
          };
        }
        if (body.status === 'timed_out') {
          return {
            status: 'failed',
            error: body.error_message || body.message || 'Review execution timed out.',
          };
        }
        return { status: 'completed', report: body as ReviewReport };
      }

      if (res.status === 202) {
        let msg = 'Review is still processing.';
        try {
          const body = await res.json();
          if (body.detail) msg = body.detail;
          else if (body.message) msg = body.message;
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
          else if (body.error_message) detail = body.error_message;
        } catch {
          // fallback detail
        }
        return { status: 'failed', error: detail };
      }

      return { status: 'failed', error: `Unexpected backend response status: ${res.status}` };
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw err;
      }
      const message = err instanceof Error ? err.message : 'Network error communicating with backend';
      return { status: 'failed', error: message };
    }
  }

  async listReviews(
    limit: number = 50,
    offset: number = 0,
    status?: string,
    search?: string
  ): Promise<ReviewHistoryResponse> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    const res = await fetch(`${this.baseUrl}/review?${params.toString()}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to list reviews: status ${res.status}`);
    }
    return await res.json();
  }

  async getDashboardStats(): Promise<DashboardStatsResponse> {
    const res = await fetch(`${this.baseUrl}/review/summary/stats`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to get dashboard stats: status ${res.status}`);
    }
    return await res.json();
  }

  async deleteReview(reviewId: string): Promise<boolean> {
    const res = await fetch(`${this.baseUrl}/review/${encodeURIComponent(reviewId)}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' },
    });
    return res.ok;
  }

  async getFindingDataflow(reviewId: string, line: number): Promise<DataflowResponse> {
    const res = await fetch(
      `${this.baseUrl}/review/${encodeURIComponent(reviewId)}/findings/${line}/dataflow`,
      {
        headers: { 'Accept': 'application/json' },
      }
    );
    if (!res.ok) {
      throw new Error(`Failed to fetch dataflow: status ${res.status}`);
    }
    return await res.json();
  }

  async testPlayground(req: PlaygroundReviewRequest): Promise<PlaygroundReviewResponse> {
    const res = await fetch(`${this.baseUrl}/review/playground`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      throw new Error(`Playground analysis failed with status ${res.status}`);
    }
    return await res.json();
  }

  async learnFinding(req: LearnerFindingRequest): Promise<LearnerFindingResponse> {
    const res = await fetch(`${this.baseUrl}/learn/finding`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      throw new Error(`Failed to generate learning content: status ${res.status}`);
    }
    return await res.json();
  }

  async chatAssistant(req: AssistantChatRequest): Promise<AssistantChatResponse> {
    const res = await fetch(`${this.baseUrl}/assistant/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      throw new Error(`Assistant query failed with status ${res.status}`);
    }
    return await res.json();
  }

  async getSecurityHealth(): Promise<SecurityHealthResponse> {
    const res = await fetch(`${this.baseUrl}/security/health`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch security health: status ${res.status}`);
    }
    return await res.json();
  }

  async getRiskReport(): Promise<RepositoryRiskResponse> {
    const res = await fetch(`${this.baseUrl}/security/risk`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch risk report: status ${res.status}`);
    }
    return await res.json();
  }

  async getKnowledgeTopics(
    categoryOrOpts?: string | { category?: string; query?: string; search?: string },
    search?: string
  ): Promise<KnowledgeTopicSummary[]> {
    let cat: string | undefined;
    let q: string | undefined;

    if (typeof categoryOrOpts === 'object' && categoryOrOpts !== null) {
      cat = categoryOrOpts.category;
      q = categoryOrOpts.query || categoryOrOpts.search;
    } else {
      cat = categoryOrOpts;
      q = search;
    }

    const params = new URLSearchParams();
    if (cat && cat !== 'ALL') params.append('category', cat);
    if (q) params.append('search', q);

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${this.baseUrl}/knowledge/topics${qs}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch knowledge topics: status ${res.status}`);
    }
    return await res.json();
  }

  async getKnowledgeTopic(topicId: string): Promise<KnowledgeTopicDetail> {
    const res = await fetch(`${this.baseUrl}/knowledge/topics/${encodeURIComponent(topicId)}`, {
      headers: { 'Accept': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch topic details: status ${res.status}`);
    }
    return await res.json();
  }
}

// Typed schemas matching backend responses
export interface StoredReviewSummary {
  review_id: string;
  type: 'pr' | 'snippet';
  repo_url?: string;
  pr_number?: number;
  filename?: string;
  language?: string;
  status: string;
  created_at: string;
  duration_seconds?: number;
  total_issues: number;
  critical_issues: number;
  high_issues: number;
}

export interface ReviewHistoryResponse {
  reviews: StoredReviewSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface DashboardStatsResponse {
  total_reviews: number;
  completed_reviews: number;
  total_issues_found: number;
  total_issues?: number;
  critical_high_issues: number;
  critical_count?: number;
  recent_reviews: StoredReviewSummary[];
}

export interface DataflowNode {
  id: string;
  step_number: number;
  label: string;
  role: 'SOURCE' | 'INPUT' | 'PROPAGATION' | 'TRANSFORMATION' | 'SINK' | string;
  description: string;
  code_snippet: string;
  line?: number;
  file_path?: string;
  symbol?: string;
  operation?: string;
  file?: string;
}

export interface DataflowResponse {
  review_id: string;
  file_path?: string;
  line?: number;
  has_dataflow?: boolean;
  available?: boolean;
  nodes: DataflowNode[];
  message?: string;
}

export interface PlaygroundReviewRequest {
  code: string;
  language?: string;
  filename?: string;
  original_issue_category?: string;
  original_issue_line?: number;
  original_finding_line?: number;
}

export interface PlaygroundReviewResponse {
  status: 'resolved' | 'still_detected' | 'error' | string;
  resolved: boolean;
  is_resolved?: boolean;
  total_issues?: number;
  message: string;
  findings: any[];
  summary_stats: Record<string, unknown>;
}

export interface QuizModel {
  question: string;
  options: string[];
  correct_option: number;
  correct_index?: number;
  explanation: string;
}

export interface LearnerFindingRequest {
  review_id?: string;
  file_path: string;
  line: number;
  finding_line?: number;
  issue_text?: string;
  category?: string;
  code_snippet?: string;
}

export interface LearnerFindingResponse {
  concept_title: string;
  concept?: string;
  cwe: string;
  owasp: string;
  concept_summary: string;
  why_it_matters: string;
  what_happened_in_code: string;
  what_happened?: string;
  impact: string;
  evidence_breakdown: string;
  evidence?: string;
  detection_sources: string[];
  how_to_fix: string;
  good_code: string;
  safer_implementation?: string;
  bad_code: string;
  key_takeaway?: string;
  key_takeaways?: string[];
  quiz: QuizModel;
  standards?: string[];
}

export interface AssistantMessage {
  role: 'user' | 'assistant' | 'system' | string;
  content: string;
  context_pill?: string;
}

export interface AssistantChatRequest {
  messages: AssistantMessage[];
  review_id?: string;
  file_path?: string;
  line?: number;
  finding_line?: number;
  query?: string;
  context?: string;
}

export interface AssistantChatResponse {
  message: string;
  reply?: string;
  provider: string;
  model: string;
  fallback_used: boolean;
  trace_id: string;
  context_used?: string;
}

export interface SecurityHealthResponse {
  security_score: number;
  score?: number;
  health_score?: number;
  grade: string;
  health_grade?: string;
  total_reviews: number;
  total_issues: number;
  critical_count: number;
  critical_issues?: number;
  high_count: number;
  high_issues?: number;
  medium_count: number;
  medium_issues?: number;
  low_count: number;
  low_issues?: number;
  style_count: number;
  style_issues?: number;
  llm_reasoned_count?: number;
  static_reasoned_count?: number;
  categories: Record<string, number>;
  category_breakdown?: Record<string, number>;
  score_breakdown?: Record<string, unknown>;
  formula?: string;
  formula_explanation?: string;
}

export interface FileRiskItem {
  file_path: string;
  repo_url?: string;
  pr_number?: number;
  critical: number;
  critical_count?: number;
  high: number;
  high_count?: number;
  medium: number;
  medium_count?: number;
  low: number;
  low_count?: number;
  total: number;
  total_count?: number;
  risk_score: number;
  risk_tier: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  complexity: string;
  fan_in: number;
  fan_out: number;
  categories: string[];
}

export interface RepositoryRiskResponse {
  overall_risk: 'critical' | 'high' | 'medium' | 'low' | string;
  ranked_files: FileRiskItem[];
  top_categories: Record<string, number>;
  formula?: string;
  files?: FileRiskItem[];
  high_risk_count?: number;
  medium_risk_count?: number;
  low_risk_count?: number;
}

export interface KnowledgeTopicSummary {
  id: string;
  cwe: string;
  owasp: string;
  title: string;
  category: string;
  severity: string;
  summary: string;
}

export interface KnowledgeTopicDetail extends KnowledgeTopicSummary {
  why_it_matters?: string;
  mechanics?: string;
  vulnerable_example?: string;
  secure_example?: string;
  secure_remediation?: string;
  preventive_guidelines: string[];
  prevention_guidelines?: string[];
  detection_rule?: string;
  quiz_question?: string;
  quiz_options?: string[];
  quiz_correct_index?: number;
  quiz_explanation?: string;
  quiz?: QuizModel;
}

export const apiClient = new ApiClient();
