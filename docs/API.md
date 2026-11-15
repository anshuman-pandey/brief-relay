# Brief Relay API

List/create requests at `/api/owner/requests` with `Authorization: Bearer <owner key>`; creation JSON is `{"title":"Website brief","labels":["Brand assets"]}`. Creation returns a request ID and client token. Clients use their token at `/api/requests/<id>` and submit text via `/items/<item>` (JSON `revision`, `body`) or files via `/items/<item>/file` (multipart `revision`, `file`). Owner review uses `/api/owner/requests/<id>/review` with `item_id`, `revision`, `decision`, `note`. Decisions are `approved` or `changes_requested`. `/rotate` revokes the old client token; `/closed` accepts JSON `closed`; `/export` returns JSON revision history.

The server binds only to 127.0.0.1:8090. This is a runnable API, **not a finished browser application or production deployment**. Keep credentials out of URLs and logs. Owner credentials grant access to all requests. No cookie authentication or cross-origin API access is enabled. Restarting with a different owner key invalidates the old owner key; client keys remain in the database. Back up the SQLite database before upgrades. Do not expose Flask's development server publicly.

## Storage and access

SQLite stores immutable text and file revisions. Limits: 10 MiB per file, 100 MiB per request including history. JSON history exports contain file metadata, not binary content. Client tokens are stored as hashes and may be revoked with rotation. Owner methods in the Python library assume their caller has authenticated; the HTTP routes enforce owner bearer authentication.
