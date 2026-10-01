# Planning notes

## What the brief actually asks for

The brief is short on purpose. It does not say how to match records, which system wins a disagreement, or what to do with a broken field. Those choices are the work.

The product is three steps:

1. Read the CRM file and the calendar file.
2. Decide which records are the same real meeting, and keep the ones that exist in only one system.
3. Serve one list. The page shows which system each value came from, and where the two systems disagree.

There is no shared id. Time is close but not always equal. Some fields contradict. A few values are missing or malformed. Nothing is dropped because it failed to parse.

What is not part of the job: visual polish, a database, login, editing meetings, or turning a recurring series into future dates.

## Architecture we settled on

One API process and one page, started together with `docker compose up --build`.

```
backend/app
  main.py                  app entry
  api/meetings.py          GET /api/meetings
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
  main.js                  subscribe, then load
```

The route calls reconciliation. Reconciliation calls ingestion, normalization, and the matcher, in that order. Models are the internal record. The schema is only the response. No file sits off that path.

A repository, a strategy per source, or a pipeline class was considered and dropped. Each would have had one implementation. The split above is the steps of the request, not a pattern layer.

The page is a single view with a store, not one HTML file that fetches and paints itself. `index.html` is the mount point. The store holds the meeting list, whether the load worked, the error, and which row is open. `load()` and `toggle(id)` update that state and notify listeners. The renderer draws from the state. Click handlers call the store. They do not edit the page on their own. No router, no component library, no state library.

One endpoint. The open row is client state, so a meeting-by-id route is unnecessary.

## Rules agreed before coding

Match on the New York date plus a person or a company. A person is the client name against an attendee email, or the relationship owner against the organizer or an attendee. A company is a distinctive word from the CRM company in the calendar title. Time does not decide the pair. A missing time, or a gap under six hours, still pairs, and the gap is stored.

Unmarked timestamps are New York local. A trailing `Z` is UTC and is converted before comparing. Same calendar day is not enough to merge two different meetings.

Inside the calendar, two rows collapse when they share a day, start within an hour, and share an attendee email. Both ids stay on the meeting. Recurring rows on different days stay separate.

After a pair exists, each field keeps the CRM value and the calendar value.

- One side empty: use the side that has it.
- One location contained in the other: show the longer one. Same place, written with more detail.
- Both sides state a different place, a different time, or a cancellation against a still-confirmed event: show both and mark a conflict. Do not pick a winner.
- `Completed` against `confirmed` is not a conflict. One system logged the meeting after it happened.
- Titles, notes, and the calendar description are two writeups. Both stay visible. They are not conflicts.

## Checks

Four outcomes lock the rules: the in-file duplicate is one meeting with both calendar ids, a place disagreement is marked, a malformed date still lands on the right day, and a CRM-only meeting stays CRM-only.
