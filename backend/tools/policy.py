from typing import Any

from backend.tools.base import tool

_MAX_ACTIONS_PER_SCAN = 8
_DISALLOWED_KINDS = {"iam.disable_user"}


@tool(name="policy.check", category="meta")
async def check(action_list: list[dict[str, Any]]) -> dict:
    """Run deterministic policy checks over a proposed remediation action list.

    Returns a dict with a `violations` list of plain-English strings. Supervisor
    surfaces these in its sign-off.
    """
    violations: list[str] = []

    if len(action_list) > _MAX_ACTIONS_PER_SCAN:
        violations.append(
            f"Too many remediation actions proposed ({len(action_list)} > {_MAX_ACTIONS_PER_SCAN})"
        )

    for a in action_list:
        kind = a.get("kind") or a.get("action")
        if kind in _DISALLOWED_KINDS and not a.get("approved"):
            violations.append(
                f"Destructive action '{kind}' requires explicit approval and was not approved"
            )
        severity = (a.get("severity") or "").lower()
        if severity in ("critical", "high") and not a.get("requires_approval", True):
            violations.append(
                f"Action '{kind}' at {severity} severity must be gated by approval"
            )

    return {"violations": violations, "ok": not violations}
