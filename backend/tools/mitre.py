import os

from backend.demo.mocks import mock_mitre_match_techniques
from backend.tools.base import tool


@tool(
    name="mitre.match_techniques",
    category="read",
    description="Return the top-k MITRE ATT&CK techniques semantically similar to the description.",
    input_schema={
        "type": "object",
        "properties": {
            "threat_description": {"type": "string"},
            "k": {"type": "integer", "default": 3},
        },
        "required": ["threat_description"],
    },
)
async def match_techniques(threat_description: str, k: int = 3) -> list[dict]:
    """Return the top-k MITRE ATT&CK techniques semantically similar to the description."""
    if os.getenv("PREPULSE_LIVE") != "1":
        return mock_mitre_match_techniques(threat_description=threat_description, k=k)

    from backend.services.mitre_store import get_retriever

    retriever = get_retriever()
    docs = retriever.invoke(threat_description)
    return [
        {
            "technique_id": d.metadata.get("technique_id", ""),
            "technique_name": d.metadata.get("name", ""),
            "tactic": d.metadata.get("tactic", ""),
            "description": d.page_content[:240],
            "similarity_score": float(d.metadata.get("score", 0.8)),
        }
        for d in docs[:k]
    ]
