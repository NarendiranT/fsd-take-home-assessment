# Planning notes

These are the notes from reading the brief, settling the stack, and building the app. They follow the order the decisions were made.

## How I read the requirement

The brief is short on purpose. It names the product and stops. It does not say how two records become one meeting, which system wins a disagreement, or what to do with a broken field. Those choices are the work.

I read it as three steps, and only those three:

1. Read the CRM file and the calendar file.
2. Decide which records are the same real meeting, and keep the ones that exist in only one system.
3. Serve one list. The page shows which system each value came from, and where the two systems disagree.

Nothing in the brief is a shared id. Time is close but not always equal. Some fields contradict. A few values are missing or malformed. A record that fails to parse still has to land on the list.

What I left out of the job: a database, login, editing a meeting, and turning a recurring series into future dates. Visual polish is not what the brief grades, so I treated the page as a way to see sources and disagreements, and stopped there.

I asked for a written plan before any file was added. The first pass of that plan was one Python file and one HTML page. That was enough to name the product. It was not the shape I wanted to ship.

## Tech stack

The brief says use whatever I am comfortable with, and start the service with one command.

I confirmed this stack before the folder layout was filled in:

| Piece | Choice | Why |
| --- | --- | --- |
| API | Python, FastAPI, Uvicorn, Pydantic | One process, typed request and response, docs generated from the routes |
| Page | HTML, CSS, and JavaScript modules | One screen. No build step, no package install |
| State | One store module | The page redraws from state. Clicks update the store |
| Run | `python3 run.py`, and Docker as the other way | The brief asks for a single command. I wanted that command to work without Docker as well |
| Tests | pytest on the API, a small self-check on the page helpers | Enough to lock the pipeline and the filter window |

The page has no `npm` install. A frontend requirements file would have been empty, so I did not add one. `requirements.txt` at the repo root installs the API packages.

I considered the Python standard library alone, with one script serving the page. I dropped that once I wanted a real app layout: models, schemas, services, and a route. FastAPI is that layout. A frontend framework, a state library, and a router were the same kind of extra. One page does not need them.

## Architecture

I asked whether a named design pattern belonged here. A repository, a strategy per source, a factory, or a pipeline class would each wrap a single implementation. Nothing else would call them. I left them out.

What I kept is the steps of one request. Matching stays separate from filling fields, so two records can be the same meeting and still disagree.

```
backend/app
  main.py                  app entry
  api/meetings.py          the list, and the file-change stream
  services/ingestion.py    read the two JSON files
  services/normalization.py  one record shape, repair bad values
  services/matcher.py      collapse in-file duplicates, then pair across files
  services/reconciliation.py  fill each field and mark conflicts
  models/meeting.py        record the services pass around
  schemas/meeting.py       JSON the route returns
frontend/src
  store.js                 the only client state
  api.js                   fetch the list
  render.js                draw from the store
  format.js                filters, labels, page window
  main.js                  subscribe, load, then watch
```

The route calls reconciliation. Reconciliation calls ingestion, normalization, and the matcher, in that order. Models are the internal record. The schema is only the response.

The page is a single view with a store. `index.html` is the mount point. The store holds the meeting list, whether the load worked, the error, which row is open, the search text, the filters, the page, and which header view is showing. `load()` and the click actions update that state and notify listeners. The renderer draws from the state. Click handlers call the store. They do not edit the page on their own.

Meetings and About are two views in that store. They are buttons in the header. They are not routes.

One list endpoint is enough. The open row, the filters, and the page are client state, so a meeting-by-id route adds nothing.

`docker compose up --build` starts the API and nginx. `python3 run.py` starts the API and a small file server that forwards `/api` to it. Both are the same app.

## How the work went

1. Read the brief and write the plan. No code until the steps and the folder tree were agreed.
2. Reject a pattern layer. Keep ingestion, normalization, matching, and reconciliation as the path of `GET /api/meetings`.
3. Replace the single HTML file with the store. The tree I wanted is `backend/app` (models, schemas, services, api), `frontend/`, `data/`, `docker-compose.yml`, `README.md`, and this file.
4. Build that path, then the page that only draws the store.
5. Turn the list into the meetings screen: search, source filter, conflict filter, a selected row, and a side panel with both systems side by side.
6. Page that list in the browser, after search and filters.
7. Watch both files and refresh the open page when they change.
8. Add `run.py` and the root requirements file so the app starts without Docker. Initialize git and ignore virtualenvs, caches, and `.env` files.
9. Fix the local proxy so a file-change event actually reaches the browser.
10. Rewrite the README as setup, stack, and how to run. The matching rules stay in the code and the tests.

## Beyond the brief

The brief stops at ingest, reconcile, one API, and a page that shows conflicts. These are the pieces I added after that worked.

**Store-driven page.** Search, source, conflict status, the selected row, and the header view live in one module. A quiet reload replaces the list and leaves the rest of that state in place.

**Filters, then pages.** The API returns the full list. The page shows 8 rows. Previous, Next, and the page numbers slice the list after search and filters. A new search or filter returns to the first page. An empty result hides the pager.

**Live updates.** `GET /api/events` is a Server-Sent Events stream. The API looks at both files about twice a second. When the text of either file changes, and both files are still valid JSON, it sends `data: changed`. The page listens with `EventSource` and reloads without the loading flash. A half-written save is ignored until the JSON parses again. A dropped stream reloads once when it reconnects.

The first version of `run.py` waited for 1024 bytes before it forwarded a response. One change event is smaller than that, so the page never saw it. The proxy now sends the stream with chunked transfer encoding. In Docker, nginx does the same job with buffering turned off on `/api/events`.

**Two ways to start.** `python3 run.py` for local work. `docker compose up --build` for the same ports behind nginx.

**API docs.** FastAPI publishes Swagger, ReDoc, and the OpenAPI document from the routes. The event stream is `text/event-stream`, so a browser or `curl -N` is the practical way to watch it.

**Observability.** The API writes JSON logs and a Prometheus text page from the standard library. A request log carries the id, status, and duration. A reconcile log carries the meeting count, the conflict count, and the duration. `GET /health` is the liveness check Docker uses. `GET /metrics` stays on the API port. I did not add a metrics client, a tracing vendor, or a log shipper. Those belong once this process is one of several.
