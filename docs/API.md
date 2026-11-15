# Brief Relay API

List/create requests at `/api/owner/requests` with `Authorization: Bearer <owner key>`; creation JSON is `{"title":"Website brief","labels":["Brand assets"]}`. Creation returns a request ID and client token. Clients use their token at `/api/requests/<id>` and submit text via `/items/<item>` (JSON `revision`, `body`) or files via `/items/<item>/file` (multipart `revision`, `file`). Owner review uses `/api/owner/requests/<id>/review` with `item_id`, `revision`, `decision`, `note`. Decisions are `approved` or `changes_requested`. `/rotate` revokes the old client token; `/closed` accepts JSON `closed`; `/export` returns JSON revision history.

The server binds only to 127.0.0.1:8090. This is a runnable API, **not a finished browser application or production deployment**. Keep credentials out of URLs and logs. Owner credentials grant access to all requests. No cookie authentication or cross-origin API access is enabled. Restarting with a different owner key invalidates the old owner key; client keys remain in the database. Back up the SQLite database before upgrades. Do not expose Flask's development server publicly.

## Storage and access

SQLite stores immutable text and file revisions. Limits: 10 MiB per file, 100 MiB per request including history. JSON history exports contain file metadata, not binary content. Client tokens are stored as hashes and may be revoked with rotation. Owner methods in the Python library assume their caller has authenticated; the HTTP routes enforce owner bearer authentication.

## Browser workspace

Open `/` for the owner workspace. Client mode is `/?client=1`; clients enter their request ID and key separately. Credentials are held in memory, not localStorage or URLs. Reload or Lock workspace clears access. The owner key is the value set in `BRIEF_OWNER_KEY`. Client keys are displayed only on creation or rotation; save the handoff before reloading. Replacing a client key revokes the old one immediately. A file chosen with a text response takes precedence and is submitted as a file revision.

## Browser acceptance

Install Playwright in an external test environment (`npm install playwright`) and provide its module directory through `NODE_PATH` if necessary. Start the server using a disposable database and test-only owner key. Run `BRIEF_OWNER_KEY=<test key> node scripts/browser.cjs`; optionally set `BRIEF_URL` and `CHROMIUM`. The test creates synthetic requests and exports and must not run against production data.
