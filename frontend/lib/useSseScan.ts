"use client";

import { useEffect, useReducer } from "react";
import {
  AGENT_ORDER,
  type ActionPending,
  type AgentName,
  type AgentState,
  type FinalReport,
  type ScanEvent,
  type ScanReducerState,
  type ToolCallRecord,
} from "./types";
import { sseUrl } from "./api";

const EMPTY_AGENTS = (): Record<AgentName, AgentState> => {
  const out = {} as Record<AgentName, AgentState>;
  for (const name of AGENT_ORDER) {
    out[name] = {
      name,
      status: "idle",
      tool_calls: [],
      report_summary: null,
    };
  }
  return out;
};

function initialState(scanId: string): ScanReducerState {
  return {
    scan_id: scanId,
    agents: EMPTY_AGENTS(),
    events: [],
    pendingAction: null,
    final: null,
    status: "idle",
    error: null,
  };
}

function reducer(state: ScanReducerState, evt: ScanEvent): ScanReducerState {
  const next: ScanReducerState = {
    ...state,
    events: [...state.events, evt],
  };
  const payload = evt.payload;

  switch (evt.type) {
    case "scan.started":
      return { ...next, status: "running" };

    case "scan.completed": {
      const finalReport = (payload.final_report as FinalReport | null) ?? null;
      return { ...next, status: "completed", final: finalReport };
    }

    case "scan.failed":
      return {
        ...next,
        status: "failed",
        error: String(payload.error ?? "unknown error"),
      };

    case "agent.started": {
      const name = payload.agent as AgentName;
      if (!(name in state.agents)) return next;
      return {
        ...next,
        agents: {
          ...state.agents,
          [name]: { ...state.agents[name], status: "running" },
        },
      };
    }

    case "agent.thinking": {
      const name = payload.agent as AgentName;
      if (!(name in state.agents)) return next;
      return {
        ...next,
        agents: {
          ...state.agents,
          [name]: { ...state.agents[name], status: "thinking" },
        },
      };
    }

    case "agent.completed": {
      const name = payload.agent as AgentName;
      if (!(name in state.agents)) return next;
      return {
        ...next,
        agents: {
          ...state.agents,
          [name]: {
            ...state.agents[name],
            status: "completed",
            report_summary: String(payload.report_summary ?? ""),
          },
        },
      };
    }

    case "tool.called": {
      const agent = _agentForTool(state, payload.tool as string);
      if (!agent) return next;
      const record: ToolCallRecord = {
        call_id: String(payload.call_id),
        tool: String(payload.tool),
        category: (payload.category as ToolCallRecord["category"]) ?? "read",
        args: (payload.args as Record<string, unknown>) ?? {},
        mode: (payload.mode as ToolCallRecord["mode"]) ?? "mock",
        started_at: evt.ts,
      };
      return {
        ...next,
        agents: {
          ...state.agents,
          [agent]: {
            ...state.agents[agent],
            tool_calls: [...state.agents[agent].tool_calls, record],
          },
        },
      };
    }

    case "tool.result": {
      const agent = _agentForCallId(state, String(payload.call_id));
      if (!agent) return next;
      const agentState = state.agents[agent];
      return {
        ...next,
        agents: {
          ...state.agents,
          [agent]: {
            ...agentState,
            tool_calls: agentState.tool_calls.map((t) =>
              t.call_id === payload.call_id
                ? {
                    ...t,
                    duration_ms: Number(payload.duration_ms ?? 0),
                    ok: Boolean(payload.ok),
                    result: payload.result,
                    error: payload.error ? String(payload.error) : undefined,
                  }
                : t,
            ),
          },
        },
      };
    }

    case "action.pending": {
      const pending: ActionPending = {
        action_id: String(payload.action_id),
        action: String(payload.action),
        severity: payload.severity as ActionPending["severity"],
        args: (payload.args as Record<string, unknown>) ?? {},
      };
      return { ...next, pendingAction: pending };
    }

    case "action.approved":
    case "action.rejected":
      return { ...next, pendingAction: null };

    case "action.executed":
      return next;

    default:
      return next;
  }
}

function _agentForTool(state: ScanReducerState, tool: string): AgentName | null {
  // best-effort: assign tool.called to the agent currently running/thinking
  const active = AGENT_ORDER.find(
    (a) => state.agents[a].status === "running" || state.agents[a].status === "thinking",
  );
  return active ?? null;
  void tool;
}

function _agentForCallId(state: ScanReducerState, callId: string): AgentName | null {
  for (const name of AGENT_ORDER) {
    if (state.agents[name].tool_calls.some((t) => t.call_id === callId)) {
      return name;
    }
  }
  return null;
}

export interface UseSseScan extends ScanReducerState {
  retry: () => void;
}

export function useSseScan(scanId: string | null): UseSseScan {
  const [state, dispatch] = useReducer(
    reducer,
    scanId ?? "",
    initialState,
  );

  useEffect(() => {
    if (!scanId) return;
    let cancelled = false;
    const es = new EventSource(sseUrl(scanId));

    const onMessage = (raw: MessageEvent) => {
      if (cancelled) return;
      try {
        const parsed = JSON.parse(raw.data) as ScanEvent;
        dispatch(parsed);
        if (parsed.type === "scan.completed" || parsed.type === "scan.failed") {
          es.close();
        }
      } catch (err) {
        console.error("bad SSE frame", err);
      }
    };

    const handled = [
      "scan.started",
      "scan.completed",
      "scan.failed",
      "agent.started",
      "agent.thinking",
      "agent.completed",
      "tool.called",
      "tool.result",
      "action.pending",
      "action.approved",
      "action.rejected",
      "action.executed",
      "confidence.flagged",
      "input.rejected",
    ];
    handled.forEach((t) => es.addEventListener(t, onMessage as EventListener));
    es.onmessage = onMessage;

    return () => {
      cancelled = true;
      es.close();
    };
  }, [scanId]);

  // No-op retry — native EventSource auto-reconnects on transient errors.
  const retry = () => {};

  return { ...state, retry };
}
