"""BaseAgent — shared LLM call + tool-use loop + structured-output parser.

Anthropic tool names must match ^[a-zA-Z0-9_-]{1,64}$ (no dots), so each of
our dotted tool names (e.g. `otx.get_pulses`) is exposed to the LLM under an
underscore alias (`otx_get_pulses`) and mapped back when dispatching.
"""

from __future__ import annotations

import json
from typing import Any, Type

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, ValidationError

from backend.events import emit
from backend.llm import get_llm
from backend.tools.base import TOOLS

# Real dotted tool name ↔ Anthropic-safe alias (first dot → underscore)
REAL_TO_ALIAS = {
    "otx.get_pulses": "otx_get_pulses",
    "hibp.check_domain": "hibp_check_domain",
    "abuseipdb.check_ip": "abuseipdb_check_ip",
    "nvd.query_cves": "nvd_query_cves",
    "mitre.match_techniques": "mitre_match_techniques",
    "firewall.block_ip": "firewall_block_ip",
    "firewall.block_range": "firewall_block_range",
    "iam.force_mfa": "iam_force_mfa",
    "iam.rotate_credentials": "iam_rotate_credentials",
    "iam.disable_user": "iam_disable_user",
    "endpoint.isolate": "endpoint_isolate",
    "endpoint.quarantine_file": "endpoint_quarantine_file",
    "mtd.rotate_port_map": "mtd_rotate_port_map",
    "mtd.refresh_certs": "mtd_refresh_certs",
    "ticketing.open_incident": "ticketing_open_incident",
    "email.notify_admin": "email_notify_admin",
    "policy.check": "policy_check",
    "audit.log_decision": "audit_log_decision",
}
ALIAS_TO_REAL = {v: k for k, v in REAL_TO_ALIAS.items()}

TOOL_SCHEMAS: dict[str, dict] = {
    "otx.get_pulses": {
        "description": "Return the N most recent threat campaigns matching the given industry.",
        "parameters": {
            "type": "object",
            "properties": {
                "industry": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["industry"],
        },
    },
    "hibp.check_domain": {
        "description": "Return breach history for the given corporate domain.",
        "parameters": {
            "type": "object",
            "properties": {"domain": {"type": "string"}},
            "required": ["domain"],
        },
    },
    "abuseipdb.check_ip": {
        "description": "Return reputation data for a single IP.",
        "parameters": {
            "type": "object",
            "properties": {
                "ip": {"type": "string"},
                "max_age_days": {"type": "integer", "default": 90},
            },
            "required": ["ip"],
        },
    },
    "nvd.query_cves": {
        "description": "Return recent CVEs affecting the given product name.",
        "parameters": {
            "type": "object",
            "properties": {
                "software": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["software"],
        },
    },
    "mitre.match_techniques": {
        "description": "Return the top-k MITRE ATT&CK techniques semantically similar to the description.",
        "parameters": {
            "type": "object",
            "properties": {
                "threat_description": {"type": "string"},
                "k": {"type": "integer", "default": 3},
            },
            "required": ["threat_description"],
        },
    },
    "firewall.block_ip": {
        "description": "Simulate blocking an IP at the perimeter firewall.",
        "parameters": {
            "type": "object",
            "properties": {
                "ip": {"type": "string"},
                "reason": {"type": "string"},
                "duration_hours": {"type": "integer", "default": 24},
            },
            "required": ["ip", "reason"],
        },
    },
    "firewall.block_range": {
        "description": "Simulate blocking a CIDR range at the perimeter.",
        "parameters": {
            "type": "object",
            "properties": {
                "cidr": {"type": "string"},
                "reason": {"type": "string"},
                "duration_hours": {"type": "integer", "default": 24},
            },
            "required": ["cidr", "reason"],
        },
    },
    "iam.force_mfa": {
        "description": "Simulate enforcing MFA on the given IAM scope.",
        "parameters": {
            "type": "object",
            "properties": {"scope": {"type": "string"}},
            "required": ["scope"],
        },
    },
    "iam.rotate_credentials": {
        "description": "Simulate rotating IAM credentials for the given scope.",
        "parameters": {
            "type": "object",
            "properties": {"scope": {"type": "string"}},
            "required": ["scope"],
        },
    },
    "iam.disable_user": {
        "description": "Simulate disabling a specific user account.",
        "parameters": {
            "type": "object",
            "properties": {"user": {"type": "string"}},
            "required": ["user"],
        },
    },
    "endpoint.isolate": {
        "description": "Simulate isolating an endpoint from the network.",
        "parameters": {
            "type": "object",
            "properties": {"host": {"type": "string"}},
            "required": ["host"],
        },
    },
    "endpoint.quarantine_file": {
        "description": "Simulate quarantining a suspicious file on an endpoint.",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["host", "path"],
        },
    },
    "mtd.rotate_port_map": {
        "description": "Simulate shuffling exposed service port mappings (moving-target defense).",
        "parameters": {"type": "object", "properties": {}},
    },
    "mtd.refresh_certs": {
        "description": "Simulate refreshing TLS certificates across the fleet.",
        "parameters": {"type": "object", "properties": {}},
    },
    "ticketing.open_incident": {
        "description": "Simulate opening an incident ticket in the ticketing system.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "severity": {"type": "string"},
                "details": {"type": "string"},
            },
            "required": ["title", "severity", "details"],
        },
    },
    "email.notify_admin": {
        "description": "Simulate sending an email notification to the admin distribution list.",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["subject", "body"],
        },
    },
    "policy.check": {
        "description": "Run deterministic policy checks over a list of proposed remediation actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_list": {
                    "type": "array",
                    "items": {"type": "object"},
                }
            },
            "required": ["action_list"],
        },
    },
    "audit.log_decision": {
        "description": "Record the supervisor's sign-off in the immutable audit store.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "sign_off": {"type": "string"},
            },
            "required": ["summary", "sign_off"],
        },
    },
}


def _format_instructions(schema: Type[BaseModel]) -> str:
    """Emit JSON schema + strict formatting guidance for the final message."""
    return (
        "Return ONLY a JSON object matching this schema, with no preamble and no "
        "trailing commentary. Do not wrap it in markdown fences.\n"
        "Schema:\n" + json.dumps(schema.model_json_schema(), indent=2)
    )


def _extract_json(text: str) -> str:
    """Pull the first balanced JSON object out of a string. Handles fenced output."""
    text = text.strip()
    if text.startswith("```"):
        # strip fence
        first_nl = text.find("\n")
        if first_nl >= 0:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    # find first { and matching closing }
    start = text.find("{")
    if start < 0:
        return text
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


class BaseAgent:
    def __init__(
        self,
        *,
        name: str,
        allowed_tools: list[str],
        prompt_template: str,
        output_schema: Type[BaseModel],
        max_tool_iterations: int = 8,
    ) -> None:
        self.name = name
        self.allowed_tools = list(allowed_tools)
        self.prompt_template = prompt_template
        self.output_schema = output_schema
        self.max_tool_iterations = max_tool_iterations

    def _bound_tools_payload(self) -> list[dict]:
        payload = []
        for real_name in self.allowed_tools:
            schema = TOOL_SCHEMAS[real_name]
            payload.append(
                {
                    "name": REAL_TO_ALIAS[real_name],
                    "description": schema["description"],
                    "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
                }
            )
        return payload

    def _render_prompt(self, **context_vars) -> str:
        return self.prompt_template.format(
            **context_vars,
            format_instructions=_format_instructions(self.output_schema),
        )

    async def _run_llm_loop(self, scan_id: str, prompt_text: str) -> str:
        llm = get_llm("primary")
        if self.allowed_tools:
            llm = llm.bind_tools(self._bound_tools_payload())

        messages: list[Any] = [HumanMessage(content=prompt_text)]
        for _iter in range(self.max_tool_iterations):
            await emit(scan_id, "agent.thinking", {"agent": self.name})
            resp: AIMessage = await llm.ainvoke(messages)
            messages.append(resp)
            tool_calls = getattr(resp, "tool_calls", None) or []
            if not tool_calls:
                # extract text content
                if isinstance(resp.content, str):
                    return resp.content
                # content can be list of blocks; join text parts
                parts = []
                for block in resp.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        parts.append(block)
                return "\n".join(parts)

            for tc in tool_calls:
                alias = tc["name"]
                real = ALIAS_TO_REAL.get(alias, alias.replace("_", ".", 1))
                args = tc.get("args", {}) or {}
                try:
                    result = await TOOLS[real](scan_id, **args)
                    content = json.dumps(result, default=str)
                except Exception as e:
                    content = json.dumps({"error": f"{type(e).__name__}: {e}"})
                messages.append(
                    ToolMessage(content=content, tool_call_id=tc["id"])
                )
        raise RuntimeError(
            f"{self.name} exceeded max_tool_iterations={self.max_tool_iterations}"
        )

    def _parse(self, text: str) -> BaseModel:
        payload = _extract_json(text)
        return self.output_schema.model_validate_json(payload)

    async def _repair(self, scan_id: str, prompt_text: str, previous: str, err: str) -> BaseModel:
        """Re-prompt once with the validation error and the previous response."""
        repair_prompt = (
            prompt_text
            + "\n\n[REPAIR]\n"
            + "Your previous response failed schema validation with this error:\n"
            + err
            + "\n\nPrevious response:\n"
            + previous
            + "\n\nReturn ONLY a valid JSON object matching the schema. Do not add any commentary."
        )
        final_text = await self._run_llm_loop(scan_id, repair_prompt)
        return self._parse(final_text)

    async def run_core(self, scan_id: str, **context_vars) -> BaseModel:
        """Shared entry point: emit lifecycle events, run the loop, parse, retry once."""
        await emit(scan_id, "agent.started", {"agent": self.name})
        prompt_text = self._render_prompt(**context_vars)
        final_text = ""
        try:
            final_text = await self._run_llm_loop(scan_id, prompt_text)
            report = self._parse(final_text)
        except (ValidationError, ValueError, json.JSONDecodeError) as e:
            report = await self._repair(scan_id, prompt_text, final_text, str(e))
        await emit(
            scan_id,
            "agent.completed",
            {"agent": self.name, "report_summary": report.__class__.__name__},
        )
        return report
