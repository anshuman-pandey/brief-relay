# Brief Relay · development component

A focused open-source Content Snare alternative in preparation. **Not a finished or published product.**

Current component: client checklists with revocable access tokens, versioned text answers and file attachments, owner approval/change requests, closed requests and JSON history export. Approved answers cannot be silently replaced, and stale reviews cannot approve newer content.

Run `python3 -m unittest discover -s tests -v` with Python 3.10+. Install HTTP dependencies with `pip install -r requirements.txt`. The `Checklists` API stores a SQLite library. Tokens are returned at creation/rotation, stored only as hashes and excluded from export. Owner methods currently rely on their caller for authorization: do not expose the library directly over HTTP.

Still required: a polished client/owner web UI, six languages, browser acceptance, deployment instructions, visual README and launch handoff. No reminders, email delivery, full Content Snare parity or compliance certification claimed.

MIT licensed. See [scope](docs/SCOPE.md).

Attachments are stored atomically in SQLite: 10 MiB per file and 100 MiB per request including immutable history. Plain filenames only; no disk paths or active previews. `download` checks the current client token and request membership for every revision. JSON exports include filename/size/SHA-256 metadata; binary files are retrieved separately. The HTTP layer bounds request and file reads and forces attachment downloads with `application/octet-stream` and `nosniff`. This library does not scan files for malware.

## Run the development API

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export BRIEF_OWNER_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python server.py
```

List/create requests at `/api/owner/requests` with `Authorization: Bearer <owner key>`; creation JSON is `{"title":"Website brief","labels":["Brand assets"]}`. Creation returns a request ID and client token. Clients use their token at `/api/requests/<id>` and submit text via `/items/<item>` (JSON `revision`, `body`) or files via `/items/<item>/file` (multipart `revision`, `file`). Owner review uses `/api/owner/requests/<id>/review` with `item_id`, `revision`, `decision`, `note`. Decisions are `approved` or `changes_requested`. `/rotate` revokes the old client token; `/closed` accepts JSON `closed`; `/export` returns JSON revision history.

The server binds only to 127.0.0.1:8090. This is a runnable API, **not a finished browser application or production deployment**. Keep credentials out of URLs and logs. Owner credentials grant access to all requests. No cookie authentication or cross-origin API access is enabled. Restarting with a different owner key invalidates the old owner key; client keys remain in the database. Back up the SQLite database before upgrades. Do not expose Flask's development server publicly.
