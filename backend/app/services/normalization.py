import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.meeting import SourceRecord

NEW_YORK = ZoneInfo("America/New_York")

# Words that show up in many company names and would pair the wrong meetings.
COMPANY_STOP = {
    "advisors",
    "and",
    "capital",
    "fund",
    "group",
    "holdings",
    "institutional",
    "investments",
    "investors",
    "partners",
    "the",
    "ventures",
    "wealth",
}

SKIP_CLIENTS = {"multiple"}


def normalize_crm(rows: list[dict]) -> list[SourceRecord]:
    return [_crm_record(row) for row in rows]


def normalize_calendar(rows: list[dict]) -> list[SourceRecord]:
    return [_calendar_record(row) for row in rows]


def _crm_record(row: dict) -> SourceRecord:
    client = _clean(row.get("client_name"))
    company = _clean(row.get("client_company"))
    owner = _clean(row.get("relationship_owner"))
    start, time_known = _crm_start(row.get("meeting_date"), row.get("meeting_time"))
    client_key = _person_key(client) if client and client.lower() not in SKIP_CLIENTS else None
    who = None
    if client and client.lower() not in SKIP_CLIENTS:
        who = f"{client}, {company}" if company else client
    elif company and company.lower() not in SKIP_CLIENTS:
        who = company
    return SourceRecord(
        source="crm",
        ids=[row["crm_id"]],
        title=_clean(row.get("subject")) or "",
        start=start,
        end=None,
        time_known=time_known,
        company_tokens=_company_tokens(company),
        location=_clean(row.get("location")),
        status=_clean(row.get("status")),
        notes=_clean(row.get("notes")),
        owner_key=_person_key(owner) if owner else None,
        client_key=client_key,
        who=who,
    )


def _calendar_record(row: dict) -> SourceRecord:
    attendees = [_fix_email(item) for item in row.get("attendees") or []]
    organizer = _fix_email(row.get("organizer"))
    emails = {item for item in attendees + [organizer] if item and "@" in item}
    people = {_person_key(item.split("@", 1)[0]) for item in emails}
    names = [_email_name(item) for item in attendees]
    if organizer and organizer not in attendees:
        names.insert(0, _email_name(organizer))
    start = _parse_clock(row.get("start_time"))
    return SourceRecord(
        source="calendar",
        ids=[row["event_id"]],
        title=_clean(row.get("title")) or "",
        start=start,
        end=_parse_clock(row.get("end_time")),
        time_known=start is not None,
        emails=emails,
        people={key for key in people if key},
        location=_clean(row.get("location")),
        status=_clean(row.get("status")),
        notes=_clean(row.get("description")),
        owner_key=_person_key(organizer.split("@", 1)[0]) if organizer and "@" in organizer else None,
        who=", ".join(name for name in names if name) or None,
    )


def _crm_start(date_text, time_text) -> tuple[datetime | None, bool]:
    day = _parse_date(date_text)
    if day is None:
        return None, False
    clock = _clean(time_text)
    if not clock:
        return datetime(day.year, day.month, day.day, tzinfo=NEW_YORK), False
    hour, minute = clock.split(":", 1)
    return (
        datetime(day.year, day.month, day.day, int(hour), int(minute), tzinfo=NEW_YORK),
        True,
    )


def _parse_date(value) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    swapped = re.fullmatch(r"(\d{2})-(\d{2})/(\d{4})", text)
    if swapped:
        month, day, year = swapped.groups()
        return datetime(int(year), int(month), int(day))
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed


def _parse_clock(value) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    # "2025-03-14T20:00" has no seconds.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text):
        text = f"{text}:00"
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=NEW_YORK)
    return parsed.astimezone(NEW_YORK)


def _fix_email(value) -> str | None:
    text = _clean(value)
    if not text:
        return None
    return text.replace("[at]", "@")


def _person_key(value: str | None) -> str | None:
    if not value:
        return None
    letters = re.findall(r"[a-z]+", value.lower().replace("'", ""))
    key = " ".join(letters)
    return key or None


def _company_tokens(company: str | None) -> set[str]:
    if not company:
        return set()
    words = re.findall(r"[a-z0-9]+", company.lower())
    return {word for word in words if len(word) >= 4 and word not in COMPANY_STOP}


def _email_name(value: str) -> str:
    if "@" not in value:
        return value
    local = value.split("@", 1)[0].replace("'", "")
    parts = re.findall(r"[A-Za-z]+", local)
    return " ".join(part.capitalize() for part in parts)


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
