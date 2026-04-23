"use client";

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
import type { CVEFinding, Severity } from "@/lib/types";

const SEV_COLOR: Record<Severity, string> = {
  CRITICAL: "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200",
  HIGH: "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200",
  MEDIUM: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200",
  LOW: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200",
  INFO: "bg-muted text-muted-foreground",
};

export function CveTable({ cves }: { cves: CVEFinding[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Validated vulnerabilities</CardTitle>
        <CardDescription>
          {cves.length === 0
            ? "No CVEs validated against this tech stack yet."
            : `${cves.length} CVE${cves.length === 1 ? "" : "s"} matched the declared products.`}
        </CardDescription>
      </CardHeader>
      {cves.length > 0 && (
        <CardContent className="pt-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[130px]">CVE</TableHead>
                <TableHead className="w-[110px]">Severity</TableHead>
                <TableHead className="w-[80px]">CVSS</TableHead>
                <TableHead className="w-[100px]">Exploit</TableHead>
                <TableHead>Product</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cves.map((c) => (
                <TableRow key={c.cve_id}>
                  <TableCell className="font-mono text-xs">{c.cve_id}</TableCell>
                  <TableCell>
                    <Badge className={SEV_COLOR[c.severity]}>{c.severity}</Badge>
                  </TableCell>
                  <TableCell className="tabular-nums">
                    {c.cvss_score?.toFixed(1) ?? "—"}
                  </TableCell>
                  <TableCell>
                    {c.exploit_available ? (
                      <span className="text-xs text-rose-600 font-medium">in-the-wild</span>
                    ) : (
                      <span className="text-xs text-muted-foreground">no</span>
                    )}
                  </TableCell>
                  <TableCell className="text-xs">{c.affected_product}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      )}
    </Card>
  );
}
