# Teammate setup and data sharing

Group 26 — Civic Issue Matchmaker

## What a clone includes

Use branch **`feat/github-issue-transition`**. It includes the application,
documentation, and a compressed public snapshot with **21,558 GitHub issues**
(3,539 open) and **2,220 already-computed AI requirements** from all five civic
trackers. The bundle is about 9.3 MiB; see its [manifest](../data/public-issues-v1.manifest.json)
for generation time, counts and checksums. No operator database or credentials
are shared. The remaining 1,319 open issues have no cached enhancement; teammates
can still browse them without launching enrichment.

## First setup

Follow the [README quick setup](../README.md#quick-local-setup) for macOS, Linux
or Windows PowerShell. Install Python 3.11+ and Node.js 18+ (22 recommended),
create a virtual environment, install requirements, run `npm ci`, and copy
`backend/.env.example` to a **new** `backend/.env`. Keep its defaults:

```env
DATABASE_URL=sqlite:///./civic-dev.db
ENABLE_WORKER=false
APP_DEMO=false
```

Leave GitHub/OpenRouter keys absent. From `backend/`, run:

macOS/Linux:

```bash
.venv/bin/python -m app.snapshot setup
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m app.snapshot setup
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Setup validates the bundle, restores issues/cache and creates your own accounts.
Save the fresh random passwords printed once:

| Email | Role |
|---|---|
| `volunteer@civic.demo` | Contributor |
| `maintainer@civic.demo` | Curator |
| `administrator@civic.demo` | Administrator |

In another terminal at the project root, run `npm run dev` and open
**http://localhost:5173**. Both servers must remain running. Subsequent launches
need only the server commands; your SQLite database persists.

## Existing installation or updated snapshot

Stop the backend and any separate worker before importing. Preserve your `.env`
and existing database. With scanning disabled, run from `backend/`:

```bash
python -m app.snapshot import
```

Use your virtual environment's interpreter if it is not activated. Repeat import
is safe: stable upstream IDs map to existing local task/repository IDs, so accounts,
passwords, sessions, contributions, bookmarks, messages, feedback and curator
overrides remain. Issues absent from the snapshot are not deleted. Newer local
source records are not downgraded; existing complete-source context, schedules
and enablement are retained. A cached result is imported only if its fingerprint
matches that issue and local project context. The command reports skipped caches.

## Offline behavior and optional updates

`ENABLE_WORKER=false` disables background source downloads. Setup/import/browsing
make no GitHub or OpenRouter requests and perform no AI computation. Cached
requirements retain their stated/inferred labels, rationales, source quotations,
model and content hashes. No processing-job lease is copied, so a teammate's
administrator screen does not inherit a fictitious running enrichment job.

If you want live refreshes later, configure your own public-read GitHub token and
set `ENABLE_WORKER=true`. Changed issue text/context can invalidate its cache.
Paid enrichment remains a separate, explicit operator command; it is never part
of setup or browsing.

## Public-only distribution

[Snapshot format and export commands](../data/README.md) describe the explicit
public-field allowlist. The bundle excludes every local user/session/message,
notification, bookmark, contribution, feedback, preference, auth/audit record,
curator override, private backup and credential. The live `backend/civic-dev.db`
contains private records and must not be shared as the teammate seed.

## Smoke check

- Sign in with your generated local credentials.
- Confirm Projects contains five sources and imported issue counts.
- Save a profile; inspect Discover's score explanations and AI stated/inferred labels.
- Track an issue, remove the entry, then track it again.
- Inspect curator metadata and administrator progress controls using those roles.
- Restart both servers and confirm the data persists.
- Repeat import and verify your accounts, bookmarks and activity remain.

Automated snapshot tests cover public-field exclusion, clean restore, repeated
import, private-record/stable-ID preservation, cache reuse without paid requests,
freshness, integrity validation and identity-conflict rollback.

A clean Linux checkout with freshly installed dependencies also passed full-bundle
offline setup, login/discovery/evidence, two repeat imports retaining private
records, contribution removal/retracking, restart and repeat account setup. See
[the verification record](IMPLEMENTATION_REVIEW.md#teammate-handoff-verification--october-29-2026-utc).
