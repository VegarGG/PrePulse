import json
import os
from pathlib import Path

import pytest

PROFILES_DIR = Path(__file__).resolve().parents[1] / "backend" / "demo" / "profiles"


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    """Force mock mode + auto-approve + no seed for every test by default.

    Live API paths must never fire; the approval gate is exercised by a
    dedicated integration test that explicitly unsets PREPULSE_AUTO_APPROVE;
    the 30-day history seed is skipped so shape-only tests see a clean store.
    """
    monkeypatch.setenv("PREPULSE_LIVE", "0")
    monkeypatch.setenv("PREPULSE_AUTO_APPROVE", "1")
    monkeypatch.setenv("PREPULSE_SKIP_SEED", "1")


@pytest.fixture(scope="session")
def profiles() -> list[dict]:
    return [
        json.loads((PROFILES_DIR / f"{name}.json").read_text())
        for name in ("river_city", "greenfield", "shoplocal")
    ]


@pytest.fixture
def scan_id() -> str:
    return f"s-test-{os.getpid()}"
