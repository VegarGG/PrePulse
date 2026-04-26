// Typed REST client for the PrePulse FastAPI backend (§18.1).

import type {
  CompanyProfile,
  DashboardMetrics,
  DemoProfileSummary,
  PipelineState,
  ScanListRow,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001";

async function request<T>(
  path: string,
  init?: RequestInit & { parse?: "json" | "text" },
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    const err = new Error(`HTTP ${res.status} ${res.statusText}`) as Error & {
      status: number;
      body: unknown;
    };
    err.status = res.status;
    err.body = body;
    throw err;
  }
  if (init?.parse === "text") {
    return (await res.text()) as T;
  }
  return (await res.json()) as T;
}

export async function getHealth(): Promise<{ status: string; version: string; mode: string }> {
  return request("/api/health");
}

export async function listProfiles(): Promise<DemoProfileSummary[]> {
  return request("/api/demo/profiles");
}

export async function startScan(
  body: { profile_id?: string; custom_profile?: CompanyProfile },
): Promise<{ scan_id: string }> {
  return request("/api/scans", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function listScans(): Promise<ScanListRow[]> {
  return request("/api/scans");
}

export async function getScan(scanId: string): Promise<PipelineState> {
  return request(`/api/scans/${encodeURIComponent(scanId)}`);
}

export async function approveAction(scanId: string, actionId: string): Promise<{ ok: true }> {
  return request(`/api/scans/${encodeURIComponent(scanId)}/approve`, {
    method: "POST",
    body: JSON.stringify({ action_id: actionId }),
  });
}

export async function rejectAction(
  scanId: string,
  actionId: string,
  reason?: string,
): Promise<{ ok: true }> {
  return request(`/api/scans/${encodeURIComponent(scanId)}/reject`, {
    method: "POST",
    body: JSON.stringify({ action_id: actionId, reason }),
  });
}

export async function getTrace(scanId: string): Promise<string> {
  return request(`/api/scans/${encodeURIComponent(scanId)}/trace`, { parse: "text" });
}

export async function getMetrics(): Promise<DashboardMetrics> {
  return request("/api/dashboard/metrics");
}

// ---------- Chat ----------

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatTopChunk {
  filename: string;
  similarity: number;
  preview: string;
}

export type ChatDecisionPath =
  | "similarity_low"
  | "llm_in_scope"
  | "llm_refused"
  | "parse_failed";

export interface ChatResponse {
  answer: string;
  is_in_scope: boolean;
  similarity: number;
  decision_path: ChatDecisionPath;
  top_chunks: ChatTopChunk[];
  refusal_sentence: string;
  provider: string;   // "anthropic" | "openai" | "deepseek" | "unknown" | ""
  model: string;      // raw model name from response_metadata, e.g. "deepseek-v4-flash"
}

export async function sendChat(messages: ChatTurn[]): Promise<ChatResponse> {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ messages }),
  });
}

export function sseUrl(scanId: string): string {
  return `${API_BASE}/api/scans/${encodeURIComponent(scanId)}/events`;
}

export function traceDownloadUrl(scanId: string): string {
  return `${API_BASE}/api/scans/${encodeURIComponent(scanId)}/trace`;
}
