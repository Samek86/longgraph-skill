"""Parse compiled run-directory edges. Golden SoT is the fixtures, not examples."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

ReadText = Callable[[Path], str]

_CODE_SPAN = re.compile(r"`([^`]*)`")
_FILE_IN_WRITE_SET = re.compile(r"([\w./-]+\.[A-Za-z0-9]+)")
_GAP_ROW = re.compile(r"^\|\s*(GAP-\d+)\s*\|")
_OB_ROW = re.compile(r"^\|\s*(OB-\d+)\s*\|")
_ITEM_ID = re.compile(r"(GAP-\d+|OB-\d+|D-\d+|M\d+)")
_CLOSED_WORDS = re.compile(r"\bresolved\b|\bclosed\b|\bclosure\b", re.I)
_ABSENT = frozenset({"none", "n/a", "-", "—", ""})


def strip_inline_code_spans(text: str) -> str:
    """Remove inline markdown code spans, keeping their inner text."""
    return _CODE_SPAN.sub(r"\1", text)


def _first_token(rest: str) -> str:
    token = rest.strip().split()[0] if rest.strip() else ""
    return token.strip("`").strip(".,;")


def _header_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.*)$", re.M)
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


class CurrentSlice:
    """Current-slice fields keyed by their human labels (spaces included)."""

    def __init__(self, fields: Mapping[str, str]):
        self._fields = dict(fields)

    def __getitem__(self, key: str) -> str:
        return self._fields[key]

    def get(self, key: str, default: str | None = None) -> str | None:
        return self._fields.get(key, default)

    @property
    def Item(self) -> str:
        return self._fields.get("Item", "")

    @property
    def Context(self) -> str:
        return self._fields.get("Context", "")

    @property
    def Verify(self) -> str:
        return self._fields.get("Verify", "")

    @property
    def fields(self) -> dict[str, str]:
        return dict(self._fields)


@dataclass
class OpsConfig:
    max_rounds: int = 100
    max_retries: int = 3
    smoke: str | None = None


@dataclass
class RunState:
    next_item: str
    open_gaps: list[str]
    last_directive_folded: str
    milestone_gate: str
    run_status: str
    current_slice: CurrentSlice
    blocked_on: str | None
    owner_blocked: list[str]
    findings_path: str | None
    ops: OpsConfig = field(default_factory=OpsConfig)
    status: dict = field(default_factory=dict)
    run_dir: Path | None = None


def findings_relpath(blocked_on: str | None) -> str | None:
    if not blocked_on or "#" not in blocked_on:
        return None
    ident = blocked_on.split("#", 1)[1].strip()
    if not ident or ident.lower() in _ABSENT:
        return None
    return f"findings/{ident}.md"


_FINDINGS_STATUS = re.compile(r"(?:\*\*Status\*\*|Status)\s*:\s*(\S+)", re.I)


def findings_status_complete(text: str) -> bool:
    """True when a findings body marks **Status**: complete."""
    match = _FINDINGS_STATUS.search(text or "")
    if not match:
        return False
    token = match.group(1).strip().strip("*").strip("`").lower().rstrip(".,;")
    return token == "complete"


def current_slice_owner_blocked(state: RunState) -> bool:
    """True when a live OB-xxx applies to the Current slice / next item."""
    live = list(state.owner_blocked or [])
    if not live:
        return False
    blob = " ".join(
        filter(
            None,
            [
                state.current_slice.Item,
                state.current_slice.get("Write set"),
                state.current_slice.Context,
                state.current_slice.Verify,
                state.current_slice.get("Done when"),
                state.next_item,
            ],
        )
    )
    if any(ob in blob for ob in live):
        return True
    return derive_item_id(state) in live


def derive_item_id(state: RunState) -> str:
    for text in (state.current_slice.Item, state.next_item):
        match = _ITEM_ID.search(text or "")
        if match:
            return match.group(1)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", (state.current_slice.Item or "item")).strip("-")
    return slug or "item"


def paths_from_write_set(write_set: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in _FILE_IN_WRITE_SET.finditer(write_set or ""):
        rel = match.group(1).lstrip("./")
        found[rel] = f"# mock write-set for {rel}\n"
    return found


def parse_ops(text: str) -> OpsConfig:
    ops = OpsConfig()
    match = re.search(r"^max_rounds:\s*(\d+)", text, re.M)
    if match:
        ops.max_rounds = int(match.group(1))
    match = re.search(r"^max_retries:\s*(\d+)", text, re.M)
    if match:
        ops.max_retries = int(match.group(1))
    match = re.search(r"^smoke:\s*(.+)$", text, re.M)
    if match:
        ops.smoke = match.group(1).strip()
    else:
        match = re.search(r"^[-*]\s*smoke:\s*(.+)$", text, re.M)
        if match:
            ops.smoke = match.group(1).strip()
    return ops


def _parse_current_slice(text: str) -> CurrentSlice:
    fields: dict[str, str] = {}
    in_slice = False
    keys = ("Item", "Write set", "Context", "Verify", "Done when")
    for line in text.splitlines():
        if line.startswith("## Current slice"):
            in_slice = True
            continue
        if in_slice and line.startswith("## "):
            break
        if not in_slice:
            continue
        for key in keys:
            prefix = f"{key}:"
            if line.startswith(prefix):
                fields[key] = line[len(prefix) :].strip()
    return CurrentSlice(fields)


def _section_lines(text: str, heading_prefix: str) -> list[str]:
    lines: list[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## ") and heading_prefix.lower() in line.lower():
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            lines.append(line)
    return lines


def _parse_open_gaps(text: str) -> list[str]:
    gaps: list[str] = []
    for line in _section_lines(text, "Debt & gap"):
        match = _GAP_ROW.match(line)
        if not match:
            continue
        if _CLOSED_WORDS.search(line):
            continue
        gaps.append(match.group(1))
    return gaps


def _parse_owner_blocked(text: str) -> list[str]:
    blocked: list[str] = []
    for line in _section_lines(text, "owner-blocked"):
        match = _OB_ROW.match(line)
        if match:
            blocked.append(match.group(1))
    return blocked


def _parse_blocked_on(text: str, slice_text: str) -> str | None:
    for blob in (slice_text, text):
        match = re.search(r"blocked-on:\s*`?(\S+?)`?(?:\s|$)", blob, re.I)
        if not match:
            continue
        value = match.group(1).rstrip(".,;")
        if value.lower() in _ABSENT:
            continue
        return value
    return None


def parse_ledger(text: str) -> dict:
    next_raw = _header_value(text, "Next unclosed work item") or ""
    folded = _first_token(_header_value(text, "Last directive folded") or "none")
    gate_rest = _header_value(text, "Milestone gate") or ""
    status_rest = _header_value(text, "Run status") or ""
    current = _parse_current_slice(text)
    # Re-extract the Current slice block for blocked-on priority.
    slice_blob = ""
    in_slice = False
    for line in text.splitlines():
        if line.startswith("## Current slice"):
            in_slice = True
        elif in_slice and line.startswith("## "):
            break
        if in_slice:
            slice_blob += line + "\n"
    blocked = _parse_blocked_on(text, slice_blob)
    return {
        "next_item": strip_inline_code_spans(next_raw),
        "last_directive_folded": folded or "none",
        "milestone_gate": _first_token(gate_rest).lower(),
        "run_status": _first_token(status_rest).lower(),
        "current_slice": current,
        "open_gaps": _parse_open_gaps(text),
        "owner_blocked": _parse_owner_blocked(text),
        "blocked_on": blocked,
        "findings_path": findings_relpath(blocked),
    }


def parse_run(run_dir: str | Path, *, read_text: ReadText | None = None) -> RunState:
    """Parse a normalized run directory. Does not walk the workspace."""
    root = Path(run_dir)
    reader = read_text or (lambda path: Path(path).read_text(encoding="utf-8"))
    ledger_text = reader(root / "ledger.md")
    parsed = parse_ledger(ledger_text)
    ops_path = root / "ops.md"
    ops = parse_ops(reader(ops_path)) if ops_path.exists() else OpsConfig()
    status_path = root / "status.json"
    status: dict = {}
    if status_path.exists():
        status = json.loads(reader(status_path))
    return RunState(
        next_item=parsed["next_item"],
        open_gaps=parsed["open_gaps"],
        last_directive_folded=parsed["last_directive_folded"],
        milestone_gate=parsed["milestone_gate"],
        run_status=parsed["run_status"],
        current_slice=parsed["current_slice"],
        blocked_on=parsed["blocked_on"],
        owner_blocked=parsed["owner_blocked"],
        findings_path=parsed["findings_path"],
        ops=ops,
        status=status,
        run_dir=root,
    )
