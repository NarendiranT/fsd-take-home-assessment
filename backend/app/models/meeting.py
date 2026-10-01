from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SourceRecord:
    source: str
    ids: list[str]
    title: str
    start: datetime | None
    end: datetime | None
    time_known: bool
    emails: set[str] = field(default_factory=set)
    people: set[str] = field(default_factory=set)
    company_tokens: set[str] = field(default_factory=set)
    location: str | None = None
    status: str | None = None
    notes: str | None = None
    owner_key: str | None = None
    client_key: str | None = None
    who: str | None = None


@dataclass
class FieldValue:
    crm: str | None = None
    calendar: str | None = None
    conflict: bool = False


@dataclass
class MeetingRecord:
    id: str
    source: str
    sort_at: datetime | None
    title: FieldValue
    when: FieldValue
    who: FieldValue
    location: FieldValue
    status: FieldValue
    notes: FieldValue
    ids: FieldValue

    @property
    def conflict_count(self) -> int:
        fields = (self.title, self.when, self.location, self.status)
        return sum(1 for item in fields if item.conflict)
