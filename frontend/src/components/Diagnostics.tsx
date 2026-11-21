import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { API_BASE, getHealth } from "../api";
import type { Health } from "../types";

export function Diagnostics() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setHealth(await getHealth());
      setError(null);
    } catch {
      setHealth(null);
      setError(`Backend unreachable at ${API_BASE}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const unknown = "unknown";
  const rows: [string, string][] = health
    ? [
        ["Backend status", health.status],
        ["Database", health.database ?? unknown],
        ["Cache", health.cache_enabled ? `enabled (${health.cache_type ?? unknown})` : "disabled"],
        ["Model", health.model ?? unknown],
        ["API keys configured", String(health.keys_configured)],
        ["Failure simulation", health.failure_simulation_enabled === undefined ? unknown : health.failure_simulation_enabled ? "enabled" : "disabled"],
        ["Version", health.version ?? unknown],
        ["Backend URL", API_BASE],
      ]
    : [];

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8 sm:px-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">System diagnostics</h2>
        <button type="button" className="btn-ghost" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>
      <p className="mt-1 text-sm text-muted">Read live from the backend's /health endpoint. Key values are never exposed, only the count.</p>
      {error && <p role="alert" className="mt-5 rounded-panel border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">{error}</p>}
      {rows.length > 0 && (
        <dl className="mt-5 divide-y divide-line rounded-panel border border-line bg-surface shadow-panel">
          {rows.map(([k, v]) => (
            <div key={k} className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
              <dt className="text-muted">{k}</dt>
              <dd className="break-all text-right font-mono text-[13px]">{v}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
