# Persistent server setup

This recipe runs Brief Relay on your own machine with a persistent SQLite volume. Container persistence and restore are tested; a public HTTPS deployment has **not** been verified. The six-language interface is implemented; native-speaker review is pending.

## Docker Compose

```sh
python3 scripts/setup.py
docker compose up -d --build
```

The setup script creates `.env` with a random owner key and mode `0600`. It refuses to overwrite an existing file. Read that file locally and use its key to open the owner workspace at `http://127.0.0.1:8090`. Keep it out of chat, Git, screenshots and client handoffs.

The service runs as UID/GID 10001, with a read-only application filesystem, a temporary scratch directory, and durable storage in the `brief-data` named volume. `docker compose down` retains that volume; **do not use `down -v` unless you intend to delete all client records**. Use `docker compose logs` for startup diagnostics. Waitress serves the application instead of Flask's development server.

Networks that use a private trusted certificate authority may build with an optional CA bundle, without disabling TLS verification:

```sh
docker build --secret id=pip_ca,src=/path/to/trusted-ca-bundle.pem -t brief-relay-local .
```

The secret is available only during dependency installation and is not copied into the image. Normal networks do not need this build option.

## Back up and restore

A backup contains client text, files, review history and hashed client keys. Keep it private and encrypt off-machine copies. The owner key lives in `.env`, separately from SQLite; preserve it securely too.

For Compose, stop the writer before copying the database. Use a fresh private directory each time:

```sh
umask 077
mkdir backup-2026-11-15
docker compose stop brief-relay
docker compose cp brief-relay:/data/brief.sqlite3 backup-2026-11-15/source.sqlite3
python3 scripts/backup.py backup-2026-11-15/source.sqlite3 backup-2026-11-15/brief.sqlite3
docker compose start brief-relay
```

The helper uses SQLite's backup API, checks integrity, creates the result with mode `0600`, and refuses to overwrite a destination. For a non-container installation it can also back up the live database directly.

Restore only into a stopped service. Retain a separate backup of the current database before replacement. Copy the chosen backup into `/data/brief.sqlite3`, set its owner to UID/GID `10001:10001` and mode `0600`, then start the service. Restoring an older backup also restores its earlier client-token state: rotate client keys after recovery if any were revoked since that backup. Validate both a file download and a new submission after restoring.

The disposable acceptance script demonstrates a clean-volume restore and a post-restore write:

```sh
docker build -t brief-relay-acceptance:local .
python3 scripts/container_acceptance.py
```

It creates uniquely named test containers and volumes, uses synthetic records and a random test key, and cleans them up afterwards. It does not deploy or change a production service.

## Before serving remote clients

The Compose port binds to **127.0.0.1 only**. Its local URL is not a remote client link. To serve clients on other machines, configure an HTTPS reverse proxy on your own domain, forward to this loopback port, and set proxy upload limits/timeouts compatible with the 10 MiB file limit. Do not forward untrusted proxy headers or put bearer keys in URLs. Verify the complete owner/client workflow from another device over HTTPS before announcing a live service.

This recipe does not provision a domain, TLS certificate, public host, email reminders, malware scanning, global storage quotas, or abuse-rate limiting. Owner credentials grant access to all requests. Scope access accordingly and plan storage capacity: the 100 MiB cap applies to each request, including its revision history, not the entire installation.

## Without containers

```sh
pip install -r requirements.txt
export BRIEF_DATA_DIR=./data
# Set BRIEF_OWNER_KEY to your securely stored random owner key.
python serve.py
```

The default bind address is `127.0.0.1:8090`. Run it under your operating system's service manager for automatic restarts. Change the owner key and restart to revoke an old owner credential; existing client keys are unaffected.
