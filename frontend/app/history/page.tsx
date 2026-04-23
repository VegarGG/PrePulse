"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listScans } from "@/lib/api";
import type { PostureGrade, ScanListRow } from "@/lib/types";

const GRADE_COLOR: Record<PostureGrade, string> = {
  A: "bg-emerald-600 hover:bg-emerald-600",
  B: "bg-green-600 hover:bg-green-600",
  C: "bg-yellow-600 hover:bg-yellow-600",
  D: "bg-orange-600 hover:bg-orange-600",
  F: "bg-rose-600 hover:bg-rose-600",
};

export default function HistoryPage() {
  const [rows, setRows] = useState<ScanListRow[] | null>(null);

  useEffect(() => {
    const load = () => listScans().then(setRows).catch(() => setRows([]));
    load();
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">History</h1>
        <p className="text-sm text-muted-foreground">
          Every scan executed in this session. Click a scan to reopen the run console.
        </p>
      </header>

      {rows === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : rows.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No scans yet</CardTitle>
            <CardDescription>
              Kick off a scan from the landing page — it will appear here and in the dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/" className="text-sm underline">
              Go to landing →
            </Link>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Started</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r) => (
                  <TableRow key={r.scan_id}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {new Date(r.started_at).toLocaleTimeString()}
                    </TableCell>
                    <TableCell className="font-medium">{r.company_name}</TableCell>
                    <TableCell className="capitalize text-xs text-muted-foreground">
                      {r.industry}
                    </TableCell>
                    <TableCell className="tabular-nums">{r.posture_score ?? "—"}</TableCell>
                    <TableCell>
                      {r.posture_grade ? (
                        <Badge className={GRADE_COLOR[r.posture_grade]}>
                          {r.posture_grade}
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {r.error ? (
                        <Badge variant="destructive">failed</Badge>
                      ) : r.completed_at ? (
                        <Badge className="bg-emerald-600 hover:bg-emerald-600">done</Badge>
                      ) : (
                        <Badge className="bg-blue-600 hover:bg-blue-600">running</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right space-x-3 text-xs">
                      <Link href={`/run/${r.scan_id}`} className="underline">
                        run
                      </Link>
                      <Link href={`/trace/${r.scan_id}`} className="underline">
                        trace
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
