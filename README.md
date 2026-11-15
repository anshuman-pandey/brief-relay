# Brief Relay · development component

A focused open-source Content Snare alternative in preparation. **Not a finished or published product.**

Current component: client checklists with revocable access tokens, versioned text answers, owner approval/change requests, closed requests and JSON history export. Approved answers cannot be silently replaced, and stale reviews cannot approve newer content.

Run `python3 -m unittest discover -s tests -v` with Python 3.10+. No external dependencies. The `Checklists` API stores a SQLite library. Tokens are returned at creation/rotation, stored only as hashes and excluded from export. Owner methods currently rely on their caller for authorization: do not expose the library directly over HTTP.

Still required: secure file upload/download, owner authentication, a polished client/owner web UI, six languages, browser acceptance, deployment instructions, visual README and launch handoff. No reminders, email delivery, full Content Snare parity or compliance certification claimed.

MIT licensed. See [scope](docs/SCOPE.md).
