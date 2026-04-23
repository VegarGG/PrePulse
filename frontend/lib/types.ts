// TypeScript mirrors of backend/models/schemas.py (§9) plus the SSE event taxonomy (§12.1).

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
export type ActionSeverity = "critical" | "high" | "medium" | "low";
export type Industry =
  | "fintech"
  | "healthcare"
  | "e-commerce"
  | "manufacturing"
  | "legal"
  | "education"
  | "media"
  | "saas"
  | "other";

export interface CompanyProfile {
  company_name: string;
  domain: string;
  industry: Industry;
  employee_count: number;
  tech_stack: string[];
  ip_range: string | null;
}

export interface ThreatCampaign {
  pulse_id: string;
  title: string;
  description: string;
  threat_level: number;
  industry_targeted: string;
  tags: string[];
  first_seen: string;
}

export interface BreachRecord {
  breach_name: string;
  date: string;
  pwn_count: number;
  data_classes: string[];
}

export interface IPReputation {
  ip: string;
  abuse_confidence: number;
  country: string | null;
  usage_type: string | null;
  total_reports: number;
}

export interface IntelligenceReport {
  domain: string;
  active_campaigns: ThreatCampaign[];
  domain_breached: boolean;
  breach_count: number;
  breaches: BreachRecord[];
  suspicious_ips: IPReputation[];
  raw_summary: string;
  confidence: number;
}

export interface CVEFinding {
  cve_id: string;
  severity: Severity;
  cvss_score: number | null;
  description: string;
  affected_product: string;
  exploit_available: boolean;
  published: string;
}

export interface MitreTechnique {
  technique_id: string;
  technique_name: string;
  tactic: string;
  description: string;
  similarity_score: number;
}

export interface ValidationReport {
  cves_found: CVEFinding[];
  mitre_techniques: MitreTechnique[];
  exploitable_count: number;
  validation_summary: string;
  confidence: number;
}

export type HardeningKind =
  | "mtd_port_rotation"
  | "mtd_cert_refresh"
  | "attack_surface_reduction"
  | "identity_posture_tightening";

export interface HardeningAction {
  action_id: string;
  kind: HardeningKind;
  description: string;
  target: string;
  simulated: boolean;
  executed_at: string | null;
  expected_impact: string;
}

export interface HardeningReport {
  actions_taken: HardeningAction[];
  rationale: string;
  risk_reduction_estimate: number;
}

export interface CriticalFinding {
  headline: string;
  detail: string;
  linked_cves: string[];
  linked_techniques: string[];
  severity: ActionSeverity;
}

export interface RecommendedAction {
  priority: number;
  description: string;
  estimated_effort: "<1h" | "<1d" | "<1w" | ">1w";
  owner_suggestion: "it_admin" | "security_engineer" | "executive" | "vendor";
}

export type PostureGrade = "A" | "B" | "C" | "D" | "F";

export interface FinalReport {
  posture_score: number;
  posture_grade: PostureGrade;
  score_explanation: string;
  critical_findings: CriticalFinding[];
  recommended_actions: RecommendedAction[];
  executive_summary: string;
  what_prepulse_would_do: string;
}

export type RemediationKind =
  | "firewall.block_ip"
  | "firewall.block_range"
  | "iam.force_mfa"
  | "iam.rotate_credentials"
  | "iam.disable_user"
  | "endpoint.isolate"
  | "endpoint.quarantine_file"
  | "ticketing.open_incident"
  | "email.notify_admin";

export interface RemediationAction {
  action_id: string;
  kind: RemediationKind;
  severity: ActionSeverity;
  args: Record<string, unknown>;
  requires_approval: boolean;
  approved: boolean | null;
  executed: boolean;
  executed_at: string | null;
  result_summary: string | null;
}

export interface RemediationReport {
  actions: RemediationAction[];
  actions_approved: number;
  actions_executed: number;
  actions_rejected: number;
  incident_ticket_id: string | null;
}

export interface ConfidenceFlag {
  agent: string;
  reason: string;
  severity: "warning" | "error";
  suggested_human_review: boolean;
}

export interface SupervisorReport {
  overall_confidence: number;
  flags: ConfidenceFlag[];
  policy_violations: string[];
  escalated_to_human: boolean;
  audit_trail_id: string;
  sign_off: "approved" | "conditional" | "escalate";
}

export interface PipelineState {
  scan_id: string;
  started_at: string;
  profile: CompanyProfile;
  intel_report: IntelligenceReport | null;
  validation_report: ValidationReport | null;
  hardening_report: HardeningReport | null;
  final_report: FinalReport | null;
  remediation_report: RemediationReport | null;
  supervisor_report: SupervisorReport | null;
  completed_at: string | null;
  error: string | null;
}

// ---------- SSE event taxonomy (§12.1) ----------

export type EventType =
  | "scan.started"
  | "scan.completed"
  | "scan.failed"
  | "agent.started"
  | "agent.thinking"
  | "agent.completed"
  | "tool.called"
  | "tool.result"
  | "action.pending"
  | "action.approved"
  | "action.rejected"
  | "action.executed"
  | "confidence.flagged"
  | "input.rejected";

export interface ScanEvent {
  type: EventType;
  ts: number;
  scan_id: string;
  payload: Record<string, unknown>;
}

// ---------- Dashboard metrics (§18.3) ----------

export interface DashboardMetrics {
  rolling: {
    total_scans: number;
    threats_detected: number;
    actions_executed: number;
    avg_posture_score: number;
    mean_time_to_contain_s: number;
  };
  series: {
    posture_30d: Array<{
      scan_id: string;
      ts: string;
      posture_score: number | null;
      grade: PostureGrade | null;
    }>;
    severities_30d: Partial<Record<Severity, number>>;
    actions_30d: Record<string, number>;
  };
  top_tactics: Array<{
    technique_id: string;
    technique_name: string;
    tactic: string;
    count: number;
  }>;
  agent_stats: Array<{
    agent: string;
    calls: number;
    avg_latency_ms: number;
  }>;
}

export interface DemoProfileSummary {
  profile_id: string;
  company_name: string;
  industry: Industry;
  domain: string;
  employee_count: number;
  expected_posture_score: number;
  narrative: string;
}

export interface ScanListRow {
  scan_id: string;
  started_at: string;
  completed_at: string | null;
  company_name: string;
  industry: string;
  posture_score: number | null;
  posture_grade: PostureGrade | null;
  error: string | null;
}

// ---------- Run-console reducer state (§18.2) ----------

export type AgentName =
  | "intelligence"
  | "validator"
  | "hardening"
  | "investigator"
  | "remediator"
  | "supervisor";

export interface ToolCallRecord {
  call_id: string;
  tool: string;
  category: "read" | "action" | "meta";
  args: Record<string, unknown>;
  mode: "live" | "mock";
  started_at: number;
  duration_ms?: number;
  ok?: boolean;
  result?: unknown;
  error?: string;
}

export interface AgentState {
  name: AgentName;
  status: "idle" | "running" | "thinking" | "completed" | "errored";
  tool_calls: ToolCallRecord[];
  report_summary: string | null;
}

export interface ActionPending {
  action_id: string;
  action: string;
  severity: ActionSeverity;
  args: Record<string, unknown>;
}

export interface ScanReducerState {
  scan_id: string;
  agents: Record<AgentName, AgentState>;
  events: ScanEvent[];
  pendingAction: ActionPending | null;
  final: FinalReport | null;
  status: "idle" | "running" | "completed" | "failed";
  error: string | null;
}

export const AGENT_ORDER: AgentName[] = [
  "intelligence",
  "validator",
  "hardening",
  "investigator",
  "remediator",
  "supervisor",
];

export const AGENT_COLORS: Record<AgentName, string> = {
  intelligence: "bg-blue-500",
  validator: "bg-violet-500",
  hardening: "bg-teal-500",
  investigator: "bg-amber-500",
  remediator: "bg-rose-500",
  supervisor: "bg-emerald-500",
};

export const AGENT_TEXT_COLORS: Record<AgentName, string> = {
  intelligence: "text-blue-700 dark:text-blue-400",
  validator: "text-violet-700 dark:text-violet-400",
  hardening: "text-teal-700 dark:text-teal-400",
  investigator: "text-amber-700 dark:text-amber-400",
  remediator: "text-rose-700 dark:text-rose-400",
  supervisor: "text-emerald-700 dark:text-emerald-400",
};
