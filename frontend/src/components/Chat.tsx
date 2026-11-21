import { Loader2, SendHorizonal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { SIMULATIONS, type ChatItem, type Health } from "../types";
import { Message } from "./Message";

interface Props {
  items: ChatItem[];
  pending: boolean;
  health: Health | null;
  systemPrompt: string;
  onSystemPrompt: (value: string) => void;
  simulate: string;
  onSimulate: (value: string) => void;
  onSend: (text: string) => void;
}

const SUGGESTIONS = ["What is the capital of France?", "Explain caching in two sentences.", "Write a Python function that reverses a string."];

export function Chat({ items, pending, health, systemPrompt, onSystemPrompt, simulate, onSimulate, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [items, pending]);

  const submit = () => {
    const text = draft.trim();
    if (!text || pending) return;
    setDraft("");
    onSend(text);
  };

  return (
    <section className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6" aria-live="polite">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {items.length === 0 && (
            <div className="py-10">
              <h2 className="text-xl font-semibold">Ask anything</h2>
              <p className="mt-1 max-w-md text-sm text-muted">
                Every reply shows where it came from, which model answered, how long it took and how many tokens it used.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" className="btn-ghost text-left" onClick={() => onSend(s)} disabled={pending}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {items.map((item) => (
            <Message key={item.id} item={item} />
          ))}
          {pending && (
            <div className="flex items-center gap-2 text-sm text-muted" role="status">
              <Loader2 size={16} className="animate-spin" /> Waiting for a reply…
            </div>
          )}
          <div ref={bottom} />
        </div>
      </div>

      <div className="border-t border-line bg-surface px-4 py-3 sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-2">
          <div className="flex flex-col gap-2 sm:flex-row">
            <input
              data-testid="system-prompt-input"
              aria-label="System prompt"
              className="field sm:flex-1"
              placeholder="System prompt for this session (optional)"
              value={systemPrompt}
              maxLength={4000}
              onChange={(e) => onSystemPrompt(e.target.value)}
            />
            {health?.failure_simulation_enabled && (
              <select aria-label="Simulate failure" className="field sm:w-60" value={simulate} onChange={(e) => onSimulate(e.target.value)}>
                {SIMULATIONS.map((o) => (
                  <option key={o.label} value={o.header}>{o.label}</option>
                ))}
              </select>
            )}
          </div>
          <div className="flex items-end gap-2">
            <textarea
              data-testid="chat-input"
              aria-label="Message"
              rows={2}
              className="field resize-none"
              placeholder="Message Lyftr AI (Enter to send, Shift+Enter for a new line)"
              value={draft}
              maxLength={4000}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
            />
            <button data-testid="send-button" type="button" className="btn-primary h-[42px]" onClick={submit} disabled={pending || !draft.trim()}>
              <SendHorizonal size={16} /> Send
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
