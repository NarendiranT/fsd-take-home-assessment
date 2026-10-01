from app.observe import metrics_text, note_reconcile, note_request, reset


def test_metrics_include_requests_and_the_latest_reconcile():
    reset()
    note_request("GET", "/api/meetings", 200)
    note_reconcile(meetings=2, conflicts=1, seconds=0.012)

    text = metrics_text()

    assert 'http_requests_total{method="GET",path="/api/meetings",status="200"} 1' in text
    assert "reconcile_total 1" in text
    assert "reconcile_meetings 2" in text
    assert "reconcile_conflicts 1" in text
    assert "reconcile_duration_seconds 0.012000" in text
