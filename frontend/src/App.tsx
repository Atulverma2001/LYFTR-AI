import { Activity, FlaskConical, MessageSquare, PanelRight, Plus, Stethoscope } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { ApiError, getHealth, newSessionId, sendChat } from "./api";
import { Chat } from "./components/Chat";
import { Diagnostics } from "./components/Diagnostics";
import { Insights } from "./components/Insights";
import { Playground } from "./components/Playground";
import type { ChatItem, ChatResult, Health } from "./types";

type View = "chat" | "playground" | "diagnostics";

const TABS: { id: View; label: string; icon: typeof Activity }[] = [
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "playground", label: "Playground", icon: FlaskConical },
  { id: "diagnostics", label: "Diagnostics", icon: Stethoscope },
];

export default function App() {
  const [view, setView] = useState<View>("chat");
  const [sessionId, setSessionId] = useState(newSessionId); // a new session on every page load
  const [items, setItems] = useState<ChatItem[]>([]);
  const [pending, setPending] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [simulate, setSimulate] = useState("");
  const [last, setLast] = useState<ChatResult | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [insightsOpen, setInsightsOpen] = useState(false);
  const counter = useRef(0);
  const nextId = () => `m${++counter.current}`;

  useEffect(() => { getHealth().then(setHealth).catch(() => setHealth(null)); }, []);

  const send = async (text: string) => {
    setItems((i) => [...i, { id: nextId(), role: "user", text }]);
    setPending(true);
    try {
      const result = await sendChat(
        { session_id: sessionId, message: text, system_prompt: systemPrompt.trim() || undefined },
        simulate || undefined,
      );
      setLast(result);
      setItems((i) => [...i, { id: nextId(), role: "assistant", text: result.reply, metadata: result.metadata }]);
    } catch (e) {
      const message = e instanceof ApiError ? e.message : "Something went wrong while sending the message.";
      setItems((i) => [...i, { id: nextId(), role: "error", text: message }]);
    } finally {
      setPending(false);
    }
  };

  const reset = () => {
    setSessionId(newSessionId());
    setItems([]);
    setLast(null);
  };

  return (
    <div className="flex h-screen flex-col">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-line bg-surface px-4 py-2.5 sm:px-6">
        <div className="leading-tight">
          <h1 className="text-base font-semibold">Lyftr AI</h1>
          
        </div>
        <nav aria-label="Views" className="order-3 flex w-full gap-1 sm:order-none sm:w-auto">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              aria-current={view === id ? "page" : undefined}
              onClick={() => setView(id)}
              className={`btn ${view === id ? "bg-accent-soft text-accent-strong" : "text-muted hover:bg-canvas hover:text-ink"}`}
            >
              <Icon size={15} /> {label}
            </button>
          ))}
        </nav>
        {view === "chat" && (
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden font-mono text-xs text-muted md:inline">{sessionId}</span>
            <button type="button" className="btn-ghost" onClick={reset}><Plus size={14} /> New chat</button>
            <button type="button" className="btn-ghost lg:hidden" aria-pressed={insightsOpen} onClick={() => setInsightsOpen((o) => !o)}>
              <PanelRight size={14} /> Insights
            </button>
          </div>
        )}
      </header>

      <main className="flex min-h-0 flex-1">
        {view === "chat" && (
          <>
            <div className="flex min-w-0 flex-1 flex-col">
              {insightsOpen && (
                <div className="max-h-[45vh] overflow-y-auto border-b border-line bg-surface p-4 lg:hidden">
                  <Insights last={last} simulate={simulate} />
                </div>
              )}
              <Chat items={items} pending={pending} health={health} systemPrompt={systemPrompt} onSystemPrompt={setSystemPrompt}
                simulate={simulate} onSimulate={setSimulate} onSend={send} />
            </div>
            <aside aria-label="Request insights" className="hidden w-80 shrink-0 overflow-y-auto border-l border-line bg-surface p-5 lg:block">
              <h2 className="mb-4 text-sm font-semibold">Request insights</h2>
              <Insights last={last} simulate={simulate} />
            </aside>
          </>
        )}
        {view === "playground" && <div className="flex-1 overflow-y-auto"><Playground health={health} /></div>}
        {view === "diagnostics" && <div className="flex-1 overflow-y-auto"><Diagnostics /></div>}
      </main>
    </div>
  );
}
