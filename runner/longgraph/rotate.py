"""Bounded rotation for the ledger Rounds log and the directives queue.

Pure helpers: parse caps from ops.md (or defaults), split live text from
archive fragments. Callers write through EdgeWriter.

CONTRACT: KEEP_ROUNDS (default 5) live round entries — `- R…` lines and
`### Round N` sections — older entries go to `archive/rounds.md`.
Corrections with IDs ≤ the ledger watermark (`Last directive folded`)
move to `archive/directives.md` before append. Next ID = max(watermark,
highest live ID) + 1; never reuse rotated IDs. Packets above the
watermark are never cap-rotated (OPEN_DIRECTIVE_CAP is append
discipline, not a silent truncate of unfolded corrections).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

DEFAULT_KEEP_ROUNDS = 5
DEFAULT_OPEN_DIRECTIVE_CAP = 8

ROUNDS_ARCHIVE_HEADING = "# Archived rounds\n"
DIRECTIVES_ARCHIVE_HEADING = "# Archived directives\n"

_KEEP_ROUNDS = re.compile(r"^(?:KEEP_ROUNDS|keep_rounds):\s*(\d+)\s*$", re.M)
_OPEN_CAP = re.compile(r"^(?:OPEN_DIRECTIVE_CAP|open_directive_cap):\s*(\d+)\s*$", re.M)
_ROUND_LINE = re.compile(r"^- R\d+\b")
_ROUND_SECTION = re.compile(r"^### Round\s+\d+\b")
_DIR_LINE = re.compile(r"^D-(\d+)\b")
_DIR_ANY = re.compile(r"\bD-(\d+)\b")
_WATERMARK_NONE = frozenset({"none", "n/a", "-", "—", ""})
_NONE_CORRECTION = re.compile(r"^\(none", re.I)
_ACCEPT_GATE_TOKEN = re.compile(r"\bACCEPT-GATE\b", re.I)


@dataclass(frozen=True)
class RotationCaps:
    keep_rounds: int = DEFAULT_KEEP_ROUNDS
    open_directive_cap: int = DEFAULT_OPEN_DIRECTIVE_CAP


def parse_rotation_caps(ops_text: str | None) -> RotationCaps:
    """Read KEEP_ROUNDS / OPEN_DIRECTIVE_CAP from ops.md; else defaults 5 / 8."""
    keep = DEFAULT_KEEP_ROUNDS
    cap = DEFAULT_OPEN_DIRECTIVE_CAP
    if ops_text:
        match = _KEEP_ROUNDS.search(ops_text)
        if match:
            keep = int(match.group(1))
        match = _OPEN_CAP.search(ops_text)
        if match:
            cap = int(match.group(1))
    return RotationCaps(keep_rounds=keep, open_directive_cap=cap)


def watermark_n(watermark: str | None) -> int:
    """Numeric id from `D-003` / `3`; `none` and empty → 0."""
    token = (watermark or "").strip().strip("`").split()[0] if watermark else ""
    if token.lower() in _WATERMARK_NONE:
        return 0
    match = re.search(r"(\d+)", token)
    return int(match.group(1)) if match else 0


def format_directive_id(n: int) -> str:
    return f"D-{n:03d}"


def next_directive_id(watermark: str, *blobs: str) -> str:
    """Next ID = max(watermark, highest D-n in blobs) + 1."""
    highest = watermark_n(watermark)
    for blob in blobs:
        if not blob:
            continue
        for match in _DIR_ANY.finditer(blob):
            highest = max(highest, int(match.group(1)))
    return format_directive_id(highest + 1)


def merge_archive(existing: str, fragment: str, *, heading: str) -> str:
    """Append `fragment` to an archive file, creating it with `heading` if empty."""
    if not fragment or not fragment.strip():
        return existing
    chunk = fragment.rstrip() + "\n"
    if not (existing or "").strip():
        head = heading if heading.endswith("\n") else heading + "\n"
        return head + "\n" + chunk
    return existing.rstrip() + "\n" + chunk


def _heading_bounds(text: str, needle: str) -> tuple[int, int, int] | None:
    """Return (heading_line_index, body_start, body_end) in splitlines list."""
    lines = text.splitlines(keepends=True)
    start: int | None = None
    end = len(lines)
    for i, line in enumerate(lines):
        raw = line.split("\n")[0]
        if start is None and raw.startswith("## ") and needle in raw.lower():
            start = i
            continue
        if start is not None and raw.startswith("## "):
            end = i
            break
    if start is None:
        return None
    return start, start + 1, end


def _raw_line(line: str) -> str:
    return line.split("\n")[0]


def _round_entry_ranges(body: list[str]) -> list[tuple[int, int]]:
    """Return (start, end) ranges for each `- R…` line or `### Round N` section."""
    ranges: list[tuple[int, int]] = []
    i = 0
    while i < len(body):
        raw = _raw_line(body[i])
        if _ROUND_LINE.match(raw):
            ranges.append((i, i + 1))
            i += 1
            continue
        if _ROUND_SECTION.match(raw):
            j = i + 1
            while j < len(body):
                nxt = _raw_line(body[j])
                if _ROUND_LINE.match(nxt) or _ROUND_SECTION.match(nxt):
                    break
                j += 1
            ranges.append((i, j))
            i = j
            continue
        i += 1
    return ranges


def rotate_rounds_log(
    ledger_text: str,
    *,
    keep_rounds: int | None = None,
) -> tuple[str, str]:
    """Keep the last KEEP_ROUNDS live round entries; return (new_ledger, archive_append).

    A live entry is one `- R…` line or one `### Round N` section (heading plus
    body until the next entry). Mixed logs stay bounded.
    """
    keep = DEFAULT_KEEP_ROUNDS if keep_rounds is None else keep_rounds
    bounds = _heading_bounds(ledger_text, "rounds log")
    if bounds is None:
        return ledger_text, ""
    _, body_start, body_end = bounds
    lines = ledger_text.splitlines(keepends=True)
    body = lines[body_start:body_end]
    entries = _round_entry_ranges(body)
    if len(entries) <= keep:
        return ledger_text, ""
    drop_ranges = entries[: len(entries) - keep]
    drop = set()
    archived_parts: list[str] = []
    for start, end in drop_ranges:
        archived_parts.append("".join(body[start:end]))
        drop.update(range(start, end))
    archived = "".join(archived_parts)
    new_body = [line for i, line in enumerate(body) if i not in drop]
    new_lines = lines[:body_start] + new_body + lines[body_end:]
    new_text = "".join(new_lines)
    if ledger_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, archived


def append_round_log_line(
    ledger_text: str,
    item_id: str,
    *,
    date: str | None = None,
    next_item: str | None = None,
) -> str:
    """Append one `- Rn …` line under the Rounds log section (create if missing)."""
    match = re.search(r"Round:\s*(\d+)", ledger_text)
    n = int(match.group(1)) if match else 1
    day = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    nxt = item_id if next_item is None else next_item
    line = f"- R{n} {day} | {item_id} | verify: green | next: {nxt}\n"
    bounds = _heading_bounds(ledger_text, "rounds log")
    if bounds is None:
        base = ledger_text if ledger_text.endswith("\n") else ledger_text + "\n"
        return base + "\n## Rounds log\n\n" + line
    _, _, body_end = bounds
    lines = ledger_text.splitlines(keepends=True)
    new_lines = lines[:body_end] + [line] + lines[body_end:]
    new_text = "".join(new_lines)
    if ledger_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text


def _parse_correction_packets(body: str) -> tuple[str, list[tuple[int, str]]]:
    lines = body.splitlines(keepends=True)
    preamble: list[str] = []
    packets: list[tuple[int, str]] = []
    current_id: int | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_lines
        if current_id is not None:
            packets.append((current_id, "".join(current_lines)))
        current_id = None
        current_lines = []

    for line in lines:
        match = _DIR_LINE.match(_raw_line(line))
        if match:
            flush()
            current_id = int(match.group(1))
            current_lines = [line]
        elif current_id is None:
            preamble.append(line)
        else:
            current_lines.append(line)
    flush()
    return "".join(preamble), packets


def _folded_marker(n: int) -> str:
    return (
        f"(none — folded through {format_directive_id(n)}; "
        "history is in `archive/directives.md`)\n"
    )


def _strip_none_lines(preamble: str) -> str:
    kept = [
        line
        for line in preamble.splitlines(keepends=True)
        if not _NONE_CORRECTION.match(_raw_line(line).strip())
    ]
    return "".join(kept)


def rotate_directives(
    directives_text: str,
    watermark: str,
    *,
    open_directive_cap: int | None = None,
) -> tuple[str, str]:
    """Move Correction packets with IDs ≤ watermark to archive.

    Supervisor state and STANDING are preserved byte-for-byte. Packets
    above the watermark stay live even when they exceed OPEN_DIRECTIVE_CAP.
    """
    cap = DEFAULT_OPEN_DIRECTIVE_CAP if open_directive_cap is None else open_directive_cap
    bounds = _heading_bounds(directives_text, "corrections")
    if bounds is None:
        return directives_text, ""
    _, body_start, body_end = bounds
    lines = directives_text.splitlines(keepends=True)
    body = "".join(lines[body_start:body_end])
    preamble, packets = _parse_correction_packets(body)
    if not packets:
        return directives_text, ""

    wm = watermark_n(watermark)
    archived: list[str] = []
    live: list[tuple[int, str]] = []
    for ident, packet in packets:
        if wm and ident <= wm:
            archived.append(packet)
        else:
            live.append((ident, packet))

    # OPEN_DIRECTIVE_CAP must not archive packets the watermark has not
    # passed — that silently drops unfolded corrections. The cap is
    # supervisor append discipline only (`_ = cap` keeps the kwarg live).
    _ = cap

    if not archived:
        return directives_text, ""

    highest_rotated = 0
    for packet in archived:
        match = _DIR_LINE.match(_raw_line(packet))
        if match:
            highest_rotated = max(highest_rotated, int(match.group(1)))
    folded_through = max(wm, highest_rotated)

    new_preamble = _strip_none_lines(preamble)
    if live:
        new_body = new_preamble + "".join(packet for _, packet in live)
    else:
        new_body = new_preamble + _folded_marker(folded_through)
    if new_body and not new_body.endswith("\n"):
        new_body += "\n"
    chunk_lines = new_body.splitlines(keepends=True)
    new_text = "".join(lines[:body_start] + chunk_lines + lines[body_end:])
    if directives_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text, "".join(archived)


def live_correction_packets(directives_text: str) -> list[tuple[int, str]]:
    """Return (id, packet) for every live Corrections packet, in order."""
    bounds = _heading_bounds(directives_text, "corrections")
    if bounds is None:
        return []
    _, body_start, body_end = bounds
    lines = directives_text.splitlines(keepends=True)
    body = "".join(lines[body_start:body_end])
    _, packets = _parse_correction_packets(body)
    return packets


def unfolded_packets(directives_text: str, watermark: str) -> list[tuple[int, str]]:
    """Live Corrections with IDs strictly above the ledger watermark."""
    wm = watermark_n(watermark)
    return [(ident, packet) for ident, packet in live_correction_packets(directives_text) if ident > wm]


def packet_verb(packet: str) -> str:
    """Third `·`-separated token on the first line (`accept`, `plan`, …)."""
    first = packet.splitlines()[0] if packet else ""
    parts = [part.strip() for part in first.split("·")]
    if len(parts) < 3:
        return ""
    token = parts[2].split()[0] if parts[2] else ""
    return token.strip("*").strip("`").strip(".,;").lower()


def is_accept_gate_packet(packet: str) -> bool:
    """True when a packet accepts the pending milestone gate.

    Marker (CONTRACT §1.4): the exact token ``ACCEPT-GATE`` (ASCII,
    case-insensitive) appears in the packet, **or** the first-line verb
    is ``accept-gate``. A bare ``accept`` verb without ``ACCEPT-GATE`` is
    a lane/item verdict and does not flip the gate.
    """
    if not packet:
        return False
    if packet_verb(packet) == "accept-gate":
        return True
    return bool(_ACCEPT_GATE_TOKEN.search(packet))


def _set_header_rest(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(label)}:\s*).*$", re.M)
    if not pattern.search(text):
        return text
    return pattern.sub(lambda match: match.group(1) + value, text, count=1)


def fold_corrections_into_ledger(
    ledger_text: str,
    directives_text: str,
    watermark: str,
) -> tuple[str, str, bool]:
    """Apply or no-op every correction above `watermark`.

    Returns ``(new_ledger, new_watermark, accepted_gate)``.
    ``ACCEPT-GATE`` flips ``Milestone gate`` to ``passed``. Every other
    packet is an explicit no-op. The watermark advances to the highest
    folded id in either case.
    """
    packets = unfolded_packets(directives_text, watermark)
    if not packets:
        return ledger_text, watermark or "none", False
    highest = watermark_n(watermark)
    accepted = False
    for ident, packet in packets:
        highest = max(highest, ident)
        if is_accept_gate_packet(packet):
            accepted = True
    new_wm = format_directive_id(highest)
    updated = _set_header_rest(ledger_text, "Last directive folded", new_wm)
    if accepted:
        updated = _set_header_rest(updated, "Milestone gate", "`passed` (ACCEPT-GATE folded)")
    return updated, new_wm, accepted


def append_correction_packet(
    directives_text: str,
    packet: str,
    *,
    watermark: str = "none",
    open_directive_cap: int | None = DEFAULT_OPEN_DIRECTIVE_CAP,
) -> str:
    """Insert a correction packet, or refuse when the unfolded queue is at cap.

    CONTRACT §2: ``OPEN_DIRECTIVE_CAP`` is append discipline. Rotation
    must not archive unfolded packets; this helper must not grow the
    unfolded queue past the cap. Callers rotate-before-append so folded
    IDs leave the live queue first. ``open_directive_cap=None`` disables
    the gate (fixture construction only).
    """
    if open_directive_cap is not None and (
        len(unfolded_packets(directives_text, watermark)) >= open_directive_cap
    ):
        return directives_text
    body = packet if packet.endswith("\n") else packet + "\n"
    bounds = _heading_bounds(directives_text, "corrections")
    if bounds is None:
        base = directives_text if directives_text.endswith("\n") else directives_text + "\n"
        return base + "\n## Corrections\n\n" + body
    _, body_start, body_end = bounds
    lines = directives_text.splitlines(keepends=True)
    section = "".join(lines[body_start:body_end])
    cleaned = _strip_none_lines(section)
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    if cleaned and not cleaned.endswith("\n\n"):
        cleaned = cleaned.rstrip("\n") + "\n\n"
    new_section = cleaned + body
    section_lines = new_section.splitlines(keepends=True)
    new_text = "".join(lines[:body_start] + section_lines + lines[body_end:])
    if directives_text.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"
    return new_text
