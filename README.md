# Civic Issue Matchmaker

Group 26's application matches technical contributors with GitHub issues from civic-tech projects. GitHub is read-only and remains authoritative. The application provides profiles, explained recommendations, private bookmarks and contribution tracking, curator metadata reviews, messages, in-app notifications and source administration.

[Master scope](docs/PROJECT_SCOPE.md) · [Requirements and verification](docs/REQUIREMENTS_STATUS.md) · [Team setup/data sharing](docs/TEAM_SETUP.md) · [Developer/LLM handoff](docs/DEVELOPER_HANDOFF.md) · [AI and matching](docs/AI_MATCHING.md)

> **Teammate-ready data:** this branch includes **21,558 public GitHub issues and 2,220 cached AI enhancements** in [`data/public-issues-v1.json.gz`](data/README.md) (about 9.3 MiB). The setup command below restores them into your own local database. No GitHub/OpenRouter keys, tracker downloads or repeated AI computation are needed. Accounts and private activity are not bundled.

## Quick local setup

Requires Python 3.11+ and Node.js 18+ with npm (Node 22 recommended). The local release uses SQLite; no Docker, paid AI service, GitHub OAuth or email provider is needed.

### macOS and Linux

From the project root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
npm ci
cp backend/.env.example backend/.env
```

Linux may require the distribution's `python3-venv` package. Reuse an existing `.env` rather than overwriting it.

### Windows PowerShell

```powershell
py -3 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
npm ci
Copy-Item backend/.env.example backend/.env
```

Use `python` instead of `py -3` if the launcher is unavailable. Use `npm.cmd` if PowerShell blocks `npm.ps1`. These commands use the environment directly; activation is unnecessary.

### Configure SQLite and offline mode

In `backend/.env`, set:

```env
DATABASE_URL=sqlite:///./civic-dev.db
APP_ORIGIN=http://localhost:5173,http://127.0.0.1:5173
COOKIE_SECURE=false
ENABLE_WORKER=false
APP_DEMO=false
BACKUP_DIR=./backups
```

These are the defaults in `.env.example`. Leave both `GITHUB_TOKEN` and `OPENROUTER_API_KEY` absent for teammate setup. `ENABLE_WORKER=false` keeps the imported public snapshot unchanged on first launch; profiles, discovery, matching, bookmarks, contributions, curator reviews and messages still work locally.

To deliberately refresh sources later, set `ENABLE_WORKER=true` and optionally provide your own public-read `GITHUB_TOKEN`. Large tracker indexing is quota-dependent: scans stage pages, pause on limits and resume without losing progress. Source content or project context changes may invalidate affected AI caches; refreshing GitHub never launches paid enrichment automatically.

### Restore the bundled data, create local accounts and start the backend

From `backend`, macOS/Linux:

```bash
.venv/bin/python -m app.snapshot setup
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m app.snapshot setup
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`app.snapshot setup` validates and imports the included public issues and AI cache, then bootstraps these local accounts, printing a randomly generated password for each new account:

| Account | Role |
|---|---|
| `volunteer@civic.demo` | Contributor |
| `maintainer@civic.demo` | Curator for the configured sources |
| `administrator@civic.demo` | Administrator |

The email names remain compatible with the earlier demo; the user-facing roles are Contributor and Curator. Existing passwords/profiles are preserved. Rerunning setup does not print or reset old passwords. Store new passwords when printed. Public signup creates contributors only. Issues with no cached AI requirements remain source-derived or Limited information; setup does not spend credits to fill those gaps.

### Start the frontend

In a second terminal at the project root:

```bash
npm run dev
```

Open **http://localhost:5173**. Keep both terminals running. Ports 5173 and 8000 must be available. Vite proxies `/api` to the backend. Health checks: http://127.0.0.1:8000/health and `/health/db`; API reference: `/docs`.

Later launches require only the two server commands. The database persists at `backend/civic-dev.db`. Startup applies additive migrations and retains earlier data. Original claim/event records remain; migrated contributions explicitly identify legacy local events.

### Update an existing local installation

Stop its backend/worker, retain `ENABLE_WORKER=false`, and run from `backend/`:

```bash
python -m app.snapshot import
```

Use the same virtual-environment interpreter paths shown above if it is not activated. Imports map stable GitHub repository/issue identities to local IDs rather than replacing the database. Existing accounts, sessions, private activity, bookmarks and curator overrides remain; repeated imports do not duplicate issues. Newer local source content and existing complete-source project settings take priority. Incompatible caches are skipped rather than rewritten to match a different context. See [data format and export commands](data/README.md).

For LAN access, add `http://YOUR_LAN_IP:5173` to `APP_ORIGIN` and restart the backend. Open that address from a reachable device and allow frontend traffic through the host firewall. Vite already binds to the LAN; the backend can stay on localhost.

## Real source projects

- [FixMyStreet](https://github.com/mysociety/fixmystreet): public infrastructure reporting.
- [HOT Tasking Manager](https://github.com/hotosm/tasking-manager): humanitarian mapping.
- [OpenStreetMap iD](https://github.com/openstreetmap/iD): open geographic data.
- [Open Food Facts](https://github.com/openfoodfacts/openfoodfacts-server): food transparency.
- [Hack for LA website](https://github.com/hackforla/website): civic participation.

Every source's entire issue tracker is eligible for ingestion, including closed issues. Pull requests are excluded. There is no `help wanted`/beginner label whitelist. Default discovery shows open issues; source assignment is displayed and filterable. Project listing does not imply affiliation or maintainer endorsement.

## Workflows

1. **Contributor:** set technical skills, civic interests, experience and weekly hours; explore Projects and Discover; inspect score explanations, metadata coverage, source freshness and original GitHub issue details.
2. **Bookmark or track:** save privately or Track contribution → Start work → Add submission → Mark contribution complete. Stop tracking withdraws activity. Remove contribution → Confirm removal deletes your local entry and its history in any state, including completed; the source issue and other contributors remain unchanged. You can track the issue again afterward.
3. **Source authority:** multiple users can track one issue. Local tracking does not assign, reserve or close it on GitHub. Follow each source's contribution process. Completion is explicitly self-reported; a linked PR is not automatically verified as accepted.
4. **Feedback:** rate an issue Relevant/Not relevant and optionally explain. Your feedback, completion history and repository preferences help break equal-fit ties; they do not inflate assessed technical fit.
5. **Curator:** Review metadata → search a source issue → inspect source → correct skills/topics/difficulty/hours and add a rationale. Corrections remain separate; source changes flag them for re-review. Reset override restores source-derived values.
6. **Administrator:** assign roles/repository scopes, add GitHub sources, configure scan intervals/topics/mission, queue/resume scans, toggle source enablement and inspect scans/audits.
7. **Messages and notifications:** coordinate through permitted private conversations, read task/account notifications and scan match digests; manage preferences in Account settings.
8. **Privacy:** export your personal data as JSON or reauthenticate to delete/anonymize your account. The last administrator must appoint another before deletion. Personal messages involving a deleted account are removed; shared source issues and sanitized audit references remain.

## Matching

The versioned `evidence-v4` model uses skills 60%, difficulty/experience 20%, civic interests 15%, and explicit availability/effort 5%. Scores use a fixed 100-point denominator: matching known factors earn points; missing factors remain unknown and do not inflate the remaining factors to 100%. A percentage requires both issue-specific skills and profile skills; topic/repository preference alone produces **Limited information**. Repository preference, own relevance feedback and completion history break equal-fit ties without changing the percentage. AI-inferred skills carry half the evidence weight of stated or curator-reviewed skills, both within skill alignment and in the overall skill factor. Evidence coverage discounts inferred evidence too. Evidence coverage is separate: a high score with partial coverage is not a guarantee of suitability. Source labels, AI suggestions labeled stated/inferred, and curator corrections supply requirements, with curator corrections taking precedence. Project languages remain contextual hints. Location is not scored.

GitHub bodies are displayed as plain text rather than executing imported HTML. Unknown estimates remain unknown. Compatibility is guidance, not probability of acceptance.

## Scheduler and backups

The backend starts a worker unless `ENABLE_WORKER=false`. It checks due sources every 15 seconds, stages five pages per scan attempt, resumes unfinished scans, scans normally at hourly/configured intervals and performs a weekly full reconciliation. Incremental scans use overlapping update timestamps; failed scans do not publish partial changes or infer closure. Missing records in a full scan are marked unavailable, not silently closed.

A one-pass worker can be run from `backend` with the environment active:

```bash
python -m app.worker --once
```

The older `app.manage`/`app.ingestion` commands are retained for legacy fixtures; use the worker and Administration for real GitHub synchronization.

The worker creates a consistent SQLite backup daily and retains seven dated backups under `BACKUP_DIR`. These contain private data and are gitignored. To restore locally, stop both backend and any separate workers, preserve the current database, copy the selected backup over `backend/civic-dev.db`, then restart. Test recovery using a separate copy first. Seven-day backup rotation bounds retention of data removed from the live database. PostgreSQL deployments require their own database backup/restore procedure; automated backups in this local release are SQLite-specific.

## Verify

With the backend environment active, from the project root:

```bash
python -m pytest backend/tests -q
ruff check backend
npm run build
npx playwright install chromium
npm run test:e2e
```

`E2E_PYTHON` can select another Python interpreter path. Browser fixtures are guarded to reset only `.e2e/civic.db`; the fixture server disables live scans. They use representative GitHub-shaped data, not a claim that the five trackers were fully downloaded. Active browser tests are `e2e/civic.spec.js`; older presentation scripts are retained as historical tests and are not selected.

Backend tests use isolated SQLite or, with `TEST_DATABASE_URL`, separate PostgreSQL schemas. PostgreSQL-only legacy tests skip without that explicit test database. Never point testing commands at your live demo database.

See [requirements status](docs/REQUIREMENTS_STATUS.md) for applicable/N/A requirements, observed verification and outstanding formal quality checks.

## Delivery boundary

This is a locally runnable application with setup and operations instructions. Public hosting, GitHub OAuth/write-back and email delivery are excluded by the agreed delivery choices. GitLab adapter code is retained as groundwork; GitHub is the required source provider. Formal course usability testing and production availability cannot be asserted from automated local tests.

Historical DOCX/PDF references live unchanged in `docs/artifcats/`. Maintained Markdown documents and the master scope govern the transition. The original physical-volunteering examples are isolated fixtures, not real GitHub data or current project opportunities.

### Optional AI enrichment of public issues

Set `OPENROUTER_API_KEY` in `backend/.env` (never commit the key). Run from `backend/`, with the backend environment activated:

```bash
python -m app.enrichment --limit 50 --budget 0.05
```

The model is `deepseek/deepseek-v3.2` through OpenRouter. The revised `minimal-requirements-v2` prompt uses public project technology context and separates stated from inferred requirements. Each run processes only enabled projects' open issues, interleaves projects, uses up to four requests concurrently by default (`--workers 1..8`), and reserves conservative request costs before submission. Provider price ceilings are $0.35/million input and $0.60/million output tokens; a run stops on provider errors or when the next request cannot fit its budget. `--budget` accepts at most $2 per invocation. Also set an account/key spending limit in OpenRouter: the application budget is a conservative estimate, not a billing guarantee.

Only public issue titles, descriptions, labels and curated public project context (mission/topics/languages) are sent—not accounts, profiles, messages or passwords. Issue text is untrusted input. The model identifies the smallest defensible skill set, labels each skill explicit or inferred, and explains why it matters. Inferences do not need literal technology mentions or quotes. Basic JSON/schema validation remains; no keyword filter removes inferred skills. A claimed explicit requirement without a matching source quote is retained as inferred. Quotations and model labels are not proof of correctness. Curators can override suggestions; difficulty is requested only when explicitly supported and AI never estimates effort. The first 14,000 characters of each issue are analyzed, so long issues may have incomplete coverage.

Results are cached in `issue_enrichments`; changed issue content, public project context, extraction version or model invalidates the cached suggestions. Curator overrides remain authoritative. Empty/unknown and validation-rejected results are cached too, avoiding repeated charges for unusable output. Re-running processes new or changed issues; provider failures remain retryable. The administrator page displays processing progress and the latest run's estimated spend; issue details and the curator editor show evidence quotations. Browsing makes **no AI calls** and works without an API key once data is enriched. New/changed issues need another explicit enrichment run; hourly GitHub synchronization does not spend AI credits automatically.
