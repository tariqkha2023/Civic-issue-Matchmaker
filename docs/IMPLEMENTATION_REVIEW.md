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

- 71 backend tests passed; 5 PostgreSQL-only legacy tests skipped without an explicit test database.
- 12 Chromium browser workflows passed across 1920, 1440 and 360-pixel widths.
- Production frontend build, Ruff and source whitespace checks passed.
- Existing local data upgraded after a consistent backup: four accounts and 19 published legacy issues retained.
- All five initial GitHub imports completed: 21,558 published issues. Open issues are being enriched with cached DeepSeek V3.2 suggestions labeled stated/inferred through OpenRouter under an explicit processing budget.

## Teammate distribution status

The public issue/AI snapshot and safe restore command are still pending. Data currently lives in the ignored private development database. Latest AI/scoring/removal code is now committed locally on `feat/github-issue-transition`. See [developer handoff](DEVELOPER_HANDOFF.md) and [team setup](TEAM_SETUP.md).

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
