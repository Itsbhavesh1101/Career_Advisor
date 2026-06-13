const AI_ERROR_PATTERNS = [
  "llm",
  "openai",
  "nvidia",
  "circuit breaker",
  "schema",
  "request timed out",
  "timed out",
  "service unavailable",
  "unable to queue analysis job",
  "analysis job failed",
  "invalid resume analysis schema",
  "invalid company fit schema",
  "invalid employability",
  "invalid internship readiness",
  "invalid placement risk",
  "invalid role-gap schema",
  "llm chat generation failed",
  "llm industry-demand generation failed",
];

export const LONG_WAIT_NOTICE =
  "AI is taking a little longer than usual. Thanks for your patience, your request is still in progress.";

export function toGentleAiMessage(message: string): string {
  const normalized = message.toLowerCase();
  const isAiIssue = AI_ERROR_PATTERNS.some((pattern) => normalized.includes(pattern));

  if (!isAiIssue) {
    return message;
  }

  return "Our AI service is temporarily busy right now. Please try again shortly. Your data is safe.";
}
