import type { ChatResult } from "../types";
import { SourceBadge } from "./Message";

const STEP_STYLE: Record<string, string> = {
  key_failed: "bg-danger",
  all_failed: "bg-danger",
  fallback: "bg-warn",
  cache_hit: "bg-accent",
  key_succeeded: "bg-ok",
};

export function Insights({ last, simulate }: { last: ChatResult | null; simulate: string }) {
  if (!last) {
    return <p className="text-sm text-muted">Send a message to see how the backend handled it: cache lookup, which key answered and any fallbacks.</p>;
  }
  const m = last.metadata;
  const rows: [string, string][] = [
    ["Model", m.model],
    ["Latency", `${m.latency_ms} ms`],
    ["Input tokens", String(m.input_tokens)],
    ["Output tokens", String(m.output_tokens)],
    ["Key", m.key_id ?? "none (cache)"],
    ["Fallback attempts", String(m.fallback_attempts)],
  ];
  return (
    <div className="flex flex-col gap-5">
      <div>
        <SourceBadge source={m.resolution_source} />
        {simulate && <p className="mt-2 text-xs text-warn">Simulation header sent: <span className="font-mono">{simulate}</span></p>}
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted">{k}</dt>
            <dd className="break-all text-right font-mono text-[13px]">{v}</dd>
          </div>
        ))}
      </dl>
      <div>
        <h3 className="mb-2 text-sm font-semibold">Request trace</h3>
        <ol className="flex flex-col gap-2">
          {last.trace.map((e, i) => (
            <li key={i} className="flex gap-2.5 text-[13px]">
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${STEP_STYLE[e.step] ?? "bg-muted/50"}`} />
              <span className="flex-1">{e.detail}</span>
              <span className="font-mono text-xs text-muted">{e.elapsed_ms} ms</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
