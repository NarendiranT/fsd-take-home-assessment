# Event Sync

CRM meetings and calendar events for the same sales team, shown as one list. A row that exists in both systems keeps both values. Where the place, the time, or a cancellation disagrees, the row says so.

## Run

```sh
pip install -r requirements.txt
python3 run.py
```

Open http://127.0.0.1:8080. The API is http://127.0.0.1:8000/api/meetings. Saving either file under `data/` refreshes the list in place. Ctrl-C stops both processes.

The same ports with Docker: `docker compose up --build`.

## Matching

The two files do not share an id. A CRM row pairs with a calendar row when the New York date matches and a person or a company matches. `David Park` lines up with `david.park@…`. A company name has to show up as a word in the calendar title. The relationship owner lines up with the organizer, and also with an attendee when someone else sent the invite.

Times with no zone are New York local. A trailing `Z` is UTC. The Crestview calendar row is the only one marked that way: 19:00 UTC is 15:00 in New York, against 14:00 in the CRM.

A missing time does not block a pair. Neither does a gap under six hours. The gap is kept and shown. Two calendar rows collapse into one meeting when they are on the same day, start within an hour, and share an attendee email. That is the Pinnacle update, `CAL-A5` and `CAL-A6`. The weekly syncs stay separate because the dates differ.

`03-15/2025` is read as 15 March 2025. An end time written without seconds still parses. `[at]` in an email is treated as `@`.

## Conflicts

If only one side has a value, that value is used and the other side stays blank. If one location contains the other, the longer one is shown (`Boston Office - Room 301` and `Boston Office` are the same place). If both sides state a different place or a different time, both are shown and the field is marked. No side is chosen as the truth.

`Completed` and `confirmed` are not a conflict. One system logged the meeting after it happened. `Cancelled` against `confirmed` is a conflict. Titles, notes, and the calendar description are both kept. They are two writeups of the same meeting, not a field to pick between.

## Tests

From `backend/`, after `pip install -r requirements.txt` at the repo root:

```sh
python -m pytest
```

Time spent: 
