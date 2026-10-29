# Developer and LLM handoff

Group 26 — Civic Issue Matchmaker. Recorded October 28, 2026 (US Eastern; October 29 UTC).

Read this first when continuing in this workspace. The described AI, matching and contribution-removal implementation is now committed locally on `feat/github-issue-transition`; public data distribution is still pending.

## Immediate request and boundaries

The next task is to make teammate setup easy and distribute the imported public GitHub issues **and cached AI enhancements**, so teammates do not repeat the downloads or pay for enrichment again. The user interrupted that task to request clear documentation committed locally before switching LLMs. Documentation and the pending implementation are now committed locally; snapshot implementation has **not** started.

- Repository: `/home/walia6/repos/Civic-issue-Matchmaker`.
- Working branch: `feat/github-issue-transition`. Local `main` has not been replaced by this work.
- No push or merge is authorized by this handoff. Prepare work locally for review.
- Preserve any new working-tree changes. The previously dirty implementation has been captured in local commits; inspect `git status --short` before further work.
- Preexisting `package.json` / `package-lock.json` changes add `@openai/codex`; they are captured in a separate tooling commit.
- Do not modify DOCX/PDF references. `docs/artifcats/AGENTS.md` marks that deliberately spelled historical directory as non-authoritative.
- Private presentation material stays in gitignored `presentation-cheat-sheets/`.
- Credentials and databases are ignored. Never commit `.env`, the live database, private backups, or credential notes.

## Read in this order

1. [Master project scope](PROJECT_SCOPE.md): current GitHub civic-tech scope, roles and boundaries.
2. [README](../README.md): actual setup, startup, source operation and tests.
3. [Team setup and data handoff](TEAM_SETUP.md): what a clone includes today and what distribution work remains.
4. [AI and matching](AI_MATCHING.md): current prompt, cache, scoring and spending behavior.
5. [Implementation review](IMPLEMENTATION_REVIEW.md) and [requirements status](REQUIREMENTS_STATUS.md): observed tests and unverified acceptance targets.

Historical physical-volunteering examples are not the current product. It sources literal GitHub software issues from civic-tech repositories; it does not source pothole-filling shifts or create upstream GitHub issues.

## Current functional implementation

- Contributor, Curator and Administrator workspaces. Internally roles retain legacy `volunteer`, `maintainer`, `administrator` names.
- Five real trackers: `hackforla/website`, `hotosm/tasking-manager`, `mysociety/fixmystreet`, `openfoodfacts/openfoodfacts-server`, `openstreetmap/iD`.
- All labels/states ingested; pull requests excluded. No beginner-only whitelist. Discover defaults to open issues.
- GitHub stays authoritative and read-only. Local tracking neither reserves nor closes an issue. Multiple contributors can track the same issue.
- Profiles, filtering, matching explanations, bookmarks, contribution states, feedback, curator metadata, source controls, messages/notifications, export/deletion and SQLite backups.
- **Remove contribution** is now implemented: owner-only DELETE with stale-version protection; available in all states through My contributions → Remove contribution → Confirm removal. It removes that contribution and its local history, preserves bookmarks/source/other users, and permits tracking again.
- Passwords use scrypt; session tokens are stored as SHA-256 hashes. Do not invent missing security or acceptance test results.

## Live local data and processing

Observed at approximately **2026-10-29 02:02 UTC**; recheck before quoting these as current:

- All five full initial imports completed: **21,558 published GitHub issues**.
- **3,539 open issues** eligible for enrichment.
- Revised-prompt cache: **2,220 processed**, **2,028 with skills**.
- Latest enrichment run: running; 2,201 newly accepted, zero schema-rejected; conservative spend estimate **$1.059655 / $1.70**. Nineteen earlier paid trial results were reused.
- Actual OpenRouter account usage before this revised bulk run was approximately **$0.24515**. The user's target was roughly $2 total for this initial work. Do not repeatedly launch new $2 runs without accounting for prior charges.

The job writes `/tmp/civic-enrichment-revised.log`. A follow-up inspection around **2026-10-29 02:15 UTC** found no active enrichment process: the log had stopped at 02:00:08 UTC, while run #5 still said `running` and its lease was expiring. The stored results remain available; do not assume the bulk run completed or launch a new budget without accounting for prior spend. Inspect Administration → AI issue enrichment or `GET /api/admin/enrichment` as an administrator. `EnrichmentRun`, `IssueEnrichment` and `JobLease` also record state. A lease alone can be stale after a crash; verify the process/log and timestamps.

The earlier restrictive run was deliberately stopped and marked `paused_for_comparison`. Its metadata is superseded by the revised prompt fingerprint; do not restart the old process/prompt.

Local database: `backend/civic-dev.db`. It contains public issues **and private accounts, password hashes, sessions, messages, activity and preferences**. It survives restarts but is not in Git. Never commit the live database to share issues.

## Runtime on this host

- Frontend LAN URL: `http://192.168.255.9:5173/` (address is host-specific).
- Frontend command from root: `npm run dev`; Vite binds `0.0.0.0:5173`.
- Backend binds `127.0.0.1:8000`; Vite proxies `/api` to it.
- Functioning local Python environment: `.local-tools/runtime-venv/`. The older `backend/.venv` was broken by a system Python change; do not assume it works on this host. Fresh teammates should create a normal new environment using the README.
- Start backend from `backend/`: `../.local-tools/runtime-venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app`.
- Keep reload/watch scope narrow. Watching the large local tool environments previously caused ENOSPC watcher errors; Vite ignores those directories.
- Health: backend `/health` and `/health/db`.
- Existing demo account passwords are in ignored `presentation-cheat-sheets/DEMO_CREDENTIALS.md`; do not copy them into committed docs. Fresh bootstrap generates new passwords and preserves existing accounts.
- `.env` has operator keys for GitHub/OpenRouter. Verify configuration by presence or safe API status only; do not print keys.

## Implementation map

The files below, which were pending at the original handoff, are now included in the local implementation commits. Run `git status --short` to identify any subsequent work.

| Area | Working-tree files |
|---|---|
| AI extraction, budgeted concurrent processing, cache | `backend/app/enrichment.py` |
| Production prompt/schema | `backend/app/enrichment_prompt.py` |
| Experimental comparisons | `backend/app/enrichment_prompt_trial.py`, `backend/app/enrichment_trial.py` (see note below) |
| Additive AI cache/run tables | `backend/app/store.py` |
| Fixed-scale scoring and metadata projection/filtering | `backend/app/matching.py`, `views.py`, `discovery.py` |
| Administrator AI progress | `backend/app/source_api.py`, `src/pages/SourceControls.jsx` |
| AI inference/rationale display and curator evidence | `src/pages/Home.jsx`, `src/pages/Maintainer.jsx` |
| Contribution removal | `backend/app/contributions.py`, `src/pages/Participation.jsx` |
| Regression coverage | new `backend/tests/test_enrichment.py`, `test_contribution_removal.py`; modified `test_github_scope.py`, `e2e/prepare.py`, `e2e/civic.spec.js` |
| Optional key example | `backend/.env.example` |

Comparison outputs live in ignored `.local-tools/enrichment-comparison.json` and `enrichment-prompt-comparison*.json`. They are development samples, not independent accuracy benchmarks. `enrichment_trial.py` is an older experimental comparison against the old response schema; production `extract()` has since changed schema, so do not use its original strict/unchecked counts on fresh responses without updating that tool. The production CLI is `python -m app.enrichment`.

## Current matching behavior

Production scoring is **`evidence-v4`**, not the earlier renormalized model that made a whole page look 100% matched. See [AI_MATCHING.md](AI_MATCHING.md) for the exact formula.

For Andre-test1, profile skills are JavaScript/HTML/CSS/documentation, interest civic participation, beginner experience/preference, five hours/week, Hack for LA preference. After the fixed-scale change, an observed first page contained eight 95% and four 80% matches; later results included 75/65/60. These ranks change as enrichment proceeds. Equal evidence may legitimately tie; do not invent precision to force a different number for every issue.

## Last observed verification

- **71 backend tests passed**, 5 PostgreSQL-only legacy tests skipped.
- **12 Chromium browser tests passed**, across wide/desktop/mobile widths, including contribution deletion and AI-inferred badges.
- Production build, Ruff and `git diff --check` passed.
- Clean earlier dependency baseline pins Vite 6.4.5 and had zero npm audit findings. Do not conflate the separately committed coding-tool package additions with that audited baseline.
- Formal load, WCAG/cross-browser, usability, PostgreSQL and AI-recommendation accuracy acceptance remains unverified. Tests above do not establish all SRS quality targets.

On this host, from root:

```bash
.local-tools/runtime-venv/bin/python -m pytest backend/tests -q
.local-tools/runtime-venv/bin/ruff check backend/app backend/tests
npm run build
E2E_PYTHON=.local-tools/runtime-venv/bin/python PLAYWRIGHT_BROWSERS_PATH=/tmp/civic-playwright npm run test:e2e
```

Browser fixtures reset only `.e2e/civic.db`; do not point them at the real database.

## Next work: teammate-ready public data distribution

This is **not implemented yet**. No seed/snapshot export/import command exists and no downloaded data is committed. A clone currently receives code/docs, not this host's 21,558 records or AI cache.

Recommended next implementation:

1. Build an explicit public-only export containing source configuration, issue content/original GitHub identifiers, source metadata and AI cache/provenance. Include schema/prompt versions and creation time/checksum.
2. Exclude every account/session/message/notification/bookmark/contribution/feedback/preference/auth/audit/private-backup record and all tokens. If including curator metadata, export only deliberately public annotation fields, not private user references.
3. Provide a small versioned compressed public snapshot or sanitized seed plus an import command. A sanitized seed SQLite file is acceptable; a compressed JSON snapshot can make schema evolution and inspection easier. Do not ship the live DB.
4. Make fresh setup load the supplied data before launching, create new local demo accounts, and work without API keys. Provide an offline mode (`ENABLE_WORKER=false`) so the first run does not immediately refresh sources and invalidate caches.
5. For existing databases, preserve private data. Use stable upstream source/issue identifiers and explicit ID mapping; never overwrite task IDs that private rows reference, or replace a teammate's whole working database to refresh public data.
6. Include the final current AI metadata and its exact project context in the snapshot so hashes remain valid and teammates do not re-enrich unnecessarily. Preserve source authority/freshness.
7. Add documented macOS/Windows/Linux commands and test a clean installation/restore with no API keys, then repeat import to establish idempotence and private-data preservation.
8. Review any new implementation and prepare local commits. Do not push or merge until explicitly authorized.

Two separate public/private runtime databases were discussed as a longer-term design, but **no split has been implemented**. Do not assume cross-database relationships already exist. Prefer completing a safe, simple teammate handoff before undertaking a broader database redesign.
