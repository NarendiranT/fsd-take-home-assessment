from pydantic import BaseModel


class FieldValue(BaseModel):
    crm: str | None = None
    calendar: str | None = None
    conflict: bool = False


class Meeting(BaseModel):
    id: str
    source: str
    conflict_count: int
    title: FieldValue
    when: FieldValue
    who: FieldValue
    location: FieldValue
    status: FieldValue
    notes: FieldValue
    ids: FieldValue


class MeetingList(BaseModel):
    meetings: list[Meeting]
