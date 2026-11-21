export type ResolutionSource = "LIVE_INFERENCE" | "LLM_CACHE";

export interface Metadata {
  resolution_source: ResolutionSource;
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  key_id: string | null;
  fallback_attempts: number;
}

export interface TraceEvent {
  step: string;
  detail: string;
  elapsed_ms: number;
  key_id: string | null;
}

export interface ChatResult {
  session_id: string;
  reply: string;
  metadata: Metadata;
  trace: TraceEvent[];
}

export interface Health {
  status: string;
  keys_configured: number;
  cache_enabled: boolean;
  database?: string;
  model?: string;
  cache_type?: string;
  failure_simulation_enabled?: boolean;
  version?: string;
}

export type ChatItem =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; text: string; metadata: Metadata }
  | { id: string; role: "error"; text: string };

export interface SimulationOption {
  label: string;
  header: string; // empty = no header
}

export const SIMULATIONS: SimulationOption[] = [
  { label: "No simulated failure", header: "" },
  { label: "key_1 returns 429", header: "key_1=429" },
  { label: "key_1 returns 500", header: "key_1=500" },
  { label: "key_1 429 and key_2 500", header: "key_1=429,key_2=500" },
  { label: "Every key returns 429", header: "*=429" },
];
