import json
from pathlib import Path

from app.services.ingestion import source_token


def test_source_token_follows_both_files(tmp_path: Path):
    crm = tmp_path / "crm_events.json"
    calendar = tmp_path / "calendar_events.json"
    crm.write_text("[]", encoding="utf-8")
    calendar.write_text("[]", encoding="utf-8")
    first = source_token(tmp_path)

    crm.write_text(json.dumps([{"id": "CRM-1"}]), encoding="utf-8")
    assert source_token(tmp_path) != first

    calendar.write_text("{", encoding="utf-8")
    assert source_token(tmp_path) is None
