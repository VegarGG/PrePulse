"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Download } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { TraceViewer } from "@/components/trace/TraceViewer";
import { getTrace, traceDownloadUrl } from "@/lib/api";

export default function TracePage() {
  const params = useParams<{ scanId: string }>();
  const scanId = params.scanId;
  const [ndjson, setNdjson] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getTrace(scanId)
      .then(setNdjson)
      .catch((e: Error) => setErr(e.message));
  }, [scanId]);

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Trace{" "}
            <span className="font-mono text-base text-muted-foreground">{scanId}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            Downloadable NDJSON of every event emitted during the scan.
          </p>
        </div>
        <a
          href={traceDownloadUrl(scanId)}
          target="_blank"
          rel="noopener noreferrer"
          download
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          <Download className="mr-1 h-4 w-4" />
          Download NDJSON
        </a>
      </header>

      {err && (
        <p className="text-sm text-rose-600">Failed to load trace: {err}</p>
      )}
      {ndjson && <TraceViewer ndjson={ndjson} />}
    </div>
  );
}
