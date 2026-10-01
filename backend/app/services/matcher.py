import re
from datetime import timedelta

from app.models.meeting import SourceRecord

HOUR = timedelta(hours=1)
PAIR_LIMIT = timedelta(hours=6)


def match(crm_rows: list[SourceRecord], calendar_rows: list[SourceRecord]) -> list[tuple[SourceRecord | None, SourceRecord | None]]:
    calendar_rows = _merge_calendar_duplicates(calendar_rows)
    candidates: list[tuple[int, float, int, int]] = []
    for crm_index, crm in enumerate(crm_rows):
        for calendar_index, calendar in enumerate(calendar_rows):
            score, gap = _score(crm, calendar)
            if score <= 0:
                continue
            candidates.append((score, gap, crm_index, calendar_index))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    used_crm: set[int] = set()
    used_calendar: set[int] = set()
    pairs: list[tuple[SourceRecord | None, SourceRecord | None]] = []
    for _ranked, _gap, crm_index, calendar_index in candidates:
        if crm_index in used_crm or calendar_index in used_calendar:
            continue
        used_crm.add(crm_index)
        used_calendar.add(calendar_index)
        pairs.append((crm_rows[crm_index], calendar_rows[calendar_index]))

    for index, crm in enumerate(crm_rows):
        if index not in used_crm:
            pairs.append((crm, None))
    for index, calendar in enumerate(calendar_rows):
        if index not in used_calendar:
            pairs.append((None, calendar))
    return pairs


def _merge_calendar_duplicates(rows: list[SourceRecord]) -> list[SourceRecord]:
    parent = list(range(len(rows)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            if _same_calendar_meeting(rows[left], rows[right]):
                parent[find(right)] = find(left)

    groups: dict[int, list[SourceRecord]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(find(index), []).append(row)
    return [_combine_calendar(group) for group in groups.values()]


def _same_calendar_meeting(left: SourceRecord, right: SourceRecord) -> bool:
    if left.start is None or right.start is None:
        return False
    if left.start.date() != right.start.date():
        return False
    if abs(left.start - right.start) > HOUR:
        return False
    return bool(left.emails & right.emails)


def _combine_calendar(rows: list[SourceRecord]) -> SourceRecord:
    if len(rows) == 1:
        return rows[0]
    ordered = sorted(rows, key=lambda row: row.start or row.ids[0])
    titles = [row.title for row in ordered if row.title]
    locations = [row.location for row in ordered if row.location]
    notes = [row.notes for row in ordered if row.notes]
    starts = [row.start for row in ordered if row.start]
    ends = [row.end for row in ordered if row.end]
    emails: set[str] = set()
    people: set[str] = set()
    who_parts: list[str] = []
    ids: list[str] = []
    for row in ordered:
        ids.extend(row.ids)
        emails |= row.emails
        people |= row.people
        if row.who:
            for part in row.who.split(", "):
                if part not in who_parts:
                    who_parts.append(part)
    return SourceRecord(
        source="calendar",
        ids=ids,
        title=max(titles, key=len) if titles else "",
        start=min(starts) if starts else None,
        end=max(ends) if ends else None,
        time_known=any(row.time_known for row in ordered),
        emails=emails,
        people=people,
        location=_longer(locations),
        status=ordered[0].status,
        notes=max(notes, key=len) if notes else None,
        owner_key=ordered[0].owner_key,
        who=", ".join(who_parts) or None,
    )


def _score(crm: SourceRecord, calendar: SourceRecord) -> tuple[int, float]:
    if crm.start is None or calendar.start is None:
        return 0, 0
    if crm.start.date() != calendar.start.date():
        return 0, 0
    gap = 0.0
    if crm.time_known and calendar.time_known:
        gap = abs((crm.start - calendar.start).total_seconds())
        if gap >= PAIR_LIMIT.total_seconds():
            return 0, gap

    score = 0
    if crm.client_key and crm.client_key in calendar.people:
        score += 10
    if crm.owner_key and crm.owner_key == calendar.owner_key:
        score += 5
    elif crm.owner_key and crm.owner_key in calendar.people:
        score += 3
    title_words = set(re.findall(r"[a-z0-9]+", calendar.title.lower()))
    if crm.company_tokens & title_words:
        score += 4
    return score, gap


def _longer(values: list[str]) -> str | None:
    if not values:
        return None
    return max(values, key=len)
