"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Download, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentTimeline } from "@/components/run/AgentTimeline";
import { EventFeed } from "@/components/run/EventFeed";
import { ThreatCardGrid } from "@/components/run/ThreatCardGrid";
import { CveTable } from "@/components/run/CveTable";
import { TacticHeatmap } from "@/components/run/TacticHeatmap";
import { ActionApprovalModal } from "@/components/run/ActionApprovalModal";
import { ExecutiveBriefing } from "@/components/run/ExecutiveBriefing";
import { PostureGauge } from "@/components/common/PostureGauge";
import { approveAction, getScan, rejectAction, traceDownloadUrl } from "@/lib/api";
import { useSseScan } from "@/lib/useSseScan";
import type { PipelineState } from "@/lib/types";

export default function RunPage() {
  const params = useParams<{ scanId: string }>();
  const scanId = params.scanId;
  const scan = useSseScan(scanId);
  const [state, setState] = useState<PipelineState | null>(null);

  // Poll for the pipeline state on completion so we can render the full reports
  useEffect(() => {
    if (scan.status === "completed" || scan.status === "failed") {
      getScan(scanId)
        .then(setState)
        .catch(() => {
          // ignore — the SSE final payload already carries the summary
        });
    }
  }, [scan.status, scanId]);

  const handleApprove = async (actionId: string) => {
    try {
      await approveAction(scanId, actionId);
      toast.success(`Approved ${actionId}`);
    } catch (err) {
      toast.error(`Approve failed: ${(err as Error).message}`);
    }
  };
  const handleReject = async (actionId: string) => {
    try {
      await rejectAction(scanId, actionId);
      toast.message(`Rejected ${actionId}`);
    } catch (err) {
      toast.error(`Reject failed: ${(err as Error).message}`);
    }
  };

  const intel = state?.intel_report ?? null;
  const validation = state?.validation_report ?? null;
  const finalReport = scan.final ?? state?.final_report ?? null;

  const activeAgent =
    (scan.status === "running" &&
      (Object.values(scan.agents).find(
        (a) => a.status === "running" || a.status === "thinking",
      )?.name ?? null)) ||
    null;

  return (
    <div className="space-y-6">
      <section className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Live scan{" "}
            <span className="font-mono text-base text-muted-foreground">{scanId}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            {scan.status === "running" && (
              <>Streaming events · {activeAgent ?? "warming up"}…</>
            )}
            {scan.status === "completed" && <>Scan completed · {scan.events.length} events</>}
            {scan.status === "failed" && <>Scan failed · {scan.error}</>}
            {scan.status === "idle" && <>Connecting…</>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={scan.status} />
          <Link
            href={`/trace/${scanId}`}
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            <FileText className="mr-1 h-4 w-4" />
            Trace
          </Link>
          <a
            href={traceDownloadUrl(scanId)}
            target="_blank"
            rel="noopener noreferrer"
            download
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            <Download className="mr-1 h-4 w-4" />
            Download
          </a>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent fleet</CardTitle>
              <CardDescription>Lifecycle events stream in over SSE.</CardDescription>
            </CardHeader>
            <CardContent>
              <AgentTimeline agents={scan.agents} pendingAgent={scan.pendingAction ? "remediator" : null} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Event feed</CardTitle>
              <CardDescription>Latest events across all agents.</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <EventFeed events={scan.events} />
            </CardContent>
          </Card>
        </section>

        <section className="lg:col-span-7 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Posture</CardTitle>
                  <CardDescription>
                    Deterministic score computed by the engine after Investigator completes.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <PostureGauge
                score={finalReport?.posture_score ?? null}
                grade={finalReport?.posture_grade ?? null}
              />
            </CardContent>
          </Card>

          <ThreatCardGrid campaigns={intel?.active_campaigns ?? []} />
          <CveTable cves={validation?.cves_found ?? []} />
          <TacticHeatmap techniques={validation?.mitre_techniques ?? []} />
          <ExecutiveBriefing report={finalReport} />
        </section>
      </div>

      <ActionApprovalModal
        pending={scan.pendingAction}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
}

function StatusBadge({ status }: { status: "idle" | "running" | "completed" | "failed" }) {
  if (status === "running")
    return <Badge className="bg-blue-600 hover:bg-blue-600">running</Badge>;
  if (status === "completed")
    return <Badge className="bg-emerald-600 hover:bg-emerald-600">completed</Badge>;
  if (status === "failed") return <Badge variant="destructive">failed</Badge>;
  return <Badge variant="secondary">connecting</Badge>;
}
