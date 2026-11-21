import { FlaskConical, Loader2 } from "lucide-react";
import { useState } from "react";
import { ApiError, getHistory, newSessionId, sendChat } from "../api";
import { SIMULATIONS, type ChatResult, type Health } from "../types";
import { SourceBadge } from "./Message";

interface Step { message: string; header?: string; newSession?: boolean; system?: string }
interface Experiment { title: string; explain: string; needsSimulation?: boolean; steps: Step[] }

const Q = "What is the capital of France?";
const EXPERIMENTS: Experiment[] = [
  { title: "Cache hit across sessions", explain: "Same question in two new sessions. The second should be LLM_CACHE with key_id none.", steps: [{ message: Q, newSession: true }, { message: Q, newSession: true }] },
  { title: "Different system prompt", explain: "Same question, different system prompt. Both should be LIVE_INFERENCE because the full message list differs.", steps: [{ message: Q, newSession: true, system: "Answer in one word." }, { message: Q, newSession: true, system: "Answer in a full sentence." }] },
  { title: "Remember earlier messages", explain: "Two turns in one session. The second prompt carries the first exchange, so input tokens grow.", steps: [{ message: "My name is Ada. Remember it.", newSession: true }, { message: "What is my name?" }] },
  { title: "Failover: key_1 returns 429", explain: "Sends X-Simulate-Failure: key_1=429. Expect key_2 with 1 fallback attempt.", needsSimulation: true, steps: [{ message: "Name one primary colour.", header: "key_1=429", newSession: true }] },
  { title: "Failover: key_1 500, key_2 fine", explain: "Sends key_1=500. Expect key_2 to answer.", needsSimulation: true, steps: [{ message: "Name one planet.", header: "key_1=500", newSession: true }] },
  { title: "Every key fails", explain: "Sends *=429. Expect a 503 and nothing saved to history.", needsSimulation: true, steps: [{ message: "This should fail.", header: "*=429", newSession: true }] },
  { title: "Invalid input", explain: "An empty message. Expect a 422.", steps: [{ message: "   ", newSession: true }] },
];

interface Entry {
  id: number;
  label: string;
  header: string;
  status: number;
  result?: ChatResult;
  error?: string;
  history?: number;
}

export function Playground({ health }: { health: Health | null }) {
  const [log, setLog] = useState<Entry[]>([]);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState(Q);
  const [system, setSystem] = useState("");
  const [header, setHeader] = useState("");
  const [fresh, setFresh] = useState(true);
  const [session, setSession] = useState(newSessionId);
  const simOk = !!health?.failure_simulation_enabled;

  const run = async (label: string, steps: Step[]) => {
    setRunning(true);
    let sid = session;
    for (const step of steps) {
      if (step.newSession) { sid = newSessionId(); setSession(sid); }
      const entry: Entry = { id: Date.now() + Math.random(), label, header: step.header ?? "", status: 200 };
      try {
        entry.result = await sendChat({ session_id: sid, message: step.message, system_prompt: step.system || undefined }, step.header);
        entry.history = (await getHistory(sid)).length;
      } catch (e) {
        entry.status = e instanceof ApiError ? e.status : 0;
        entry.error = e instanceof Error ? e.message : "Unknown error";
      }
      setLog((l) => [entry, ...l]);
    }
    setRunning(false);
  };

  const custom = () => run("Custom request", [{ message, header, system, newSession: fresh }]);

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_1.1fr]">
      <div className="flex flex-col gap-6">
        <div>
          <h2 className="flex items-center gap-2 text-xl font-semibold"><FlaskConical size={20} /> Developer playground</h2>
          <p className="mt-1 text-sm text-muted">Each experiment sends real requests to the backend. Nothing here is mocked.</p>
          {!simOk && <p className="mt-2 text-sm text-warn">Failure simulation is off on this backend (ENABLE_FAILURE_SIMULATION), so failover experiments are disabled.</p>}
        </div>
        <ul className="flex flex-col gap-2">
          {EXPERIMENTS.map((x) => (
            <li key={x.title} className="flex items-start justify-between gap-3 rounded-panel border border-line bg-surface p-3 shadow-panel">
              <div>
                <p className="text-sm font-medium">{x.title}</p>
                <p className="mt-0.5 text-[13px] text-muted">{x.explain}</p>
              </div>
              <button type="button" className="btn-ghost shrink-0" disabled={running || (x.needsSimulation && !simOk)} onClick={() => run(x.title, x.steps)}>Run</button>
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-2 rounded-panel border border-line bg-surface p-3 shadow-panel">
          <p className="text-sm font-medium">Custom request</p>
          <textarea aria-label="Playground message" className="field" rows={2} value={message} onChange={(e) => setMessage(e.target.value)} />
          <input aria-label="Playground system prompt" className="field" placeholder="System prompt (optional)" value={system} onChange={(e) => setSystem(e.target.value)} />
          <select aria-label="Playground failure simulation" className="field" value={header} onChange={(e) => setHeader(e.target.value)} disabled={!simOk}>
            {SIMULATIONS.map((o) => <option key={o.label} value={o.header}>{o.label}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={fresh} onChange={(e) => setFresh(e.target.checked)} /> Use a new session ({fresh ? "new" : session})</label>
          <button type="button" className="btn-primary" onClick={custom} disabled={running}>Send request</button>
        </div>
      </div>

      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">Results {running && <Loader2 size={14} className="animate-spin" />}</h3>
        {log.length === 0 && <p className="text-sm text-muted">Run an experiment to see the response metadata and trace here.</p>}
        <ul className="flex flex-col gap-3">
          {log.map((e) => (
            <li key={e.id} className="rounded-panel border border-line bg-surface p-3 text-sm shadow-panel">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{e.label}</span>
                <span className={`rounded-full px-2 py-0.5 font-mono text-xs ${e.status === 200 ? "bg-ok-soft text-ok" : "bg-danger-soft text-danger"}`}>HTTP {e.status || "network"}</span>
                {e.header && <span className="font-mono text-xs text-warn">{e.header}</span>}
              </div>
              {e.error && <p className="mt-2 text-danger">{e.error}</p>}
              {e.result && (
                <>
                  <p className="mt-2 text-[13px]">{e.result.reply}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs">
                    <SourceBadge source={e.result.metadata.resolution_source} />
                    <span>key: {e.result.metadata.key_id ?? "none"}</span>
                    <span>fallbacks: {e.result.metadata.fallback_attempts}</span>
                    <span>{e.result.metadata.latency_ms} ms</span>
                    <span>in {e.result.metadata.input_tokens} / out {e.result.metadata.output_tokens}</span>
                    <span>stored msgs: {e.history}</span>
                  </div>
                  <p className="mt-2 font-mono text-xs text-muted">{e.result.trace.map((t) => t.step).join(" → ")}</p>
                </>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
