# Developer handoff

Updated November 15, 2026. Work is on `feat/context-search-review`; inspect Git
status before changing or committing anything. Preserve the current account,
source and contribution data. Historical office documents remain unchanged.

## Current product

Read [scope](PROJECT_SCOPE.md), [README](../README.md), [matching](AI_MATCHING.md)
and [requirements status](REQUIREMENTS_STATUS.md). The local GitHub-based app has
Contributor, Curator and Administrator workspaces, scoped corrections, private
bookmarks/tracking, messages/notifications, export/deletion and source management.
GitHub remains authoritative; local tracking never assigns or closes an issue.

Main Discover integrates the former trial's context and skill-discovery features:
20 saved research examples keyed by URL and unchanged source text, visible inferred
skills with reasons/quotes, suggested-skill search controls, synonym-aware search,
explained relevance ordering, and saved-profile match explanations. Other issues
use current AI caches. Skills/interests-v5 uses 80/20 when both are available,
normalizes missing factors, and discounts inferred skills within skill alignment.
Review limitations belong in evidence details, not contributor task guidance.
The standalone trial retains its frozen examples and temporary profile for comparison.

## Data and inference

The public bundle contains 21,558 GitHub issues, 3,539 open. Every open issue has
a current result: 2,389 accepted interpretations and 1,150 validation rejections.
The November 15 update completed with zero pending issues and approximately $3.10
recorded estimated spending; a few interrupted in-flight requests may add charges.
Do not automatically repeat paid inference. Source/version/context changes can
invalidate caches; empty/rejected results are cached too.

`python -m app.snapshot setup` restores public data and generates local account
passwords. Import preserves existing private data. Export uses public allowlists;
never distribute `backend/civic-dev.db`, `.env`, backups or credential notes.
`data/discovery-reviews.json` holds the saved project research separately.

## Runtime on this host

- LAN URL: `http://192.168.255.9:5173/`; host-specific, not a portable deployment URL.
- Frontend: `npm run dev`, listening on all interfaces and proxying `/api`.
- Backend: loopback port 8000, `ENABLE_WORKER=false` to preserve the offline cache.
- Network browser origins must be explicitly included in `APP_ORIGIN`.
- The old virtual environment's Python symlink no longer matches its libraries.
  On this host use Python 3.11 with `PYTHONPATH=.venv/lib/python3.11/site-packages`
  from `backend/`. Fresh installations should create a new normal environment.
- Demo account passwords were reset in chat; older ignored credential notes may
  be stale. Passwords are not recoverable from stored hashes. Do not commit them.

## Verification and remaining acceptance

Use [implementation review](IMPLEMENTATION_REVIEW.md) for current verification
and explicit boundaries. Run backend tests with `python -m pytest`, frontend build
with `npm run build`, and browser workflows with `npm run test:e2e` (isolated
`.e2e/civic.db`, never the live database). Local SQLite delivery is the selected
baseline; PostgreSQL-only tests need a dedicated test database.

Functional automation does not certify the 30-minute/100-user load targets,
500-session target, 50-source/100k-record scan target, full WCAG/cross-browser
coverage, five-person first-time usability or human assessment of AI accuracy.
Record measurements honestly. No public deployment, email or GitHub write-back
is required by the selected delivery boundary. Do not push or merge unreviewed
working changes as though previous authorization for a different change applies.
