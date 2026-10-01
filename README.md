# Event Sync

A small view of sales meetings. The CRM and the calendar each keep their own file. This app reads both, turns them into one list, and shows which system each value came from.

## Setup

You need Python 3.12 or newer, and pip. Docker is optional.

From the repo root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate with `.venv\Scripts\activate`.

`requirements.txt` points at `backend/requirements.txt`. That installs FastAPI, Uvicorn, and pytest. The page has no `npm` install and no build step.

The API reads JSON from `DATA_DIR`. `run.py` sets that to the `data/` folder in this repo. Docker does the same by mounting `./data`.

## Tech stack

| Piece | What it is |
| --- | --- |
| API | Python, FastAPI, Uvicorn, Pydantic |
| Page | HTML, CSS, and JavaScript modules |
| Data | `data/crm_events.json` and `data/calendar_events.json` |
| Local run | `run.py` starts the API and a small file server |
| Docker | Python 3.12 for the API, nginx for the page |

There is no database, no login, and no frontend framework. The page keeps its own state in one module and redraws from that.

## How to run

With the virtualenv active:

```sh
python3 run.py
```

Then open the page at [http://127.0.0.1:8080](http://127.0.0.1:8080). The API listens on [http://127.0.0.1:8000](http://127.0.0.1:8000). Ctrl-C stops both.

The page server forwards anything under `/api` to the API. Save either file in `data/` and the list refreshes on its own.

The same ports with Docker:

```sh
docker compose up --build
```

nginx serves the page on port 8080 and proxies `/api` to the API container.

## Architecture

One request builds the list. Nothing else writes it.

1. `ingestion` reads the two JSON files.
2. `normalization` turns each row into one internal record.
3. `matcher` groups rows that are the same meeting, and keeps rows that exist in only one file.
4. `reconciliation` builds the list the API returns, sorted by time.
5. The page loads that list into a store. The renderer draws from the store.

```
data/*.json
    → ingestion → normalization → matcher → reconciliation
    → GET /api/meetings
    → store.js → render.js
```

`index.html` is only the mount point. Search, filters, the open row, and the current page live in `frontend/src/store.js`. Click handlers call the store. They do not edit the DOM on their own.

```
backend/app
  main.py                     FastAPI app, CORS for GET
  api/meetings.py             /api/meetings and /api/events
  services/ingestion.py       read the two files
  services/normalization.py   one record shape
  services/matcher.py         pair records
  services/reconciliation.py  the list the route returns
  models/meeting.py           records inside the services
  schemas/meeting.py          JSON the route returns
frontend/src
  main.js                     subscribe, load, then watch
  store.js                    the only client state
  api.js                      fetch the list
  render.js                   draw from the store
  format.js                   filters, labels, page window
```

### Live updates (SSE)

`GET /api/events` is a Server-Sent Events stream. The API looks at both files about twice a second. When the text of either file changes, and both files are still valid JSON, it sends:

```
data: changed

```

The page opens that stream with `EventSource("/api/events")`. Each message reloads the list without the loading flash. If the stream drops and reconnects, the page reloads once on the way back, too.

A half-written save is ignored until the JSON parses again.

`run.py` proxies this stream with chunked transfer encoding, so the browser can read events while the response is still open. In Docker, nginx does the same job with buffering turned off on `/api/events`.

### Pagination

The API returns the full list in one response. Paging happens in the browser.

The meetings view shows 8 rows at a time (`PAGE_SIZE` in `frontend/src/format.js`). Previous, Next, and the page numbers slice the list you are already looking at, after search and filters. A new search, source filter, or status filter jumps back to the first page. If the current page would be past the end, the window clamps to the last page that still has rows.

An empty filter result shows “No meetings match.” and hides the pager.

## Backend URLs

Swagger is on the API port. FastAPI builds it from the routes.

| What | URL |
| --- | --- |
| Meeting list | [http://127.0.0.1:8000/api/meetings](http://127.0.0.1:8000/api/meetings) |
| File-change stream | [http://127.0.0.1:8000/api/events](http://127.0.0.1:8000/api/events) |
| Swagger UI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| ReDoc | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |
| OpenAPI document | [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json) |

`GET /api/meetings` returns `{ "meetings": [ ... ] }`. Each meeting has `id`, `source` (`crm`, `calendar`, or `both`), `conflict_count`, and these fields: `title`, `when`, `who`, `location`, `status`, `notes`, `ids`. Each field has `crm`, `calendar`, and `conflict`.

`GET /api/events` stays open. It is `text/event-stream`, not JSON. Swagger will show the route. A browser tab or `curl -N` is the easier way to watch it.

## Frontend URLs

The UI is one page. Meetings and About are buttons in the header, not separate paths. About is a short description of the page. Meetings is the list.

| What | URL |
| --- | --- |
| Meetings (home) | [http://127.0.0.1:8080/](http://127.0.0.1:8080/) |
| Stylesheet | [http://127.0.0.1:8080/src/styles.css](http://127.0.0.1:8080/src/styles.css) |
| App script | [http://127.0.0.1:8080/src/main.js](http://127.0.0.1:8080/src/main.js) |
| Meeting list, via the page | [http://127.0.0.1:8080/api/meetings](http://127.0.0.1:8080/api/meetings) |
| Live updates, via the page | [http://127.0.0.1:8080/api/events](http://127.0.0.1:8080/api/events) |

On Meetings you can search by client, title, or attendee, filter by source (All, CRM, Calendar) or by status (all, has conflicts, no conflicts), move between pages, and select a row. The side panel shows attendees, conflict flags, and the CRM and calendar values side by side.

## Sample data

Both files are in `data/`. They do not share an id. Some meetings are in both files, some in only one.

**CRM** — `data/crm_events.json`, 20 records (`CRM-1001` through `CRM-1020`).

Fields: `crm_id`, `subject`, `client_name`, `client_company`, `relationship_owner`, `meeting_date`, `meeting_time`, `meeting_type`, `location`, `notes`, `status`, `created_at`.

```json
{
  "crm_id": "CRM-1001",
  "subject": "Q1 Portfolio Review",
  "client_name": "David Park",
  "client_company": "Meridian Capital",
  "relationship_owner": "Sarah Chen",
  "meeting_date": "2025-03-10",
  "meeting_time": "14:00",
  "meeting_type": "In-Person",
  "location": "HQ - Conference Room B",
  "notes": "Review Q1 allocation strategy. David requested updated fee schedule.",
  "status": "Completed",
  "created_at": "2025-02-28T09:15:00Z"
}
```

**Calendar** — `data/calendar_events.json`, 22 records (`CAL-A1` through `CAL-A22`).

Fields: `event_id`, `title`, `organizer`, `attendees`, `start_time`, `end_time`, `location`, `description`, `is_recurring`, `status`, `created_at`.

```json
{
  "event_id": "CAL-A1",
  "title": "Q1 Portfolio Review - Meridian Capital",
  "organizer": "sarah.chen@firma.com",
  "attendees": ["sarah.chen@firma.com", "david.park@meridiancap.com"],
  "start_time": "2025-03-10T14:00:00",
  "end_time": "2025-03-10T15:30:00",
  "location": "Conference Room B",
  "description": "Quarterly review of portfolio allocation and performance.",
  "is_recurring": false,
  "status": "confirmed",
  "created_at": "2025-02-27T10:00:00Z"
}
```

Edit either file while the app is running. After the JSON is valid again, the meetings list updates.

## Tests

From `backend/`, with the virtualenv active:

```sh
cd backend
python -m pytest
```

`backend/pytest.ini` adds that folder to the Python path, so the tests import `app` directly. `test_ingestion.py` checks that a file change is noticed and that broken JSON is ignored. `test_reconciliation.py` checks the reconciled list against the sample files.

The page helpers in `frontend/src/format.js` have a small self-check. From the repo root:

```sh
node frontend/src/format.js
```

It prints nothing when the checks pass.

## Time spent

Fill this in before you submit.
