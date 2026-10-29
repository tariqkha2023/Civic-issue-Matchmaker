# Requirements applicability and verification

**Group 26 — October 28, 2026.** Applies the SRS/SDD to the agreed GitHub-based scope. Local delivery, read-only GitHub and in-app notifications are the selected boundaries. This is an acceptance record, not a blanket claim that all quality targets passed.

## Governing decisions

- [Master scope](PROJECT_SCOPE.md) defines contributors, curators, all-issue ingestion and nonexclusive personal contribution tracking.
- GitHub remains authoritative for issue state, assignment and contribution acceptance. Local completion is self-reported.
- Email delivery, GitHub OAuth/write-back and public cloud hosting are N/A for this delivery. In-app notification preferences/delivery records remain applicable.
- Exclusive claims and hiding an issue because another app user tracks it are superseded. Legacy data and fixture behavior are retained separately.
- Repository curator scope replaces claims of verified external maintainer identity. Application administrators assign curator access; they cannot grant authority over GitHub.

## Functional requirements

| SRS | Applicability and implementation |
|---|---|
| FR-1–FR-3 | Email/password accounts, sessions and technical/civic profiles implemented; external identity login is an alternative, not required. |
| FR-4–FR-5 | Implemented as additive contributor/curator/admin roles with backend repository scope. Curator authorization is application-scoped. |
| FR-6 | Reauthenticated immediate anonymization and personal-data removal; source records/sanitized audit references retained. |
| FR-7 | Hourly/configurable scheduled GitHub scanning with resumable staging, quota pauses and recorded attempts. GitHub-imposed delays are explicit, not claimed as an hourly full scan. |
| FR-8 | Revised: ingest all issue labels/states from configured repositories. Open/assignment/topic filters operate after ingestion. |
| FR-9 | Canonical content/source identity, labels, unknown-aware derived metadata, original issue numbers/assignees/timestamps and curator overlays. |
| FR-10 | Revised: GitHub open/closed and assignment remain separate from local tracking. Missing/inaccessible records are not assumed closed. |
| FR-11 | Staged pages do not replace a published snapshot until complete; failure retains cache and progress. |
| FR-12–FR-13 | Scoped metadata corrections, rationale, source-change review flag, override reset and audited before/after. |
| FR-14–FR-19 | Explainable weighted matching, ordering, filters and metadata coverage. Missing issue-specific skills produces Limited information rather than a fabricated percentage. Evidence-v4 weights and AI provenance are documented in the scope and README. |
| FR-20 | Closed issues excluded by default. Exclusion based on another user's local claim is N/A; upstream assignment is shown/filterable. |
| FR-21 | Revised to Interested/In progress/Submitted/Completed/Withdrawn personal activity. Saved bookmarks remain separate. |
| FR-22 | N/A for external issues: several contributors can track one issue; there is no local reservation of GitHub work. |
| FR-23 | Activity event history, saved/unsaved bookmark history and earlier migrated participation events retained. Bookmark actions stay distinct from contribution state. |
| FR-24–FR-25 | Own relevance feedback/explanation and completed activity break equal-fit ties without altering technical fit. Cached LLM extraction analyzes public issues only; no training or external profile inference. |
| FR-26 | Authoritative GitHub links and project contribution entry points. |
| FR-27–FR-28 | In-app new-match preferences/threshold and per-scan digests created at successful publication. Very large scans remain quota-dependent. |
| FR-29 | N/A as written: curators are not external repository maintainers and local tracking is not an upstream claim. |
| FR-30–FR-31 | Private read/unread controls, mark-all-read and deduplicated delivered/suppressed event records. Email channels are N/A. |

## Constraints and operational requirements

| SRS | Implementation or verification boundary |
|---|---|
| DC-1–DC-5 | Configured public GitHub read APIs, stable source IDs, no credentials in output, server RBAC, separate correction overlays. A project listing is not endorsement. |
| RA-1 | Production monthly availability is N/A to a local app; no measured uptime claim. |
| RA-2–RA-4 | Cached snapshots/freshness retained across expected source failures. Resumable staging and transactional publication are tested. |
| RA-5 | Daily local SQLite backups with seven-day rotation; a backup content/recovery test exists. PostgreSQL backup operations are not provided by the local worker. |
| SP-1 | Salted scrypt hashes. SDD permits a slow salted algorithm; WBS's specific bcrypt/Argon2 names are an implementation difference. |
| SP-2 | Current-password reauthentication for deletion. No credential-change screen is exposed. |
| SP-3–SP-4 | Own profile/history/feedback/notifications and participant-only messages; curator access is metadata-only. Authorized admins list account data for role management, not all conversations. |
| SP-5 | 30-minute idle expiry and explicit logout. |
| SP-6 | Auth attempt records, privileged-operation audit, correction/source audit and rejected authenticated write authorization audit. Cross-site writes are rejected before mutation. |
| SP-7 | Live personal data removed/anonymized immediately; sanitized audit references retained; local rotating backups expire within seven days. |
| US-1 | Requires a real trial with five representative users. Not fulfilled by browser automation; team must record results. |
| US-2–US-4 | Forms, validation/state preservation, loading/empty/freshness indicators and semantic keyboard controls implemented; browser workflows check representative paths, not a full accessibility audit. |
| MP-1–MP-2 | Admin source configuration/disablement without redeploy, scan diagnostics and sanitized records. |
| MP-3 | Automated Chromium desktop/mobile checks; formal current/previous Firefox/Edge/Safari compatibility remains unverified. |
| MP-4 | Matching stays in its own service independently of source adapters. |
| OR-1 | Accessibility baseline implemented; full applicable WCAG AA audit remains unverified. |
| OR-2 | Registration privacy notice and account deletion/export disclosures. |
| OR-3 | Downloadable account JSON including profile, history, feedback, bookmarks, messages and notifications; password/session secrets excluded. |
| OR-4–OR-5 | Source/project contribution links, source-authority and acceptance disclaimers. |

## Performance acceptance

PR-1–PR-5 retain their original targets. Functional tests do not prove the 30-minute/100-user latency targets, 500 active sessions, 50-source/100k-record scan scale or source-dependent scan timing. A public GitHub token is recommended for large initial scans, but token configuration alone does not prove those targets.

These are verification work, not automatic N/A exclusions. Do not present the project as formally accepted against every SRS quality attribute without recording these measurements and representative-user/accessibility results.

## Verification record

- Backend regression suite: 78 passed, including seven public snapshot tests; five PostgreSQL-only legacy tests skipped locally without a test database.
- All 12 Chromium browser workflows passed across desktop/mobile widths; production build and Ruff passed.
- New tests cover all-state paginated ingestion, PR exclusion, resumable quota failures, snapshot/source preservation, curator review flags, nonexclusive tracking, evidence/state validation, personal feedback, export/deletion and backup data recovery.
- Existing tests retain authentication/profile/role/messaging coverage and explicit legacy fixture behavior. Local fixture creation requires `APP_DEMO=true`; it is disabled by default.
- Formal course usability, full browser/accessibility certification and production availability are not claimed.

## Live upgrade smoke check

The existing SQLite database was consistently backed up before migration. All four existing accounts and 19 published legacy issues were preserved. A real read-only HOT Tasking Manager request successfully staged its first tracker page, and the worker subsequently advanced multiple pages for all five configured sources. Repository-ID pagination was verified live and added to regression coverage. These are connectivity/staging checks, not evidence that all five trackers completed indexing. The worker continues resumable scans subject to GitHub quotas.

The committed dependency baseline was also installed and built in a clean temporary export. Vite is pinned to 6.4.5; that clean install reported zero npm audit vulnerabilities. Private-source rejection and safe repository-rename redirects have additional regression coverage.
