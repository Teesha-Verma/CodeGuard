export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type IssueSource = 'static_analysis' | 'linter' | 'llm' | 'combined' | 'bandit' | 'pylint' | 'flake8' | 'ast' | 'cfg' | 'dataflow' | 'taint';

export type IssueType =
  | 'bug'
  | 'security'
  | 'performance'
  | 'code_smell'
  | 'style'
  | 'complexity'
  | 'dead_code'
  | 'type_error'
  | 'concurrency'
  | 'error_handling'
  | 'best_practice'
  | 'async misuse'
  | 'mutation risks'
  | 'runtime logic risks'
  | 'maintainability'
  | string;

export interface ReviewIssue {
  line: number;
  severity: Severity;
  confidence: number;
  issue: string;
  root_cause: string;
  fix: string;
  patch?: string | null;
  issue_type: IssueType;
  source: IssueSource | string;
  detection_sources?: string[];
  reasoning_source?: 'llm' | 'static_analysis' | string;
  standards?: string[]; // e.g. ["CWE-89", "OWASP ASVS 5.3.4"]
  dataflow_path?: string[]; // e.g. ["request.args.get('id')", "account_id", "query", "cursor.execute()"]
  trigger_condition?: string;
  impact?: string;
  category?: string;
}

export interface FileReport {
  file_path: string;
  status?: 'modified' | 'added' | 'deleted' | string; // 'M', 'A', 'D'
  issues: ReviewIssue[];
  ast_metadata?: Record<string, unknown> | null;
  linter_findings?: Array<Record<string, unknown>> | null;
  file_content?: string; // Optional embedded content if supplied by diff or snippet
}

export interface SummaryStats {
  total_issues: number;
  meaningful_issues?: number;
  style_findings?: number;
  suppressed_findings?: number;
  total_all_issues?: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  by_source?: {
    llm?: number;
    static_analysis?: number;
    linter?: number;
    [key: string]: number | undefined;
  };
  reasoning_sources?: {
    llm?: number;
    static_analysis?: number;
  };
  avg_confidence: number;
}

export interface RepositoryIntelligence {
  architecture?: string; // e.g. "Layered", "Clean", "MVC"
  layer_violations?: number;
  modules_affected?: number;
  risk_hotspots?: Array<{
    module: string;
    complexity: 'High' | 'Medium' | 'Low' | string;
    fan_in: number;
    fan_out: number;
  }>;
  change_impact?: string;
}

export interface ReviewReport {
  review_id: string;
  repo_url?: string;
  pr_number?: number;
  snippet_filename?: string;
  file_reports: FileReport[];
  summary_stats: SummaryStats;
  evaluation_metrics?: Record<string, unknown>;
  trace_id: string;
  created_at?: string;
  duration_seconds?: number;
  repo_intelligence?: RepositoryIntelligence;
}

export interface ReviewStatusResponse {
  review_id: string;
  status: 'started' | 'running' | 'processing' | 'queued' | 'completed' | 'failed' | 'cancelled' | 'timed_out' | string;
  message?: string;
  stage?: string;
  error_code?: string;
  error_message?: string;
  failed_stage?: string;
  duration_seconds?: number;
  started_at?: string;
  updated_at?: string;
  progress_percent?: number;
}

export interface StoredReviewRecord {
  review_id: string;
  type: 'pr' | 'snippet';
  repo_url?: string;
  pr_number?: number;
  filename?: string;
  language?: string;
  status: 'running' | 'completed' | 'failed' | 'queued';
  created_at: string;
  duration_seconds?: number;
  total_issues?: number;
  meaningful_issues?: number;
  style_findings?: number;
  suppressed_findings?: number;
  critical_issues?: number;
  high_issues?: number;
  error_message?: string;
  report?: ReviewReport;
}
