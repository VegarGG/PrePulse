import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import store
from backend.api.chat import router as chat_router
from backend.api.dashboard import router as dashboard_router
from backend.api.demo import router as demo_router
from backend.api.health import router as health_router
from backend.api.scans import router as scans_router

load_dotenv()


def _count_profiles() -> int:
    root = Path(__file__).resolve().parent / "demo" / "profiles"
    return len(list(root.glob("*.json")))


def _count_mitre_techniques() -> int:
    try:
        from backend.services.mitre_store import technique_count

        return technique_count()
    except Exception:
        return 0


def _count_kb_docs() -> tuple[int, int]:
    try:
        from backend.services.knowledge import corpus_chars, doc_count

        return doc_count(), corpus_chars()
    except Exception:
        return 0, 0


def _print_banner(seeded: int) -> None:
    mode = "live" if os.getenv("PREPULSE_LIVE") == "1" else "mock"
    profiles = _count_profiles()
    mitre = _count_mitre_techniques()
    kb_docs, kb_chars = _count_kb_docs()
    auto_approve = os.getenv("PREPULSE_AUTO_APPROVE") == "1"

    banner = f"""
╭──────────────────────────────────────────────────────────────╮
│  PrePulse v0.2.0  ·  ready                                    │
├──────────────────────────────────────────────────────────────┤
│  mode           : {mode:<10}                                   │
│  auto-approve   : {'on' if auto_approve else 'off':<10}                                   │
│  demo profiles  : {profiles:<3}                                           │
│  mitre attck    : {mitre:<5} techniques loaded                        │
│  knowledge base : {kb_docs:<3} docs · {kb_chars:<5} chars                       │
│  scan store     : {seeded:<4} historical scans seeded                  │
╰──────────────────────────────────────────────────────────────╯
"""
    print(banner, flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seeded = 0
    if os.getenv("PREPULSE_SKIP_SEED") != "1":
        from backend.demo.seed import seed_history

        seeded = seed_history()
    _print_banner(seeded)
    yield
    # no shutdown work — everything is in-memory


def create_app() -> FastAPI:
    app = FastAPI(title="PrePulse", version="0.2.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api")
    app.include_router(scans_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(demo_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app


# Re-export for `from backend import store` callers in the lifespan
_ = store

app = create_app()
