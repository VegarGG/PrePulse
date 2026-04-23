"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ProfilePicker } from "@/components/landing/ProfilePicker";
import { CustomProfileForm } from "@/components/landing/CustomProfileForm";
import { getHealth, listProfiles, startScan } from "@/lib/api";
import type { CompanyProfile, DemoProfileSummary } from "@/lib/types";

type HealthPayload = { status: string; version: string; mode: string };

type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthPayload }
  | { kind: "error"; message: string };

export default function Home() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthState>({ kind: "loading" });
  const [profiles, setProfiles] = useState<DemoProfileSummary[]>([]);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [submittingCustom, setSubmittingCustom] = useState(false);

  useEffect(() => {
    getHealth()
      .then((data) => setHealth({ kind: "ok", data }))
      .catch((err: Error) => setHealth({ kind: "error", message: err.message }));
    listProfiles()
      .then(setProfiles)
      .catch(() => {
        // profiles endpoint shape will tell the user via the profile picker
      });
  }, []);

  async function handleRun(profileId: string) {
    setLoadingId(profileId);
    try {
      const { scan_id } = await startScan({ profile_id: profileId });
      router.push(`/run/${scan_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Scan failed to start";
      toast.error(message);
      setLoadingId(null);
    }
  }

  async function handleCustom(profile: CompanyProfile) {
    setSubmittingCustom(true);
    try {
      const { scan_id } = await startScan({ custom_profile: profile });
      router.push(`/run/${scan_id}`);
    } catch (err) {
      const body =
        err && typeof err === "object" && "body" in err
          ? (err as { body: unknown }).body
          : null;
      const detail =
        body && typeof body === "object" && "detail" in body
          ? (body as { detail: unknown }).detail
          : null;
      const reason =
        detail && typeof detail === "object" && "reason" in detail
          ? String((detail as { reason: unknown }).reason)
          : err instanceof Error
            ? err.message
            : "unknown error";
      toast.error(`Custom scan rejected: ${reason}`);
      setSubmittingCustom(false);
    }
  }

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold tracking-tight">PrePulse</h1>
            <p className="text-muted-foreground max-w-2xl">
              Preemptive, agentic-AI cybersecurity intelligence for small and mid-market
              organizations. A six-agent fleet identifies threats, validates exposure, and
              stages defensive actions before an attack lands.
            </p>
          </div>
          <HealthBadge state={health} />
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Run a showcase scan</h2>
        <ProfilePicker profiles={profiles} onSelect={handleRun} loadingId={loadingId} />
      </section>

      <section>
        <CustomProfileForm onSubmit={handleCustom} submitting={submittingCustom} />
      </section>

      <section>
        <Card>
          <CardHeader>
            <CardTitle>How it works</CardTitle>
            <CardDescription>
              Six specialized agents coordinate through LangGraph. Reasoning is live; defensive
              actions are simulated and logged.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground grid md:grid-cols-3 gap-4">
            <div>
              <span className="font-medium text-foreground">1. Observe.</span> Intelligence &
              Validator survey the external threat landscape and exploit surface.
            </div>
            <div>
              <span className="font-medium text-foreground">2. Defend.</span> Hardening rotates
              attack surface preemptively; Investigator synthesizes the briefing.
            </div>
            <div>
              <span className="font-medium text-foreground">3. Contain.</span> Remediator
              plans containment — destructive actions gated on human approval — and Supervisor
              signs off or escalates.
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function HealthBadge({ state }: { state: HealthState }) {
  if (state.kind === "loading")
    return <Badge variant="secondary">checking backend…</Badge>;
  if (state.kind === "error")
    return (
      <Badge variant="destructive" title={state.message}>
        backend unreachable
      </Badge>
    );
  return (
    <Badge className="bg-emerald-600 hover:bg-emerald-600" title={`v${state.data.version}`}>
      backend {state.data.status} · {state.data.mode}
    </Badge>
  );
}
