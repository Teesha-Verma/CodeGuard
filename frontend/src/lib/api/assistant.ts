import { apiClient } from './client';
import { ReviewIssue, ReviewReport } from '@/types';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  contextPill?: string;
}

export interface AssistantQueryOptions {
  query: string;
  issue?: ReviewIssue | null;
  filePath?: string;
  report?: ReviewReport | null;
}

/**
 * Assistant service adapter.
 * Communicates with FastAPI `/assistant/chat` (Groq primary -> Gemini fallback),
 * with graceful deterministic local fallback if backend is offline.
 */
export async function queryAssistant({
  query,
  issue,
  filePath,
  report,
}: AssistantQueryOptions): Promise<string> {
  // 1. Attempt real backend assistant call
  try {
    const apiResp = await apiClient.chatAssistant({
      messages: [{ role: 'user', content: query }],
      review_id: report?.review_id,
      file_path: filePath,
      line: issue?.line,
      finding_line: issue?.line,
      context: report?.repo_url ? `Repository: ${report.repo_url}` : undefined,
    });
    const reply = apiResp.reply || apiResp.message;
    if (reply && reply.trim()) {
      return reply.trim();
    }
  } catch {
    // Fall back to local contextual heuristics if backend is unreachable
  }

  const normQuery = query.toLowerCase().trim();

  // If no finding is attached
  if (!issue) {
    if (normQuery.includes('summary') || normQuery.includes('overview')) {
      const stats = report?.summary_stats;
      if (stats) {
        return `Review Summary for ${report?.repo_url || 'Active Review'}:\n\n` +
          `• Total Findings: ${stats.total_issues} (${stats.meaningful_issues || stats.total_issues} high-signal)\n` +
          `• Critical Severity: ${stats.by_severity.critical}\n` +
          `• High Severity: ${stats.by_severity.high}\n` +
          `• Medium Severity: ${stats.by_severity.medium}\n` +
          `• Average Confidence: ${(stats.avg_confidence * 100).toFixed(0)}%\n\n` +
          `Would you like me to inspect the critical issues or provide a remediation plan?`;
      }
      return `CodeGuard Assistant is ready. Please select a finding or review to begin in-depth contextual analysis.`;
    }

    return `I am CodeGuard Assistant. I analyze static AST rules, dataflow taint paths, and repository intelligence. Attach a finding or ask about code review best practices to begin.`;
  }

  // 1. Explain / Why Query
  if (normQuery.includes('explain') || normQuery.includes('why') || normQuery.includes('what happened')) {
    let resp = `### Finding Analysis: ${issue.issue}\n\n`;
    resp += `**Location**: \`${filePath}:${issue.line}\`\n\n`;
    resp += `**Root Cause**:\n${issue.root_cause || 'Direct unvalidated parameter flow into execution sink.'}\n\n`;
    if (issue.impact) {
      resp += `**Security Impact**:\n${issue.impact}\n\n`;
    }
    if (issue.standards && issue.standards.length > 0) {
      resp += `**Governing Standards**: ${issue.standards.join(', ')}\n\n`;
    }
    resp += `**Detection Signature**:\nTriggered by ${issue.detection_sources?.join(' + ') || issue.source} with ${(
      (issue.confidence || 0.85) * 100
    ).toFixed(0)}% confidence rating.`;
    return resp;
  }

  // 2. Fix / How to solve Query
  if (normQuery.includes('fix') || normQuery.includes('solve') || normQuery.includes('remediat')) {
    let resp = `### Recommended Remediation for Line ${issue.line}\n\n`;
    resp += `${issue.fix || 'Parameterize inputs and eliminate dynamic string concatenation.'}\n\n`;
    if (issue.patch) {
      resp += `**Suggested Diff**:\n\`\`\`diff\n${issue.patch}\n\`\`\`\n\n`;
    }
    resp += `You can test this remediation directly in the **Fix Playground** to verify that CodeGuard's AST analyzer confirms the vulnerability is eliminated.`;
    return resp;
  }

  // 3. Dataflow / Taint Query
  if (normQuery.includes('dataflow') || normQuery.includes('taint') || normQuery.includes('flow')) {
    if (issue.dataflow_path && issue.dataflow_path.length > 0) {
      let resp = `### Taint Propagation Path\n\n`;
      resp += `CodeGuard detected an unbroken source-to-sink dataflow trace:\n\n`;
      issue.dataflow_path.forEach((step: string, idx: number) => {
        const role =
          idx === 0 ? '(Taint Source)' : idx === issue.dataflow_path!.length - 1 ? '(Dangerous Sink)' : '(Propagation)';
        resp += `${idx + 1}. \`${step}\` ${role}\n`;
      });
      resp += `\nNo sanitizing validator or boundary escape was detected between the entry point and execution call.`;
      return resp;
    }
    return `This finding was flagged via structural AST visitor pattern (\`${issue.source}\`). No dynamic interprocedural taint path was required for detection.`;
  }

  // 4. Teach me / Concept Query
  if (normQuery.includes('teach') || normQuery.includes('learn') || normQuery.includes('concept')) {
    return `### Security Concept: ${issue.category || issue.issue_type}\n\n` +
      `This issue belongs to the **${issue.standards?.[0] || 'CWE Security'}** classification.\n\n` +
      `**Core Principle**: Never allow external untrusted data to dictate program control flow or backend syntax. Inputs must be validated against a strict allowlist or parsed through safe structural types.\n\n` +
      `Would you like to open **Learner Mode** for an interactive quiz and comprehensive curriculum on this topic?`;
  }

  // 5. Summarize Query
  if (normQuery.includes('summarize') || normQuery.includes('summary')) {
    return `### Summary of Issue\n\n` +
      `• **Issue**: ${issue.issue}\n` +
      `• **Severity**: ${issue.severity.toUpperCase()}\n` +
      `• **File**: ${filePath}:${issue.line}\n` +
      `• **Action**: ${issue.fix ? issue.fix.slice(0, 140) + '...' : 'Apply parameterized isolation'}`;
  }

  // General Grounded Response
  return `### Finding Context: ${issue.issue}\n\n` +
    `Regarding your question: "${query}"\n\n` +
    `In \`${filePath}\` at line ${issue.line}, CodeGuard identified that: ${issue.root_cause || issue.issue}\n\n` +
    `**Next Recommended Steps**:\n` +
    `1. Use [Fix Playground](/playground) to modify and re-analyze the code.\n` +
    `2. Open [Learner Mode](/learn) to complete a mini-quiz on this vulnerability pattern.\n` +
    `3. View [Dataflow](/dataflow) to see the untrusted input propagation graph.`;
}
