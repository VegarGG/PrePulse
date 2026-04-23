"""Scan-lifecycle REST + SSE routes."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend import orchestrator, store
from backend.events import get_history, subscribe, unsubscribe
from backend.models.schemas import CompanyProfile
from backend.safety import validate_profile
from backend.services.approvals import resolve_approval

router = APIRouter()

_PROFILES_DIR = Path(__file__).resolve().parents[1] / "demo" / "profiles"


def _load_profile(profile_id: str) -> CompanyProfile:
    path = _PROFILES_DIR / f"{profile_id}.json"
    if not path.exists():
        raise HTTPException(404, {"error": "profile_not_found", "profile_id": profile_id})
    data = json.loads(path.read_text())
    return CompanyProfile.model_validate(data["profile"])


class CreateScanBody(BaseModel):
    profile_id: Optional[str] = None
    custom_profile: Optional[CompanyProfile] = None


class CreateScanResponse(BaseModel):
    scan_id: str


class ApproveBody(BaseModel):
    action_id: str


class RejectBody(BaseModel):
    action_id: str
    reason: Optional[str] = None


@router.post("/scans", response_model=CreateScanResponse)
async def create_scan(body: CreateScanBody) -> CreateScanResponse:
    if body.profile_id:
        profile = _load_profile(body.profile_id)
    elif body.custom_profile:
        profile = body.custom_profile
    else:
        raise HTTPException(400, {"error": "missing_profile", "reason": "profile_id or custom_profile required"})

    validate_profile(profile)

    scan_id = f"s-{uuid.uuid4().hex[:8]}"
    orchestrator.run_scan(scan_id, profile)
    return CreateScanResponse(scan_id=scan_id)


@router.get("/scans")
async def list_scans() -> list[dict]:
    out = []
    for s in store.list_all():
        out.append(
            {
                "scan_id": s.scan_id,
                "started_at": s.started_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                "company_name": s.profile.company_name,
                "industry": s.profile.industry,
                "posture_score": s.final_report.posture_score if s.final_report else None,
                "posture_grade": s.final_report.posture_grade if s.final_report else None,
                "error": s.error,
            }
        )
    # newest first
    return sorted(out, key=lambda r: r["started_at"], reverse=True)


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str) -> dict:
    state = store.get(scan_id)
    if state is None:
        raise HTTPException(404, {"error": "not_found"})
    return json.loads(state.model_dump_json())


@router.get("/scans/{scan_id}/events")
async def stream_events(scan_id: str) -> StreamingResponse:
    q = await subscribe(scan_id)

    async def generator():
        try:
            while True:
                evt = await q.get()
                yield f"event: {evt['type']}\ndata: {json.dumps(evt, default=str)}\n\n"
                if evt["type"] in ("scan.completed", "scan.failed"):
                    break
        finally:
            unsubscribe(scan_id, q)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(generator(), media_type="text/event-stream", headers=headers)


@router.post("/scans/{scan_id}/approve")
async def approve_action(scan_id: str, body: ApproveBody) -> dict:
    ok = resolve_approval(scan_id, body.action_id, approved=True)
    if not ok:
        raise HTTPException(404, {"error": "no_pending_action", "action_id": body.action_id})
    return {"ok": True}


@router.post("/scans/{scan_id}/reject")
async def reject_action(scan_id: str, body: RejectBody) -> dict:
    ok = resolve_approval(scan_id, body.action_id, approved=False)
    if not ok:
        raise HTTPException(404, {"error": "no_pending_action", "action_id": body.action_id})
    return {"ok": True, "reason": body.reason}


@router.get("/scans/{scan_id}/trace")
async def get_trace(scan_id: str) -> StreamingResponse:
    events = get_history(scan_id)
    if not events and store.get(scan_id) is None:
        raise HTTPException(404, {"error": "not_found"})

    async def gen():
        for e in events:
            yield json.dumps(e, default=str) + "\n"

    headers = {
        "Content-Disposition": f'attachment; filename="{scan_id}-trace.ndjson"',
    }
    return StreamingResponse(gen(), media_type="application/x-ndjson", headers=headers)
