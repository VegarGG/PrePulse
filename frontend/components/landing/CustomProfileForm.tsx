"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { CompanyProfile, Industry } from "@/lib/types";

const INDUSTRIES: Industry[] = [
  "fintech",
  "healthcare",
  "e-commerce",
  "manufacturing",
  "legal",
  "education",
  "media",
  "saas",
  "other",
];

export function CustomProfileForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (profile: CompanyProfile) => void;
  submitting?: boolean;
}) {
  const [company, setCompany] = useState("");
  const [domain, setDomain] = useState("");
  const [industry, setIndustry] = useState<Industry>("saas");
  const [employees, setEmployees] = useState(50);
  const [techStack, setTechStack] = useState("");
  const [ipRange, setIpRange] = useState("");

  const canSubmit =
    company.trim().length > 0 &&
    domain.trim().length > 0 &&
    employees > 0 &&
    !submitting;

  const fieldClass =
    "w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Or scan a custom company</CardTitle>
        <CardDescription>
          Enter the profile of a company you&apos;d like PrePulse to assess.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit({
              company_name: company.trim(),
              domain: domain.trim(),
              industry,
              employee_count: employees,
              tech_stack: techStack
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
              ip_range: ipRange.trim() || null,
            });
          }}
        >
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Company name
            <input
              className={fieldClass}
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              required
              maxLength={128}
              placeholder="Acme Financial"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Primary domain
            <input
              className={fieldClass}
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              required
              placeholder="acme.test"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Industry
            <select
              className={fieldClass}
              value={industry}
              onChange={(e) => setIndustry(e.target.value as Industry)}
            >
              {INDUSTRIES.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground">
            Employee count
            <input
              className={fieldClass}
              type="number"
              min={1}
              max={5000}
              value={employees}
              onChange={(e) => setEmployees(Number(e.target.value))}
              required
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground md:col-span-2">
            Tech stack (comma-separated)
            <input
              className={fieldClass}
              value={techStack}
              onChange={(e) => setTechStack(e.target.value)}
              placeholder="AWS Lambda, PostgreSQL, Stripe"
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-muted-foreground md:col-span-2">
            IP range (optional CIDR)
            <input
              className={fieldClass}
              value={ipRange}
              onChange={(e) => setIpRange(e.target.value)}
              placeholder="198.51.100.0/24"
            />
          </label>

          <Separator className="md:col-span-2 my-2" />

          <div className="md:col-span-2 flex justify-end">
            <Button type="submit" disabled={!canSubmit}>
              {submitting ? "Starting…" : "Run custom assessment"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
