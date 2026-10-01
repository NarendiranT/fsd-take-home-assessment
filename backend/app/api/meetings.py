import asyncio
import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.meeting import FieldValue as FieldRecord
from app.models.meeting import MeetingRecord
from app.schemas.meeting import FieldValue, Meeting, MeetingList
from app.services.ingestion import source_token
from app.services.reconciliation import reconcile

router = APIRouter()


def data_dir() -> Path:
    configured = os.environ.get("DATA_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "data"


@router.get("/api/meetings", response_model=MeetingList)
def list_meetings() -> MeetingList:
    meetings = [_meeting(record) for record in reconcile(data_dir())]
    return MeetingList(meetings=meetings)


@router.get("/api/events")
async def file_events() -> StreamingResponse:
    return StreamingResponse(
        _file_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _file_events():
    folder = data_dir()
    seen = source_token(folder)
    # ponytail: poll both files; switch to inotify if this interval shows up in profiles
    while True:
        await asyncio.sleep(0.5)
        token = source_token(folder)
        if token is None or token == seen:
            continue
        seen = token
        yield "data: changed\n\n"


def _meeting(record: MeetingRecord) -> Meeting:
    return Meeting(
        id=record.id,
        source=record.source,
        conflict_count=record.conflict_count,
        title=_field(record.title),
        when=_field(record.when),
        who=_field(record.who),
        location=_field(record.location),
        status=_field(record.status),
        notes=_field(record.notes),
        ids=_field(record.ids),
    )


def _field(record: FieldRecord) -> FieldValue:
    return FieldValue(crm=record.crm, calendar=record.calendar, conflict=record.conflict)
