"""Tool registry bootstrap.

Importing this package imports every tool module, which registers each tool
in `backend.tools.base.TOOLS` via the `@tool` decorator.
"""

from backend.tools.base import TOOLS  # noqa: F401

# Read tools
from backend.tools import (  # noqa: F401
    abuseipdb,
    audit,
    email,
    endpoint,
    firewall,
    hibp,
    iam,
    mitre,
    mtd,
    nvd,
    otx,
    policy,
    ticketing,
)

__all__ = ["TOOLS"]
