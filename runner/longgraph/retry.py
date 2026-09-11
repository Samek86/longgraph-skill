"""Idempotency key (runId, round, item_id) and resume-from-verify."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryKey:
    run_id: str
    round: int
    item_id: str

    def as_dict(self) -> dict[str, object]:
        return {"runId": self.run_id, "round": self.round, "item_id": self.item_id}


def increment_retry(status: dict, item_id: str) -> int:
    meta = status.setdefault("metadata", {})
    retries = meta.setdefault("itemRetries", {})
    retries[item_id] = int(retries.get(item_id, 0)) + 1
    return retries[item_id]


def should_resume_verify_only(status: dict, key: RetryKey) -> bool:
    last = (status.get("metadata") or {}).get("lastAttempt") or {}
    if last.get("phase") != "verify_green":
        return False
    recorded = last.get("key") or {}
    return (
        recorded.get("runId") == key.run_id
        and int(recorded.get("round", -1)) == key.round
        and recorded.get("item_id") == key.item_id
    )


def set_last_attempt(status: dict, key: RetryKey, phase: str) -> None:
    meta = status.setdefault("metadata", {})
    meta["lastAttempt"] = {"key": key.as_dict(), "phase": phase}
