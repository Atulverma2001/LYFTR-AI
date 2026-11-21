import { Check, Copy } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatItem } from "../types";

function MetaItem({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-baseline gap-1.5">
      <span className="text-muted">{label}</span>
      {children}
    </span>
  );
}

export function SourceBadge({ source, testId }: { source: string; testId?: string }) {
  const cached = source === "LLM_CACHE";
  return (
    <span
      data-testid={testId}
      className={`rounded-full px-2 py-0.5 font-mono text-xs font-medium ${cached ? "bg-accent-soft text-accent-strong" : "bg-ok-soft text-ok"}`}
    >
      {source}
    </span>
  );
}

export function Message({ item }: { item: ChatItem }) {
  const [copied, setCopied] = useState(false);

  if (item.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-panel rounded-br-sm bg-ink px-4 py-2.5 text-sm text-white sm:max-w-[70%]">
          {item.text}
        </p>
      </div>
    );
  }

  if (item.role === "error") {
    return (
      <div role="alert" className="rounded-panel border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
        {item.text}
      </div>
    );
  }

  const m = item.metadata;
  const copy = async () => {
    await navigator.clipboard.writeText(item.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <article data-testid="assistant-message" className="max-w-full rounded-panel rounded-bl-sm border border-line bg-surface p-4 shadow-panel sm:max-w-[85%]">
      <div className="prose-chat break-words text-sm leading-relaxed">
        <ReactMarkdown>{item.text}</ReactMarkdown>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-line pt-2.5 text-xs">
        <SourceBadge source={m.resolution_source} testId="meta-source" />
        <MetaItem label="model"><span data-testid="meta-model" className="font-mono">{m.model}</span></MetaItem>
        <MetaItem label="latency"><span data-testid="meta-latency" className="font-mono">{m.latency_ms} ms</span></MetaItem>
        <MetaItem label="in"><span data-testid="meta-input-tokens" className="font-mono">{m.input_tokens}</span></MetaItem>
        <MetaItem label="out"><span data-testid="meta-output-tokens" className="font-mono">{m.output_tokens}</span></MetaItem>
        <button type="button" onClick={copy} aria-label="Copy reply" className="ml-auto rounded p-1 text-muted hover:bg-canvas hover:text-ink">
          {copied ? <Check size={14} /> : <Copy size={14} />}
        </button>
      </div>
    </article>
  );
}
