import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_PROFILES_DIR = Path(__file__).resolve().parents[1] / "demo" / "profiles"


@router.get("/demo/profiles")
async def list_profiles() -> list[dict]:
    out = []
    for path in sorted(_PROFILES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        p = data.get("profile", {})
        out.append(
            {
                "profile_id": data.get("profile_id", path.stem),
                "company_name": p.get("company_name"),
                "industry": p.get("industry"),
                "domain": p.get("domain"),
                "employee_count": p.get("employee_count"),
                "expected_posture_score": data.get("expected_posture_score"),
                "narrative": data.get("narrative", ""),
            }
        )
    return out
