"""Bounded rotation for the ledger Rounds log and the directives queue.

Pure helpers: parse caps from ops.md (or defaults), split live text from
archive fragments. Callers write through EdgeWriter.

CONTRACT: KEEP_ROUNDS (default 5) live `- R…` lines; older lines go to
`archive/rounds.md`. Corrections with IDs ≤ the ledger watermark
(`Last directive folded`) move to `archive/directives.md` before append.
Next ID = max(watermark, highest live ID) + 1; never reuse rotated IDs.
After watermark rotate, oldest excess live packets rotate until the
queue is ≤ OPEN_DIRECTIVE_CAP (default 8).
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
_DIR_LINE = re.compile(r"^D-(\d+)\b")
_DIR_ANY = re.compile(r"\bD-(\d+)\b")
_WATERMARK_NONE = frozenset({"none", "n/a", "-", "—", ""})
_NONE_CORRECTION = re.compile(r"^\(none", re.I)


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


def rotate_rounds_log(
    ledger_text: str,
    *,
    keep_rounds: int | None = None,
) -> tuple[str, str]:
    """Keep the last KEEP_ROUNDS `- R…` lines; return (new_ledger, archive_append)."""
    keep = DEFAULT_KEEP_ROUNDS if keep_rounds is None else keep_rounds
    bounds = _heading_bounds(ledger_text, "rounds log")
    if bounds is None:
        return ledger_text, ""
    _, body_start, body_end = bounds
    lines = ledger_text.splitlines(keepends=True)
    body = lines[body_start:body_end]
    round_idxs = [i for i, line in enumerate(body) if _ROUND_LINE.match(_raw_line(line))]
    if len(round_idxs) <= keep:
        return ledger_text, ""
    drop = set(round_idxs[: len(round_idxs) - keep])
    archived = "".join(body[i] for i in sorted(drop))
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
) -> str:
    """Append one `- Rn …` line under the Rounds log section (create if missing)."""
    match = re.search(r"Round:\s*(\d+)", ledger_text)
    n = int(match.group(1)) if match else 1
    day = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"- R{n} {day} | {item_id} | verify: green | next: {item_id}\n"
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
    """Move Correction packets with IDs ≤ watermark (then oldest excess) to archive.

    Supervisor state and STANDING are preserved byte-for-byte. After the
    watermark pass, if live Corrections still exceed OPEN_DIRECTIVE_CAP,
    the oldest remaining packets (lowest IDs) rotate until the live queue
    is at the cap — newest unfolded corrections stay.
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

    if cap >= 0 and len(live) > cap:
        overflow = len(live) - cap
        archived.extend(packet for _, packet in live[:overflow])
        live = live[overflow:]

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


def append_correction_packet(directives_text: str, packet: str) -> str:
    """Insert a correction packet at the end of the Corrections section."""
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
