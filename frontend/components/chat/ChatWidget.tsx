"use client";

import { useEffect, useRef, useState } from "react";
import { MessageSquare, Send, X, ShieldAlert, Sparkles } from "lucide-react";
import { sendChat, type ChatDecisionPath, type ChatTurn } from "@/lib/api";

type Message =
  | { role: "user"; content: string }
  | {
      role: "assistant";
      content: string;
      is_in_scope: boolean;
      similarity: number;
      decision_path: ChatDecisionPath;
      provider: string;
      model: string;
    }
  | { role: "error"; content: string };

const STORAGE_KEY = "prepulse_chat_history_v1";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // restore + persist history (per-tab, sessionStorage)
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) setMessages(JSON.parse(raw) as Message[]);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      // quota — ignore
    }
  }, [messages]);

  // auto-scroll to bottom on new messages
  useEffect(() => {
    if (!open) return;
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, open, busy]);

  async function handleSend(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || busy) return;
    const next: Message[] = [...messages, { role: "user", content: trimmed }];
    setMessages(next);
    setDraft("");
    setBusy(true);
    try {
      // build chat history for the backend (only user + assistant turns)
      const history: ChatTurn[] = next
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({ role: m.role as "user" | "assistant", content: m.content }));
      const resp = await sendChat(history);
      setMessages((cur) => [
        ...cur,
        {
          role: "assistant",
          content: resp.answer,
          is_in_scope: resp.is_in_scope,
          similarity: resp.similarity,
          decision_path: resp.decision_path,
          provider: resp.provider,
          model: resp.model,
        },
      ]);
    } catch (err) {
      const msg =
        err && typeof err === "object" && "body" in err
          ? extractErrorMessage((err as { body: unknown }).body)
          : err instanceof Error
            ? err.message
            : "Chat failed.";
      setMessages((cur) => [...cur, { role: "error", content: msg }]);
    } finally {
      setBusy(false);
    }
  }

  function clear() {
    setMessages([]);
  }

  return (
    <>
      <button
        type="button"
        aria-label={open ? "Close PrePulse assistant" : "Open PrePulse assistant"}
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-5 right-5 z-50 h-12 w-12 rounded-full bg-primary text-primary-foreground shadow-lg flex items-center justify-center hover:opacity-90 transition-opacity"
      >
        {open ? <X className="h-5 w-5" /> : <MessageSquare className="h-5 w-5" />}
      </button>

      {open && (
        <div className="fixed bottom-20 right-5 z-50 w-[min(420px,calc(100vw-2.5rem))] h-[min(640px,calc(100vh-7rem))] rounded-xl border bg-popover text-popover-foreground shadow-2xl flex flex-col overflow-hidden">
          <header className="flex items-center justify-between px-4 py-3 border-b bg-background">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" />
              <div>
                <div className="font-semibold text-sm">PrePulse Assistant</div>
                <div className="text-[11px] text-muted-foreground">
                  Answers from the product knowledge base
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={clear}
              className="text-[11px] text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
            >
              Clear
            </button>
          </header>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && <Suggestions onPick={(q) => setDraft(q)} />}
            {messages.map((m, idx) => (
              <Bubble key={idx} message={m} />
            ))}
            {busy && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-pulse" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-pulse [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground/60 animate-pulse [animation-delay:300ms]" />
                <span>thinking…</span>
              </div>
            )}
          </div>

          <form
            onSubmit={handleSend}
            className="border-t p-2 flex items-end gap-2 bg-background"
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about PrePulse… (Shift+Enter for newline)"
              maxLength={2000}
              rows={2}
              className="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              disabled={busy}
            />
            <button
              type="submit"
              disabled={busy || draft.trim().length === 0}
              className="h-9 w-9 shrink-0 rounded-md bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50"
              aria-label="Send"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}

function Bubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl bg-primary text-primary-foreground px-3 py-2 text-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }
  if (message.role === "error") {
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] rounded-2xl border border-rose-300 bg-rose-50 dark:bg-rose-950 dark:border-rose-700 px-3 py-2 text-xs text-rose-700 dark:text-rose-200">
          {message.content}
        </div>
      </div>
    );
  }
  // assistant
  const refusal = !message.is_in_scope;
  const gateLabel =
    message.decision_path === "similarity_low"
      ? "Filtered by similarity gate"
      : message.decision_path === "llm_refused"
        ? "Refused by model"
        : message.decision_path === "parse_failed"
          ? "Model output unparseable"
          : "Out of scope";
  return (
    <div className="flex justify-start">
      <div
        className={
          "max-w-[85%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap " +
          (refusal
            ? "border border-amber-300 bg-amber-50 dark:bg-amber-950 dark:border-amber-700 text-amber-900 dark:text-amber-100"
            : "bg-muted text-foreground")
        }
      >
        {refusal && (
          <div className="flex items-center gap-1.5 mb-1 text-[11px] uppercase tracking-wide font-semibold">
            <ShieldAlert className="h-3.5 w-3.5" />
            {gateLabel}
          </div>
        )}
        {message.content}
        <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground/80 font-mono">
          <span>sim {message.similarity.toFixed(2)}</span>
          <span>·</span>
          <span>{message.decision_path}</span>
          {message.provider && (
            <>
              <span>·</span>
              <span title={message.model || "unknown"}>
                {message.provider}
                {message.model ? ` (${message.model})` : ""}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Suggestions({ onPick }: { onPick: (q: string) => void }) {
  const items = [
    "What is PrePulse?",
    "How does the Remediator agent work?",
    "What's the posture score?",
    "Why are some defensive actions simulated?",
  ];
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        Ask me anything about the product. A few starters:
      </p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="text-[11px] rounded-full border bg-background hover:bg-muted px-2.5 py-1 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function extractErrorMessage(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const d = (body as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (d && typeof d === "object" && "reason" in d) {
      return String((d as { reason: unknown }).reason);
    }
  }
  return "Chat failed.";
}
