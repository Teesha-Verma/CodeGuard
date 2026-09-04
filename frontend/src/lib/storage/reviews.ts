import { StoredReviewRecord, ReviewReport } from '@/types';
import { INITIAL_SAMPLE_REVIEWS } from '@/lib/data/sampleReviews';

const STORAGE_KEY = 'codeguard_reviews_v2';

export function getStoredReviews(): StoredReviewRecord[] {
  if (typeof window === 'undefined') return INITIAL_SAMPLE_REVIEWS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_SAMPLE_REVIEWS));
      return INITIAL_SAMPLE_REVIEWS;
    }
    return JSON.parse(raw);
  } catch {
    return INITIAL_SAMPLE_REVIEWS;
  }
}

export function saveStoredReview(review: StoredReviewRecord): void {
  if (typeof window === 'undefined') return;
  try {
    const current = getStoredReviews();
    const existingIndex = current.findIndex((r) => r.review_id === review.review_id);
    if (existingIndex >= 0) {
      current[existingIndex] = { ...current[existingIndex], ...review };
    } else {
      current.unshift(review);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch (err) {
    console.error('Failed to save review to storage', err);
  }
}

export function updateStoredReview(
  reviewId: string,
  update: Partial<StoredReviewRecord>
): void {
  if (typeof window === 'undefined') return;
  try {
    const current = getStoredReviews();
    const index = current.findIndex((r) => r.review_id === reviewId);
    if (index >= 0) {
      current[index] = { ...current[index], ...update };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
    }
  } catch (err) {
    console.error('Failed to update review in storage', err);
  }
}

export function getStoredReview(reviewId: string): StoredReviewRecord | undefined {
  const current = getStoredReviews();
  return current.find((r) => r.review_id === reviewId);
}

export function deleteStoredReview(reviewId: string): void {
  if (typeof window === 'undefined') return;
  try {
    const current = getStoredReviews().filter((r) => r.review_id !== reviewId);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch (err) {
    console.error('Failed to delete review from storage', err);
  }
}

/**
 * Creates a baseline record from a finished report
 */
export function recordFromReport(report: ReviewReport, durationSeconds?: number): StoredReviewRecord {
  const isSnippet = !report.repo_url || report.repo_url === 'snippet';
  return {
    review_id: report.review_id,
    type: isSnippet ? 'snippet' : 'pr',
    repo_url: report.repo_url || 'code-snippet',
    pr_number: report.pr_number,
    filename: report.snippet_filename || report.file_reports[0]?.file_path || 'snippet.py',
    status: 'completed',
    created_at: report.created_at || new Date().toISOString(),
    duration_seconds: durationSeconds ?? report.duration_seconds ?? 28,
    total_issues: report.summary_stats?.total_issues ?? 0,
    meaningful_issues: report.summary_stats?.meaningful_issues ?? report.summary_stats?.total_issues ?? 0,
    style_findings: report.summary_stats?.style_findings ?? 0,
    suppressed_findings: report.summary_stats?.suppressed_findings ?? 0,
    critical_issues: report.summary_stats?.by_severity?.critical ?? 0,
    high_issues: report.summary_stats?.by_severity?.high ?? 0,
    report,
  };
}
