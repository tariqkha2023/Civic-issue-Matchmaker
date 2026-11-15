# Local implementation review

**Group 26 — October 28, 2026**

The GitHub-based functional implementation is prepared on `feat/github-issue-transition`. Nothing in this review authorizes a push or merge. Team-attributed commit authors reflect WBS responsibilities, not independent evidence of original authorship.

## Implemented behavior

- Five real GitHub projects; all issue states, labels, original issue numbers and assignment metadata. PRs are excluded.
- Resumable staged scans, full and incremental reconciliation, safe pagination, bounded request retries, quota pauses, hourly scheduling and diagnostics.
- Contributor/Curator/Administrator interfaces, explained matching with metadata coverage, project directory, filters, bookmarks, nonexclusive contribution activity and relevance feedback.
- Cached public-issue AI enrichment with evidence quotations, content/version invalidation, provider price ceilings, concurrent request budget reservations, rejection caching and administrator progress. Stated/inferred skills have rationales; inferred skills count at half weight and curator corrections take priority. No AI calls on browse; no private profile/account data sent.
- Evidence-v4 fit requires issue-specific skills; weights are skills 60%, difficulty 20%, interests 15%, explicit effort 5%. Repository preference and own feedback/completion affect ties only.
- Curator annotation rationales, source preservation, stale-review flags, reset controls and audit history.
- Tariq's messages and notifications integrated with participant privacy, preferences, deduplicated match digests and event delivery records.
- Account export, reauthenticated deletion/anonymization, session safeguards, additive legacy migration and daily SQLite backups.
- Local setup, source access, backup restoration and scope applicability documented in the README and requirements record.

## Observed checks

- 78 backend tests passed, including seven public snapshot tests; 5 PostgreSQL-only legacy tests skipped without an explicit test database.
- 12 Chromium browser workflows passed across 1920, 1440 and 360-pixel widths.
- Production frontend build, Ruff and source whitespace checks passed.
- Existing local data upgraded after a consistent backup: four accounts and 19 published legacy issues retained.
- All five initial GitHub imports completed: 21,558 published issues. Open issues are being enriched with cached DeepSeek V3.2 suggestions labeled stated/inferred through OpenRouter under an explicit processing budget.

## Teammate distribution status

The public issue/AI snapshot and safe restore command are implemented in `app.snapshot`. The bundle includes 21,558 public GitHub issues and 2,220 valid cached AI enhancements. Fresh setup uses SQLite with scanning disabled and restores the bundle before creating new local demo accounts; no operator keys or repeated computation are needed. The live private development database remains ignored. See [developer handoff](DEVELOPER_HANDOFF.md), [team setup](TEAM_SETUP.md) and [snapshot format](../data/README.md).

### Teammate handoff verification — October 29, 2026 UTC

- A clean temporary repository export received a fresh isolated Python dependency
  installation and `npm ci`; the clean production build passed. This Linux host
  lacks `ensurepip`, so its isolated environment was created with `--without-pip`
  and populated using system `pip --python`. Normal teammate commands require
  the platform's venv support, as noted in the README.
- Setup with both operator keys absent restored 21,558 issues (3,539 open),
  2,220 valid AI caches, including 2,028 skill-bearing results, and generated
  three new local accounts. No operator accounts or processing-job state arrived.
- Login, project counts, recommendations and AI evidence were exercised against
  the restored real bundle; external HTTP transport was blocked during API checks.
- Two repeat imports preserved all private tables, including the new local
  bookmark/contribution and password/session records. Contribution removal and
  retracking, backend restart, administrator cache status, and repeat setup
  preserving existing passwords passed.
- A direct public-payload check found none of this host's local account emails,
  password hashes, session hashes or configured operator API keys in the bundle.

## Required acceptance work still outstanding

The implementation is functionally reviewable, but it is not yet formally accepted against every SRS quality target. The following remain unverified and must not be described as passed:

- Thirty-minute, 100-user latency targets; 500-session verification; 50-source/100k-record scan scale.
- Full applicable WCAG AA and current/previous cross-browser compatibility review.
- Five-participant first-time-user usability trial.
- Full PostgreSQL verification when using that database instead of the local SQLite delivery.
- Formal human assessment of AI-extracted requirement accuracy and recommendation usefulness.

These are not silently marked N/A. Public hosting, write-back/OAuth and email are excluded by the agreed delivery scope. See [requirements status](REQUIREMENTS_STATUS.md) for each applicable or superseded requirement.

## Review path

1. Start with [master scope](PROJECT_SCOPE.md) and [README](../README.md).
2. Use the local bootstrap accounts with the passwords saved on this machine; fresh installations generate different passwords.
3. Inspect Projects for initial scan completeness before expecting real issue results.
4. Exercise Discover → source issue → save/track → contribution states → feedback.
5. Exercise curator corrections and administrator source/role controls.
6. Inspect privacy export/preferences/deletion using a disposable account.
7. Review commit attribution and changes, then explicitly approve any push.

Preexisting local `package.json`/lockfile changes adding a coding-tool dependency are intentionally excluded from this implementation's commits. Private presentation files, databases, credentials and backups remain ignored.

The committed dependency baseline was also installed and built in a clean temporary export. Vite is pinned to 6.4.5; that clean install reported zero npm audit vulnerabilities. Private-source rejection and safe repository-rename redirects have additional regression coverage.

## Integrated local release checks — November 15, 2026

The main app now combines the context/skill discovery trial with authenticated
profiles, the full current AI cache, saving/tracking and curator permissions.
Contributor task guidance excludes internal review methodology. Those limitations
remain available in evidence details. Empty fallback sections are omitted.
Profile and sign-in copy now accurately describe skills/interests matching.

Observed verification for this revision:

- 94 backend tests passed; five legacy PostgreSQL tests remain skipped for the
  selected SQLite delivery. One test verifies 500 active identities under 32
  parallel authenticated reads with no identity mixups or lost sessions.
- 45 browser checks passed across Chromium at 1920/1440/360-pixel widths, Firefox
  and WebKit (27 Chromium and 18 Firefox/WebKit checks in the final runs).
- Automated WCAG A/AA checks cover account forms and main contributor workspaces
  in all five browser configurations. Low-contrast labels found by the scan were
  corrected. This is automated coverage, not a full manual accessibility audit.
- Production build, frontend search/matching unit tests, Ruff and whitespace
  checks passed. The dependency installation audit reported zero vulnerabilities.
- A fresh isolated offline import restored all 21,558 issues and all 3,539 current
  caches, with no external requests. Repeat import preserved local accounts and
  passwords. Public bundle checks found no live account emails, password hashes
  or configured operator keys. The bundle contains 2,389 accepted interpretations
  and 1,150 cached validation rejections; accepted does not mean independently
  verified for accuracy.
- LAN login and real issue #8695 were checked through the running Vite proxy.
  The real-data search took about 1.05 seconds on this host in that smoke check;
  this is not the formal concurrent-load measurement.

The local app remains on `http://192.168.255.9:5173/` on this host. The backend is
loopback-only and allows that browser origin. Existing private data was preserved.
The refreshed public bundle and review data are ready for teammate distribution.

### Remaining formal acceptance

Do not mark the whole SRS 100% accepted from these results. The remaining work is:

1. Record the 30-minute, 100-active-user latency test and 50-source/100k-record
   scan measurement. The 500-session identity probe above is a narrower test.
2. Complete a manual keyboard/screen-reader/WCAG review and target-browser/version
   coverage beyond the recorded Playwright engines.
3. Run the five-participant first-use study below and assess AI extraction and
   recommendation usefulness against a human-reviewed sample.
4. Run PostgreSQL-specific checks if PostgreSQL becomes the selected runtime.

### First-use study ready to run

Give five representative participants the app URL and ask them, without coaching,
to create an account, enter their skills/interests, find a task and open its GitHub
posting. Time each attempt from arrival until the GitHub page opens. Record an
anonymous participant ID, elapsed seconds, success/failure, assistance required
and confusing steps. The stated target is at least four of five completing within
five minutes without assistance. Record actual observations; no study has yet
been performed. Separately ask reviewers to compare suggested skills, summary and
task questions with each original posting and record unsupported claims and gaps.
