# Civic Issue Matchmaker Master Project Scope

**Team:** Group 26

**Version:** 1.0

**Effective date:** October 28, 2026

**Status:** Target scope for the transition to real GitHub issue sources. This document defines intended behavior; it is not a claim that every function is implemented.

## 1. Product definition

Civic Issue Matchmaker helps people contribute technical skills to projects that serve the public. It aggregates GitHub issues from selected civic technology repositories, matches them to contributor profiles, explains the recommendations, and helps users track their contributions.

**Product statement:** A contributor can find a suitable software issue supporting a civic cause, understand why it fits, open the authoritative GitHub issue, and track their contribution without confusing local tracking with upstream project approval.

The civic purpose belongs to the project: public infrastructure reporting, humanitarian mapping, open geographic data, food transparency, and civic participation. The work items are literal GitHub issues, including bugs, features, documentation, testing, design, accessibility, and maintenance. Physical volunteering activities such as serving meals or repairing roads are outside this product's scope.

### Authority of this scope

This document is the controlling product-scope reference for the transition. Where the earlier Markdown SRS, SDD, WBS, architecture description, or README describes conflicting account terminology, fictional community activities, exclusive claims, or issue ownership, the definitions here take precedence for new work. The earlier documents remain supporting specifications to reconcile with this scope; their requirements are not automatically evidence of implementation.

DOCX/PDF files in `docs/artifcats/` are historical artifacts, not sources of truth, and remain unchanged. The WBS table remains a general team responsibility guide rather than an exact record of completed work. Changes to this scope require an explicit update to this document and corresponding acceptance criteria.

## 2. Users and intended outcomes

| User | Need | Intended outcome |
|---|---|---|
| New contributor | Find approachable work with a public-interest purpose | Understand the project, issue, relevant skills, and contribution process |
| Returning contributor | Reduce repeated searching across repositories | Receive current recommendations and maintain a personal contribution history |
| Curator | Improve incomplete or inconsistent issue classifications | Correct local metadata for assigned repositories without changing source content |
| Administrator | Operate a trustworthy collection of sources and accounts | Manage access, synchronization, failures, and audit activity |

The application does not guarantee that an issue is available, that its maintainers will accept a contribution, or that a compatibility score predicts acceptance.

## 3. Source projects and issue coverage

The initial production data set consists of these five GitHub repositories:

| Project | Repository | Civic subject |
|---|---|---|
| FixMyStreet | [mysociety/fixmystreet](https://github.com/mysociety/fixmystreet) | Reporting public infrastructure problems to authorities |
| HOT Tasking Manager | [hotosm/tasking-manager](https://github.com/hotosm/tasking-manager) | Humanitarian and community mapping coordination |
| OpenStreetMap iD | [openstreetmap/iD](https://github.com/openstreetmap/iD) | Editing community-maintained geographic data |
| Open Food Facts | [openfoodfacts/openfoodfacts-server](https://github.com/openfoodfacts/openfoodfacts-server) | Open food-product information and transparency |
| Hack for LA website | [hackforla/website](https://github.com/hackforla/website) | Civic technology projects and volunteer participation |

These projects are selected sources, not represented partners. Their maintainers retain their own onboarding, assignment, contribution, and review processes. An account in this application does not establish membership in any of these projects.

### Entire issue trackers are sources

- Ingest actual GitHub Issues across each selected repository, with pagination. Do not limit ingestion to handpicked issues or labels such as `good first issue` or `help wanted`.
- Initial source synchronization covers both open and closed issues. Closed issues support history and synchronization correctness; discovery defaults to open issues.
- GitHub's issues API can return pull requests. Exclude pull requests from the issue collection. Separately linked pull requests can support contribution records.
- Labels, assignees, issue type, age, or missing estimates do not exclude an issue from ingestion. User-selected filters and recommendation eligibility act on the imported collection afterward.
- A partial scan must be labeled incomplete. Never present a truncated page of results as the entire tracker.
- Repositories are selected by administrators. Contributors cannot turn an arbitrary URL into a fetch target.

## 4. Source authority and application authority

| Information or action | Authority |
|---|---|
| Issue title, body, state, labels, assignees, author, timestamps, URL | GitHub |
| Repository contribution instructions and official acceptance | The source project and its GitHub workflow |
| Contributor profile and preferences | The contributor, within application validation rules |
| Saved issues, local tracking states, feedback, messages | This application |
| Local skills, civic topics, difficulty and effort annotations | Derived classifications or explicitly recorded curator corrections |
| Application roles, source configuration and schedules | Application administrators |

Synchronization refreshes source facts. Curator annotations are separate overlays and never silently replace the retained source values. The UI labels source data, derived values, curator-reviewed values, and self-reported contribution claims distinctly.

Reading and indexing public issue data does not establish a relationship with the repository owner. GitHub remains the place to discuss issues, request assignment, submit pull requests, and obtain project acceptance.

## 5. Account roles and permissions

Three roles share one application. **Contributor** replaces Volunteer in product language. **Curator** replaces the current Maintainer role to avoid implying authority over external GitHub projects. Existing internal role names may remain during migration, but the user-facing meaning must follow this scope.

### Contributor

A contributor can register, sign in/out, manage their own profile, browse projects/issues, receive explained recommendations, save issues, track contributions, submit relevance feedback, use permitted messaging, manage notifications, export personal data, and request account deletion.

Public signup grants contributor access only. It cannot grant curator or administrator privileges.

### Curator

A curator has contributor capabilities plus permission to review and correct local issue metadata for explicitly assigned repositories. Correctable fields include technical skills, civic topics, difficulty, estimated effort, and a classification rationale.

A curator cannot change source issue content, state, labels, assignees, or GitHub permissions. A curator cannot administer application roles or source configuration. Curators are application metadata reviewers; verified GitHub maintainer identity is not required or implied.

### Administrator

An administrator has contributor capabilities, can curate all enabled sources, and can manage application roles, curator repository assignments, sources, synchronization schedules, operational status, and audit records. The last active administrator cannot be removed through ordinary role administration.

Administrator status is application authority only. It does not authorize actions inside external GitHub projects. Administrators access user information only for defined support/administration functions; private messages are not an administrator-wide inbox.

### Permission summary

| Capability | Contributor | Curator | Administrator |
|---|---|---|---|
| Discover issues and inspect projects | Yes | Yes | Yes |
| Edit own profile and personal tracking | Yes | Yes | Yes |
| Read another user's private history, feedback, or conversation | No | No | No routine access |
| Correct local metadata | No | Assigned repositories | All sources |
| Change GitHub issue data through this app | No | No | No |
| Assign application roles or repository access | No | No | Yes |
| Configure sources and scan schedules | No | No | Yes |
| Inspect administration audit and operational records | No | No | Yes |

Authentication and server-side permission checks apply to every protected request. Hiding navigation items is not an authorization mechanism. Export/deletion acts on the authenticated user's data and requires reauthentication where appropriate.

## 6. Required product functions

### Accounts and profiles

Profiles capture technical skills, experience, civic interests, preferred difficulty, weekly availability, and optional preferred repositories. They may include a GitHub username or profile URL as **self-reported** information. Linking a username is not proof of account ownership.

Support validation, persistence, session expiry after 30 minutes of inactivity, sign-out, machine-readable data export, and account deletion with documented retention/anonymization. Email addresses and profiles are not exposed as a public contributor directory.

### Project directory

Each project page shows the civic mission, repository link, relevant languages/technical areas, contribution instructions link, issue list, and source synchronization status. Project topics are curated and distinguish the public-interest domain from technical skills.

### Issue discovery

Import and display the full source collection. Default discovery shows open issues from enabled sources. Users can filter by project, civic topic, technical skill, difficulty, estimated effort, source state, and upstream assignment status, and search titles/body/labels. Support sorting, pagination, saved issues, and issue detail views.

Show original labels, upstream assignees, source URL, GitHub issue number, freshness, and matching explanations. A local database ID must not be presented as though it were the original GitHub issue number.

Assigned issues remain part of the source collection. Their assignment is clearly displayed; users may explicitly filter for unassigned issues. Do not claim all open issues are unclaimed or suitable for beginners.

### Source synchronization

Support an initial complete scan, incremental updates, pagination, rate-limit handling, bounded retries/backoff, a scheduled worker, and administrator-triggered scans. Default scans run hourly, with configurable longer intervals where appropriate to source limits.

Use stable repository/issue identities and idempotent upserts. Preserve source state, including closed/reopened issues, changes in labels/assignees/content, and repository renames. Retain issue records referenced by personal histories rather than cascading away user work.

Record attempted/successful scan times, completeness, counts and sanitized failures. Preserve the last successful snapshot on a failed scan. Do not mark issues closed merely because they were absent from an incomplete or open-only response. Confirm closure through authoritative state or a known complete reconciliation. Permission loss, deletion or transfer is distinct from closure and must be represented as unavailable or reconciled explicitly.

### Matching and explanations

Rank issues using technical skill fit, civic interests, experience/difficulty, time/effort, optional repository preference, and bounded history/feedback adjustments. Display the factors and metadata coverage behind every score. With insufficient data, show limited confidence or an unscored issue rather than fabricate certainty.

The approved `evidence-v4` scoring weights are skills 60%, difficulty/experience 20%, civic interests 15%, and explicit availability/effort 5%. Scores use a fixed 100-point denominator. Matching known factors earn points; missing factors remain unknown and limit the available score instead of inflating the remaining factors. A percentage requires issue-specific skill evidence and profile skills. Otherwise display Limited information. Repository preferences, own feedback and completed activity affect equal-fit ordering only, not assessed fit. Cached LLM enrichment of public issue text supplies evidence-backed requirements; original labels and curator overrides remain preserved, with curator corrections taking priority. AI does not estimate effort or assign fit percentages. Distinguish stated and inferred skills with rationales and optional source quotations; inferred skills carry half the evidence weight of stated or curator-reviewed skills, and evidence coverage reflects this discount. Basic schema validation remains but inference is not rejected for lacking literal keywords. Record model/version and provenance; invalidate enrichment when source content changes. Processing is an explicit, budget-limited operator action rather than a request-time dependency.

A repository language is a weak project-level signal; it is not proof that a particular issue requires that language. Prefer explicit issue evidence and curator-reviewed classifications. Preserve unknown difficulty/effort. Display metadata provenance and coverage separately from compatibility. Scores are guidance, not estimates of acceptance probability.

Location does not affect the score in this scope. The product supports remote software contribution; civic interests identify the cause a person cares about. Scoring weights must be versioned and explainable if changed.

### Metadata review

Curators review uncertain classifications, set approved annotation fields, record a rationale, and reset overrides when appropriate. Retain source values and an audit trail with actor/time/before/after. Scans update source content without erasing curator corrections. Flag reviewed metadata for re-review when relevant source content changes materially.

### Contribution tracking

Saving an issue is a private bookmark. Tracking records the contributor's intent or progress; it does not reserve the issue for that person. Several contributors can track the same GitHub issue.

| Local state | Meaning | Conditions |
|---|---|---|
| Interested | Considering or planning a contribution | Issue record exists |
| In progress | Contributor reports active work | User explicitly starts tracking work |
| Submitted | Contribution has been submitted upstream | Store a relevant GitHub contribution URL |
| Completed | Contributor reports finishing their contribution | Record time and completion basis |
| Withdrawn | Contributor stops tracking active work | Preserve prior history; issue remains unchanged |

Support Interested → In progress → Submitted → Completed and withdrawal from active states. Allow completion without a pull request for documentation, testing, design or other work, but label it **self-reported** with a short explanation. Users can resume withdrawn work; additional contributions on the same issue require a new activity record so prior history remains intact.

Remove the old global exclusive-claim rule for external issues. UI actions become **Save issue**, **Track contribution**, **Start work**, **Add submission**, **Mark contribution complete**, and **Stop tracking**. Explain that GitHub assignment must be requested upstream according to project instructions.

Self-reported completion, a linked pull request being merged, and the source issue being closed are separate facts. If GitHub evidence is checked, show exactly the verified fact and time, such as “Linked PR merged.” Do not infer issue resolution, the user's identity, or sole authorship from an arbitrary link. Source closure never automatically marks every user's contribution complete.

### Relevance feedback

Allow relevant/not relevant ratings and optional explanations up to 1,000 characters. Users can review/update their own feedback. Changes to ranking remain bounded, deterministic and explained. Feedback is not a public rating of a contributor or a guarantee that an issue is unsuitable for other users.

### Messaging

Retain basic in-app direct messages for coordination with curators/administrators and existing contacts. Volunteers cannot cold-message arbitrary other contributors. Conversations remain private to participants; administrator role alone does not grant access to every conversation.

Provide message persistence, unread/read state, text validation, conversation selection, and send/reply. Polling is sufficient for the baseline; real-time sockets, attachments, group chats and GitHub discussion mirroring are outside the baseline. Conversations do not substitute for a project's official contribution process.

### Notifications

Required in-app events include account welcome, saved/tracked contribution events, and newly matching issues after a successful scan. Support read/unread state and notification preferences. Avoid repeated alerts for the same unchanged issue/event. Existing messages have separate unread indicators.

Email delivery is an optional extension, not required for the first GitHub-based release. No curator notification implies an external maintainer has been contacted or accepted a contributor. Any staff coordination alerts must be explicitly scoped and implemented, not inferred from the old design.

### Administration and operations

Provide source add/disable/configuration for GitHub repositories, curator repository assignments, role management, scan schedules, manual scans, status/errors, and audit review. Restrict fetch targets to valid configured GitHub repositories; do not fetch arbitrary user-supplied URLs. Keep credentials outside stored issue data and client responses.

Disabling a source removes it from default discovery and stops its scheduled scans. Existing saved/tracked records remain accessible with a disabled-source indicator. Audit role changes, source changes, annotation changes and relevant security events without logging passwords or tokens.

## 7. Main user journeys

1. **Find an issue:** register → technical/civic profile → ranked issue list → read explanations and source details → open GitHub → follow contribution instructions.
2. **Track work:** save/track → start work → add a submission URL or activity note → record completion or withdrawal → review private history.
3. **Improve metadata:** curator login → assigned project issues → inspect source evidence → correct annotations/rationale → see revised recommendation → inspect recorded correction.
4. **Operate sources:** administrator login → source configuration → scan → inspect coverage/freshness/errors → retry or disable a failing source while retaining history.
5. **Coordinate:** contributor opens a permitted conversation with a curator → sends a message → recipient reads/replies; issue discussion and acceptance remain upstream.

## 8. Navigation and screens

| Screen | Main content |
|---|---|
| Discover issues | Ranked feed, filters, metadata coverage, assignment/freshness indicators |
| Projects | Five civic projects, missions, source/contribution links, issue collections |
| Issue detail | GitHub content, issue number/assignees, explanations, annotations, tracking actions |
| Saved issues | Private bookmarks |
| My contributions | Local activity states, evidence links, history |
| Profile and account | Technical/civic preferences, identity/session, export/deletion |
| Messages | Permitted conversations and unread counts |
| Notifications | In-app event list, read controls, preferences |
| Metadata review | Curator's assigned projects, annotations and review rationale |
| Administration | Accounts/roles, repository configuration, scans and audit |

Replace local **Create issue** forms in the real-source experience with **Open issue on GitHub**, linking to the selected project's creation/contribution entry point. The app does not write an issue on the user's behalf. Preserve fictional samples only as clearly separated test/demo fixtures, excluded from the normal real-source feed.

## 9. Architecture and persistent information

Retain the four-layer structure: responsive web presentation → application request handling/authorization → domain services → relational persistence. Background scanning uses the same domain/persistence rules as on-demand synchronization.

Persist accounts/sessions/roles, curator source access, repository identity/settings/status, source issues/assignees/labels/timestamps, metadata annotations/provenance, saved issues, contribution activity/events/evidence, feedback, messages, notifications/preferences and audit records. Version schema changes with data-preserving migrations. Do not reuse the old ActiveClaim task-key uniqueness rule for multi-user external contribution tracking.

GitHub is the required source provider for this release. Keep the adapter boundary for future providers; an existing GitLab adapter may be retained, but GitLab integration is not a release acceptance requirement. GitHub OAuth, write-back, webhooks and automatic PR submission are outside the baseline.

## 10. Security and quality requirements

Retain salted password hashing, opaque server-managed sessions, inactivity expiry, private account-scoped data, cross-site write protections, validation, throttling and safe secret handling. Curator permissions are repository-scoped; administrator role is application-scoped. Serve production traffic over HTTPS and configure secure cookies.

Sanitize rendered GitHub Markdown and URLs; imported issue content is untrusted. A source issue cannot issue instructions to the application, change privileges, or trigger arbitrary network requests. Contributions are not executed by the app. External tokens are operator-configured with the minimum required access; public-source reading does not require each contributor to provide a GitHub token.

Preserve original measurable targets from the SRS as verification targets, not passed results:

| Quality target | Required measurement |
|---|---|
| Recommendation latency | First page within 5 seconds for 95% of requests at 100 concurrent active users over 30 minutes |
| Profile/detail/history latency | Within 3 seconds for 95% of requests under the same load |
| Sessions | 500 simultaneously authenticated sessions without data loss or authorization errors |
| Aggregation scale | 50 repositories and 100,000 open/closed records scanned within 60 minutes when source limits permit |
| Freshness after scan | Retrieved changes eligible for recommendation within 5 minutes after a successful scan |
| First-time usability | At least 80% of five representative users create an account/profile and open a recommendation within 5 minutes without assistance |

The initial product has five selected sources; the 50-source target is a scalability test, not an additional source-selection commitment. Test API-budget assumptions and report source-imposed limits separately. Use keyboard access, visible focus, semantic controls and responsive layouts, then perform an accessibility review. Production operation requires recoverable daily backups and a demonstrated restore path; the earlier SRS's availability/retention requirements remain operations verification work.

## 11. Baseline release and later extensions

### Required for the redefined baseline

The release includes all five repositories with complete tracker ingestion, source-preserving synchronization and hourly scheduling; contributor accounts/profiles; explained matching with metadata provenance; project/issue discovery; personal saves and nonexclusive contribution tracking; curator reviews; basic administration; feedback; in-app coordination/notifications; account export/deletion; and verified deployment/quality controls.

A release must report functional acceptance and quality verification separately. A working UI is not proof that scale, privacy, security or accessibility targets passed. If any required item is deferred, record that explicitly as a scope change or an incomplete requirement.

### Later extensions

Email delivery, GitHub account ownership verification/OAuth, upstream issue assignment/write-back, webhook-driven synchronization, additional providers such as GitLab, more civic projects, automated skill extraction using language models, public contributor profiles, and real-time/group messaging may follow. None is implied by selecting a repository as a source.

### Outside the product

Physical volunteer-event scheduling, service dispatch, paying contributors, operating the source civic services, running untrusted submitted code, developing fixes automatically, guaranteeing issue assignment or acceptance, and providing an alternative GitHub pull-request/code-review system are outside scope.

## 12. Acceptance scenarios

| ID | Acceptance scenario |
|---|---|
| AC01 | Each initial repository is configured and a paginated scan imports all issue states without a label whitelist or pull-request contamination. Counts/scan completeness can be reconciled with the source at scan time. |
| AC02 | Repeated scans update the same stable issues without duplication; rename, close/reopen and changed-assignee cases retain identity/history. |
| AC03 | An interrupted/malformed/rate-limited scan retains the last successful snapshot, displays failure/freshness and does not falsely close missing records. |
| AC04 | New signup receives contributor privileges only. Direct unauthorized curator/admin API calls fail; curator access is limited to assigned repositories. |
| AC05 | A saved technical/civic profile changes ranked recommendations; missing metadata is not invented and score explanations/coverage identify contributing signals. |
| AC06 | Project/issue pages show original issue numbers, source URLs, assignees and contribution instructions. Filters do not change which issues are ingested. |
| AC07 | Two contributors can independently track one external issue. Neither action changes GitHub assignment; each private history is isolated. |
| AC08 | Submitted/completed/withdrawn transitions retain evidence and event history; self-reported completion is distinct from merged-PR evidence and source closure. |
| AC09 | An authorized correction survives later source refresh, updates effective matching metadata and produces an audit entry. |
| AC10 | Source disablement stops scans/default discovery but preserves accessible personal history and clear source-state indicators. |
| AC11 | Scheduled scans run with recorded status and bounded failure handling; new matches generate deduplicated in-app notifications under user preferences. |
| AC12 | Permitted users can message/read/reply and track unread state; unrelated users cannot retrieve or mutate their messages/notifications. |
| AC13 | Export contains the user's defined personal data; reauthenticated deletion/anonymization follows documented retention rules without exposing other users. |
| AC14 | Local/CI tests and a repeatable demo validate the full contributor → GitHub handoff → tracking → curator → administrator path. |
| AC15 | Performance, accessibility, security, usability, deployment and backup/restore results are recorded against section 10 rather than asserted from functional tests. |

## 13. Transition from the existing implementation

| Existing implementation | Transition action |
|---|---|
| Authentication, sessions, profiles, relational persistence | Retain; expand technical skill taxonomy and privacy/migration support |
| GitHub adapters/manual canonical ingestion | Extend for complete tracker coverage, assignments, original issue numbers, incremental/scheduled scans and resilient reconciliation |
| Fictional civic repository and Create issue | Isolate as fixtures; real-source UI links to GitHub |
| Weighted matching and metadata overlays | Retain structure; improve technical evidence/provenance, coverage, feedback/history and correction review |
| Exclusive claim/release/completion | Migrate historical records safely to contribution activity; replace external issue claims with nonexclusive tracking |
| Maintainer role | Relabel as Curator and preserve explicit repository scope without asserting upstream membership |
| Basic role/source/audit UI | Extend with source creation, schedules, scan diagnostics and review rationale |
| Tariq's upstream messaging/notifications | Integrate and verify; adapt role language/event semantics and add missing preferences/new-match behavior |

As of this definition, local code still reflects the earlier demo and has not been restructured to these requirements. Tariq's upstream `ad8b544` adds basic messages and in-app notifications; it was inspected but not pulled or verified locally. Its current notifications cover welcome/saving/participation, not the full event scope above. Earlier functional test results do not establish that the redefined release is complete.

Existing user accounts, source records and activity histories must not be discarded to perform the transition. Preserve original events and identify migrated records. Do not silently turn earlier exclusive claims into assertions of GitHub assignment or verified contribution acceptance.

### Implementation order

1. Align schema, terminology, permissions and acceptance tests with this scope.
2. Integrate the upstream messaging work while preserving local changes.
3. Import the five real repositories and build project/issue views with authoritative source fields.
4. Replace claims with contribution tracking and migrate prior records.
5. Improve metadata/matching and add scheduled synchronization, feedback and event behavior.
6. Complete privacy, administration and deployment work, then execute functional and quality acceptance.

## 14. Team responsibility guide

Use the WBS table's general allocation, adjusted for the new semantics. This is a planning assignment, not a claim of original code authorship.

| Member | Primary focus for the transition |
|---|---|
| Andre Walia | Canonical ingestion/synchronization, source administration, curator overlays and integration tests |
| Michael Anstett | Schema/migrations, profiles/RBAC, matching and explanations, privacy functions |
| Tariq Khan | Responsive contributor/curator/admin screens; integration of existing messages and notifications UI |
| Davian Brooks | Contribution state/history, feedback/notification coordination, scope tracking and demo/documentation |
| David Landivar | Provider adapters, authentication/security, infrastructure, performance testing and deployment |

Module boundaries are shared. Coordinate API/data contracts before implementing independent screens or changing source-state semantics.

## 15. Supporting references

- [Software requirements](P30_Civic_Issue_Matchmaker_IEEE_830_SRS(1).md)
- [Software design](<SOFTWARE DESIGN DOCUMENT (SDD).md>)
- [Development plan and WBS](<Project Development Plan and Milestones(1).md>)
- [Layered architecture](layered_system_architecture.md)
- [Historical artifact handling](artifcats/AGENTS.md)
- [Original Civic Issue Finder inspiration](https://github.com/codeforamerica/civic-issue-finder)

### Contribution removal

Contributors can remove their own local contribution in any state, including completed and withdrawn. Removal deletes that entry and its local event history, with confirmation in the UI and stale-version protection in the API. It does not delete the source issue, other users' contributions or independent bookmarks. The issue can be tracked again afterward.
