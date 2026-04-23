"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { ActionPending } from "@/lib/types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-rose-600",
  high: "text-orange-600",
  medium: "text-yellow-600",
  low: "text-blue-600",
};

export function ActionApprovalModal({
  pending,
  onApprove,
  onReject,
}: {
  pending: ActionPending | null;
  onApprove: (actionId: string) => Promise<void>;
  onReject: (actionId: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const open = pending !== null;

  async function handle(fn: (id: string) => Promise<void>) {
    if (!pending || busy) return;
    setBusy(true);
    try {
      await fn(pending.action_id);
    } finally {
      setBusy(false);
    }
  }

  // Treat X click / Escape / outside-click as a reject so the orchestrator's
  // awaiting future gets resolved rather than leaving the scan hung.
  const handleOpenChange = (next: boolean) => {
    if (!next && pending && !busy) {
      handle(onReject);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] flex flex-col overflow-hidden">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-rose-600 shrink-0" />
            <DialogTitle>Human approval required</DialogTitle>
          </div>
          <DialogDescription>
            PrePulse is about to execute a simulated defensive action. Review the details and
            approve or reject.
          </DialogDescription>
        </DialogHeader>

        {pending && (
          <div className="flex-1 min-h-0 overflow-y-auto -mx-4 px-4">
            <div className="rounded-md border bg-muted/40 p-3 space-y-3">
              <Field label="Action">
                <code className="font-mono text-sm break-all">{pending.action}</code>
              </Field>
              <Field label="Severity">
                <span
                  className={`text-sm font-semibold uppercase ${
                    SEVERITY_COLOR[pending.severity] ?? "text-foreground"
                  }`}
                >
                  {pending.severity}
                </span>
              </Field>
              <Field label="Action id">
                <code className="font-mono text-xs break-all">{pending.action_id}</code>
              </Field>
              <ArgumentsBlock args={pending.args} />
            </div>
            <p className="text-xs text-muted-foreground mt-3">
              In this prototype every action is simulated — no real infrastructure is mutated.
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" disabled={busy} onClick={() => handle(onReject)}>
            Reject
          </Button>
          <Button
            className="bg-rose-600 hover:bg-rose-700 text-white"
            disabled={busy}
            onClick={() => handle(onApprove)}
          >
            {busy ? "Working…" : "Approve & execute"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 items-baseline min-w-0">
      <span className="text-xs text-muted-foreground shrink-0">{label}</span>
      <div className="min-w-0 break-words">{children}</div>
    </div>
  );
}

function ArgumentsBlock({ args }: { args: Record<string, unknown> }) {
  const entries = Object.entries(args);
  if (entries.length === 0) {
    return (
      <Field label="Arguments">
        <span className="text-xs text-muted-foreground italic">(no arguments)</span>
      </Field>
    );
  }
  return (
    <div className="space-y-2 min-w-0">
      <div className="text-xs text-muted-foreground">Arguments</div>
      <dl className="space-y-2 min-w-0">
        {entries.map(([key, value]) => (
          <ArgumentRow key={key} label={key} value={value} />
        ))}
      </dl>
    </div>
  );
}

function ArgumentRow({ label, value }: { label: string; value: unknown }) {
  const asString =
    typeof value === "string" ? value : JSON.stringify(value, null, 2);
  const isMultiline = asString.length > 120 || asString.includes("\n");

  return (
    <div className="min-w-0">
      <dt className="text-[11px] font-mono text-muted-foreground mb-0.5">{label}</dt>
      <dd className="min-w-0">
        {isMultiline ? (
          <pre className="rounded bg-background border p-2 text-[11px] leading-relaxed font-mono whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
            {asString}
          </pre>
        ) : (
          <code className="text-xs font-mono break-all">{asString}</code>
        )}
      </dd>
    </div>
  );
}
