import asyncio
import time
import uuid

from backend.services.audit import record_action
from backend.tools.base import tool


@tool(
    name="iam.force_mfa",
    category="action",
    description="Simulate enforcing MFA on the given IAM scope.",
    input_schema={
        "type": "object",
        "properties": {"scope": {"type": "string"}},
        "required": ["scope"],
    },
)
async def force_mfa(scope: str) -> dict:
    """Simulate enforcing MFA on the given IAM scope."""
    await asyncio.sleep(0.15)
    token = f"iam-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "iam.force_mfa",
            "scope": scope,
            "token": token,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "scope": scope,
        "mfa_enforced": True,
        "enforcement_id": token,
        "simulated": True,
        "message": f"Would require MFA on next login for: {scope}",
    }


@tool(
    name="iam.rotate_credentials",
    category="action",
    description="Simulate rotating IAM credentials for the given scope.",
    input_schema={
        "type": "object",
        "properties": {"scope": {"type": "string"}},
        "required": ["scope"],
    },
)
async def rotate_credentials(scope: str) -> dict:
    """Simulate rotating credentials for the given IAM scope."""
    await asyncio.sleep(0.15)
    token = f"iam-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "iam.rotate_credentials",
            "scope": scope,
            "token": token,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "scope": scope,
        "rotated": True,
        "rotation_id": token,
        "simulated": True,
        "message": f"Would rotate credentials for: {scope}",
    }


@tool(
    name="iam.disable_user",
    category="action",
    description="Simulate disabling a specific user account.",
    input_schema={
        "type": "object",
        "properties": {"user": {"type": "string"}},
        "required": ["user"],
    },
)
async def disable_user(user: str) -> dict:
    """Simulate disabling a user account."""
    await asyncio.sleep(0.15)
    token = f"iam-{uuid.uuid4().hex[:8]}"
    record_action(
        {
            "action": "iam.disable_user",
            "user": user,
            "token": token,
            "ts": time.time(),
            "simulated": True,
        }
    )
    return {
        "user": user,
        "disabled": True,
        "simulated": True,
        "message": f"Would disable account: {user}",
    }
