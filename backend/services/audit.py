"""In-memory audit log for simulated action tool calls."""

from typing import Any

_actions: list[dict[str, Any]] = []
_decisions: list[dict[str, Any]] = []


def record_action(entry: dict[str, Any]) -> None:
    _actions.append(entry)


def get_actions() -> list[dict[str, Any]]:
    return list(_actions)


def record_decision(entry: dict[str, Any]) -> None:
    _decisions.append(entry)


def get_decisions() -> list[dict[str, Any]]:
    return list(_decisions)


def clear() -> None:
    _actions.clear()
    _decisions.clear()
