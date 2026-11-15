# Brief Relay · development component

A focused open-source Content Snare alternative in preparation. **Not a finished or published product.**

Current component: client checklists with revocable access tokens, versioned text answers and file attachments, owner approval/change requests, closed requests and JSON history export. Approved answers cannot be silently replaced, and stale reviews cannot approve newer content.

Run `python3 -m unittest discover -s tests -v` with Python 3.10+. No external dependencies. The `Checklists` API stores a SQLite library. Tokens are returned at creation/rotation, stored only as hashes and excluded from export. Owner methods currently rely on their caller for authorization: do not expose the library directly over HTTP.

Still required: HTTP upload/download endpoints, owner authentication, a polished client/owner web UI, six languages, browser acceptance, deployment instructions, visual README and launch handoff. No reminders, email delivery, full Content Snare parity or compliance certification claimed.

MIT licensed. See [scope](docs/SCOPE.md).

Attachments are stored atomically in SQLite: 10 MiB per file and 100 MiB per request including immutable history. Plain filenames only; no disk paths or active previews. `download` checks the current client token and request membership for every revision. JSON exports include filename/size/SHA-256 metadata; binary files are retrieved separately. The future HTTP layer must stream bounded uploads and force attachment downloads with `application/octet-stream` and `nosniff`. This library does not scan files for malware.
