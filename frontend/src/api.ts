import type { ChatResult, Health } from "./types";

export const API_BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const newSessionId = (): string => `s-${crypto.randomUUID().slice(0, 8)}`;

function describe(status: number, detail: unknown): string {
  if (status === 503) return "All AI providers are unavailable right now. Nothing was saved; try again in a moment.";
  if (status === 422) {
    if (Array.isArray(detail)) {
      const msgs = detail.map((d) => (typeof d?.msg === "string" ? d.msg.replace(/^Value error, /, "") : "invalid value"));
      return `The request was rejected: ${msgs.join("; ")}.`;
    }
    return `The request was rejected: ${String(detail)}`;
  }
  return typeof detail === "string" ? detail : `The server returned an error (${status}).`;
}

export async function sendChat(
  body: { session_id: string; message: string; system_prompt?: string },
  simulate?: string,
): Promise<ChatResult> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (simulate) headers["X-Simulate-Failure"] = simulate;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat`, { method: "POST", headers, body: JSON.stringify(body) });
  } catch {
    throw new ApiError(0, `Can't reach the backend at ${API_BASE}. Check that it is running and that CORS allows this origin.`);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new ApiError(res.status, describe(res.status, data?.detail));
  return data as ChatResult;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_BASE}/health`);
  const data = (await res.json()) as Health;
  return data; // a 503 still carries a useful body ("degraded")
}

export async function getHistory(sessionId: string): Promise<{ role: string; content: string }[]> {
  const res = await fetch(`${API_BASE}/sessions/${encodeURIComponent(sessionId)}/messages`);
  if (!res.ok) throw new ApiError(res.status, describe(res.status, (await res.json().catch(() => ({}))).detail));
  return (await res.json()).messages;
}
