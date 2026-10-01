"""Process-local logs and counters. No extra package."""

import json
import logging
import time
import uuid
from collections import Counter

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

log = logging.getLogger("eventsync")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False

# ponytail: one process, one counter map. A collector if you run more than one worker.
_requests: Counter[tuple[str, str, int]] = Counter()
_reconcile_runs = 0
_reconcile_meetings = 0
_reconcile_conflicts = 0
_reconcile_seconds = 0.0
_source_changes = 0

_QUIET = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


def reset() -> None:
    global _reconcile_runs, _reconcile_meetings, _reconcile_conflicts, _reconcile_seconds, _source_changes
    _requests.clear()
    _reconcile_runs = 0
    _reconcile_meetings = 0
    _reconcile_conflicts = 0
    _reconcile_seconds = 0.0
    _source_changes = 0


def note_request(method: str, path: str, status: int) -> None:
    _requests[(method, path, status)] += 1


def note_reconcile(meetings: int, conflicts: int, seconds: float) -> None:
    global _reconcile_runs, _reconcile_meetings, _reconcile_conflicts, _reconcile_seconds
    _reconcile_runs += 1
    _reconcile_meetings = meetings
    _reconcile_conflicts = conflicts
    _reconcile_seconds = seconds
    log_event(
        "reconcile",
        meetings=meetings,
        conflicts=conflicts,
        duration_ms=round(seconds * 1000, 1),
    )


def note_source_change() -> None:
    global _source_changes
    _source_changes += 1
    log_event("source_changed")


def log_event(event: str, **fields: object) -> None:
    log.info(json.dumps({"event": event, **fields}, separators=(",", ":")))


def metrics_text() -> str:
    lines = [
        "# HELP http_requests_total HTTP requests handled by this process",
        "# TYPE http_requests_total counter",
    ]
    for (method, path, status), count in sorted(_requests.items()):
        lines.append(
            "http_requests_total{"
            f'method="{_label(method)}",path="{_label(path)}",status="{status}"'
            f"}} {count}"
        )
    lines += [
        "# HELP reconcile_total Times the meeting list was built",
        "# TYPE reconcile_total counter",
        f"reconcile_total {_reconcile_runs}",
        "# HELP reconcile_meetings Meetings in the latest reconcile",
        "# TYPE reconcile_meetings gauge",
        f"reconcile_meetings {_reconcile_meetings}",
        "# HELP reconcile_conflicts Meetings with a conflict in the latest reconcile",
        "# TYPE reconcile_conflicts gauge",
        f"reconcile_conflicts {_reconcile_conflicts}",
        "# HELP reconcile_duration_seconds Duration of the latest reconcile",
        "# TYPE reconcile_duration_seconds gauge",
        f"reconcile_duration_seconds {_reconcile_seconds:.6f}",
        "# HELP source_changes_total Valid file changes noticed by the event stream",
        "# TYPE source_changes_total counter",
        f"source_changes_total {_source_changes}",
        "",
    ]
    return "\n".join(lines)


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def observe_requests(request: Request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        finally:
            seconds = time.perf_counter() - started
            path = request.url.path
            note_request(request.method, path, status)
            if path not in _QUIET:
                log_event(
                    "request",
                    request_id=request_id,
                    method=request.method,
                    path=path,
                    status=status,
                    duration_ms=round(seconds * 1000, 1),
                )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> PlainTextResponse:
        return PlainTextResponse(metrics_text(), media_type="text/plain; version=0.0.4; charset=utf-8")


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
