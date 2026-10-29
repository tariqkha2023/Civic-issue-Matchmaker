# Developer and LLM handoff

Group 26 — Civic Issue Matchmaker. Recorded October 28, 2026 (US Eastern; October 29 UTC).

Read this first when continuing in this workspace. The described AI, matching and contribution-removal implementation is committed on `feat/github-issue-transition`. Public data distribution is now implemented with a bundled snapshot and `app.snapshot` export/import/setup commands.

## Immediate request and boundaries

The current request is teammate-ready local setup distributing imported public GitHub issues **and cached AI enhancements**, so teammates do not repeat downloads or pay for enrichment again. The public-only bundle and safe import/setup commands are implemented. Formal quality acceptance work is deferred at the user's request; do not restart paid enrichment as part of this delivery.

- Repository: `/home/walia6/repos/Civic-issue-Matchmaker`.
- Working branch: `feat/github-issue-transition`. Local `main` has not been replaced by this work.
- The user authorized pushing the teammate-ready implementation and documentation branch. Merging or replacing `main` still requires explicit authorization.
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
| Public issue/cache snapshot export, import and setup | `backend/app/snapshot.py`, `backend/tests/test_snapshot.py`, `data/` |

Comparison outputs live in ignored `.local-tools/enrichment-comparison.json` and `enrichment-prompt-comparison*.json`. They are development samples, not independent accuracy benchmarks. `enrichment_trial.py` is an older experimental comparison against the old response schema; production `extract()` has since changed schema, so do not use its original strict/unchecked counts on fresh responses without updating that tool. The production CLI is `python -m app.enrichment`.

## Current matching behavior

Production scoring is **`evidence-v4`**, not the earlier renormalized model that made a whole page look 100% matched. See [AI_MATCHING.md](AI_MATCHING.md) for the exact formula.

For Andre-test1, profile skills are JavaScript/HTML/CSS/documentation, interest civic participation, beginner experience/preference, five hours/week, Hack for LA preference. After the fixed-scale change, an observed first page contained eight 95% and four 80% matches; later results included 75/65/60. These ranks change as enrichment proceeds. Equal evidence may legitimately tie; do not invent precision to force a different number for every issue.

## Last observed verification

- **78 backend tests passed**, 5 PostgreSQL-only legacy tests skipped, including seven public snapshot tests.
- **12 Chromium browser tests passed**, across wide/desktop/mobile widths, including contribution deletion and AI-inferred badges.
- Production build, Ruff and `git diff --check` passed.
- Clean temporary-checkout offline setup restored the full public bundle and all
  2,220 valid cache fingerprints. API checks, two repeat imports preserving all
  private tables, contribution removal/retracking, restart and repeat setup
  preserving passwords passed; see [implementation review](IMPLEMENTATION_REVIEW.md).
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

## Teammate-ready public data distribution

- `data/public-issues-v1.json.gz`: 21,558 public GitHub issues, 3,539 open, and 2,220 valid cached AI enhancements; about 9.3 MiB compressed. `data/public-issues-v1.manifest.json` records counts, generation time and checksums.
- `backend/app/snapshot.py` uses explicit public-field models, including nested source metadata and AI evidence allowlists. It exports no private tables or local curator overrides. The archive embeds schema/prompt versions, exact production prompt and payload checksum.
- From `backend/`, `python -m app.snapshot setup` restores the bundle and then creates fresh local demo accounts. `python -m app.snapshot import` refreshes public records in an existing installation without resetting accounts/passwords or replacing the database. `python -m app.snapshot export` regenerates the public bundle from the operator database.
- `.env.example` defaults to SQLite and `ENABLE_WORKER=false`. Setup, import and browsing make no source/AI API calls. The 1,319 open issues without cached enhancements remain source-derived or Limited information.
- Repository GitHub IDs and stable upstream issue IDs map to local primary keys; existing private references remain valid. Repeated imports do not duplicate issues. Import validates the entire archive before writes and commits public changes in one transaction. Newer local source content, existing complete-source project settings and newer caches take priority; incompatible caches are skipped.
- Source freshness, original GitHub issue numbers, labels and assignees remain distinct from local IDs and tracking. Exact issue/context fingerprints retain cached requirements without another paid extraction. Runtime job leases, staging and processing ledgers are not imported.
- [Team setup](TEAM_SETUP.md) provides platform-specific interpreter paths and a first-run checklist; [snapshot format](../data/README.md) documents data refresh.

The application still uses one local runtime database with public/private tables. No cross-database split has been implemented. Formal load, WCAG/cross-browser, usability, PostgreSQL and AI-accuracy acceptance remains deferred. Any resumption of the incomplete enrichment run is a separate request and must account for previous spending.
