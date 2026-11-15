<p align="center">
  <img src="docs/assets/hero.svg" alt="Brief Relay — get the brief, keep the approval. Collect, review, and approve client responses." width="100%">
</p>

<p align="center">
  <a href="https://github.com/anshuman-pandey/brief-relay/actions/workflows/check.yml"><img src="https://github.com/anshuman-pandey/brief-relay/actions/workflows/check.yml/badge.svg" alt="Core checks"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-d8f17a?labelColor=102a2a" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/status-API_preview-d8f17a?labelColor=102a2a" alt="API preview">
</p>

<p align="center"><strong>Open-source client intake and approvals. A focused alternative to Content Snare workflows.</strong><br>Collect text and files, request changes, and approve the exact revision you reviewed.</p>

<p align="center"><a href="#quick-start">Run locally</a> · <a href="docs/API.md">API guide</a> · <a href="#what-works-today">What works</a> · <a href="docs/SCOPE.md">Scope &amp; comparison</a></p>

> **Public development preview.** The authenticated API runs locally today. A browser interface, six-language support, and browser acceptance are still in development. The graphic above illustrates the implemented workflow; it is not an app screenshot.

## Stop losing the latest version

A client sends a logo. You ask for a change. They replace the file. Which version did you approve?

Brief Relay keeps each response as an immutable revision. An approval belongs to that revision. Approved items stay locked until the owner requests changes, and an outdated review cannot approve a newer submission.

## What works today

| Collect | Review | Keep control |
| :--- | :--- | :--- |
| Create a checklist of up to 50 items | Approve an exact response revision | Revoke a client key immediately |
| Receive text or file responses | Request changes with a note | Close a request to submissions |
| Preserve previous submissions | Reject stale edits and approvals | Export JSON history and download files |

Files live in SQLite alongside their revisions: **10 MiB per file**, **100 MiB per request including history**. Downloads require access to the matching request. JSON exports contain file metadata; file bytes are downloaded separately.

## Quick start

Requires Python 3.10+.

```sh
git clone https://github.com/anshuman-pandey/brief-relay.git
cd brief-relay
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export BRIEF_OWNER_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python server.py
```

The API listens at **`http://127.0.0.1:8090`**. Keep the owner key available in a second terminal to create your first request:

```sh
curl http://127.0.0.1:8090/api/owner/requests \
  -H "Authorization: Bearer $BRIEF_OWNER_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Website brief","labels":["Brand assets","Who is your audience?"]}'
```

The response contains a request `id` and client `token`. Use the client token to submit responses; use the owner key to review them. **[Continue with the API guide →](docs/API.md)**

## Where it fits

Brief Relay is for developers and small agencies who want to own a focused client collection and approval workflow.

| Workflow | Brief Relay today |
| :--- | :--- |
| Content Snare-style client checklists, files, and approval | Implemented through the API |
| Self-hosted storage and portable records | SQLite, JSON history, separate file downloads |
| Visual owner/client workspace | Planned; not yet available |
| Automated email reminders and team collaboration | Not implemented |
| Complete Content Snare feature parity | Not claimed |

See the [scope and vendor reference](docs/SCOPE.md) for the exact comparison boundary.

## Development

```sh
python -m unittest discover -s tests -v
```

The current suite has **25 tests**, covering revision conflicts, file persistence, access isolation, token revocation, storage limits, and the HTTP approval flow. GitHub Actions runs the suite on each push and pull request.

Next milestones: a polished owner/client UI, six languages, and real browser workflow tests. Contributions should include a reproducible use case and relevant tests. Report bugs through [GitHub Issues](https://github.com/anshuman-pandey/brief-relay/issues).

## Operating boundaries

The included server is for local development, not public production hosting. Keep credentials out of URLs and logs; the owner key grants access to every request. Files are downloaded as attachments and are not scanned for malware. Back up the SQLite database before upgrades. See [API and storage notes](docs/API.md#storage-and-access).

[MIT licensed](LICENSE). Your storage. Your client records. Your review trail.
