import re
from datetime import datetime
from pathlib import Path

from app.models.meeting import FieldValue, MeetingRecord, SourceRecord
from app.services.ingestion import load_sources
from app.services.matcher import match
from app.services.normalization import normalize_calendar, normalize_crm

ACTIVE_STATUS = {"completed", "confirmed", "scheduled"}


def reconcile(data_dir: Path) -> list[MeetingRecord]:
    crm_rows, calendar_rows = load_sources(data_dir)
    pairs = match(normalize_crm(crm_rows), normalize_calendar(calendar_rows))
    meetings = [_meeting(crm, calendar) for crm, calendar in pairs]
    meetings.sort(key=lambda item: (item.sort_at is None, item.sort_at.timestamp() if item.sort_at else 0))
    return meetings


def _meeting(crm: SourceRecord | None, calendar: SourceRecord | None) -> MeetingRecord:
    crm_ids = crm.ids if crm else []
    calendar_ids = calendar.ids if calendar else []
    if crm and calendar:
        source = "both"
    elif crm:
        source = "crm"
    else:
        source = "calendar"
    sort_at = _sort_at(crm, calendar)
    return MeetingRecord(
        id="+".join(crm_ids + calendar_ids),
        source=source,
        sort_at=sort_at,
        title=FieldValue(crm=_title(crm), calendar=_title(calendar)),
        when=_when_field(crm, calendar),
        who=FieldValue(crm=_who(crm), calendar=_who(calendar)),
        location=_text_field(_location(crm), _location(calendar), contain=True),
        status=_status_field(crm, calendar),
        notes=FieldValue(crm=_notes(crm), calendar=_notes(calendar)),
        ids=FieldValue(
            crm=", ".join(crm_ids) or None,
            calendar=", ".join(calendar_ids) or None,
        ),
    )


def _text_field(crm: str | None, calendar: str | None, contain: bool) -> FieldValue:
    if not crm or not calendar:
        return FieldValue(crm=crm, calendar=calendar)
    if _norm(crm) == _norm(calendar):
        return FieldValue(crm=crm, calendar=calendar)
    if contain and _contains(crm, calendar):
        return FieldValue(crm=crm, calendar=calendar)
    return FieldValue(crm=crm, calendar=calendar, conflict=True)


def _when_field(crm: SourceRecord | None, calendar: SourceRecord | None) -> FieldValue:
    crm_text = _format_when(crm)
    calendar_text = _format_when(calendar)
    conflict = False
    if (
        crm
        and calendar
        and crm.time_known
        and calendar.time_known
        and crm.start
        and calendar.start
        and abs((crm.start - calendar.start).total_seconds()) > 15 * 60
    ):
        conflict = True
    return FieldValue(crm=crm_text, calendar=calendar_text, conflict=conflict)


def _status_field(crm: SourceRecord | None, calendar: SourceRecord | None) -> FieldValue:
    crm_status = crm.status if crm else None
    calendar_status = calendar.status if calendar else None
    conflict = False
    if crm_status and calendar_status and _norm(crm_status) != _norm(calendar_status):
        left = crm_status.lower()
        right = calendar_status.lower()
        conflict = not (left in ACTIVE_STATUS and right in ACTIVE_STATUS)
    return FieldValue(crm=crm_status, calendar=calendar_status, conflict=conflict)


def _format_when(record: SourceRecord | None) -> str | None:
    if record is None or record.start is None:
        return None
    stamp = f"{record.start.day} {record.start.strftime('%b %Y')}"
    if record.time_known:
        return f"{stamp}, {record.start.strftime('%H:%M')}"
    return stamp


def _sort_at(crm: SourceRecord | None, calendar: SourceRecord | None) -> datetime | None:
    if calendar and calendar.time_known:
        return calendar.start
    if crm and crm.time_known:
        return crm.start
    if calendar and calendar.start:
        return calendar.start
    if crm and crm.start:
        return crm.start
    return None


def _title(record: SourceRecord | None) -> str | None:
    if record is None or not record.title:
        return None
    return record.title


def _who(record: SourceRecord | None) -> str | None:
    if record is None:
        return None
    return record.who


def _location(record: SourceRecord | None) -> str | None:
    if record is None:
        return None
    return record.location


def _notes(record: SourceRecord | None) -> str | None:
    if record is None:
        return None
    return record.notes


def _contains(left: str, right: str) -> bool:
    a = _norm(left)
    b = _norm(right)
    if not a or not b or a == b:
        return False
    return a in b or b in a


def _norm(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))
