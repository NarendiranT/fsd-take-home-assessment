from pathlib import Path

from app.services.reconciliation import reconcile

DATA = Path(__file__).resolve().parents[2] / "data"


def _meetings():
    return reconcile(DATA)


def _with_crm(crm_id: str):
    matches = [meeting for meeting in _meetings() if meeting.ids.crm and crm_id in meeting.ids.crm]
    assert len(matches) == 1
    return matches[0]


def test_pinnacle_is_one_meeting_with_both_calendar_ids():
    meeting = _with_crm("CRM-1005")
    calendar_ids = meeting.ids.calendar or ""
    assert "CAL-A5" in calendar_ids
    assert "CAL-A6" in calendar_ids
    involved = [
        item
        for item in _meetings()
        if (item.ids.calendar and ("CAL-A5" in item.ids.calendar or "CAL-A6" in item.ids.calendar))
    ]
    assert len(involved) == 1


def test_summit_location_is_a_conflict():
    meeting = _with_crm("CRM-1002")
    assert meeting.location.conflict is True
    assert meeting.location.crm
    assert meeting.location.calendar


def test_atlas_lunch_is_15_march():
    meeting = _with_crm("CRM-1008")
    assert meeting.when.crm is not None
    assert "15 Mar 2025" in meeting.when.crm
    assert meeting.ids.calendar == "CAL-A9"


def test_lakeshore_stays_in_the_crm():
    meeting = _with_crm("CRM-1003")
    assert meeting.source == "crm"
    assert meeting.ids.calendar is None
