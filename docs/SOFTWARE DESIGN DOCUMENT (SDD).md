# SOFTWARE DESIGN DOCUMENT (SDD)

Civic Issue Matchmaker

Course: EGN 4950C - Engineering Design 1

Prepared by: Group 12

Davian Brooks | Michael Anstett | Tariq Khan | Andre Walia | David Landivar

Version: 1.0

Date: July 2026

Design basis: IEEE Std 1016-1998 (reaffirmed 2009)

All team members collaborated on the complete document.

Revision History

| Version | Date | Authors | Description |
| --- | --- | --- | --- |
| 1.0 | July 2026 | Group 12 | Initial complete SDD aligned with the approved Civic Issue Matchmaker SRS. |

## Table of Contents

1. Introduction

2. System Overview and Architecture

3. Design Views

4. Detailed Component Design

5. Interface Design

6. Data Design

7. Design Constraints

8. Security, Privacy, and Safety Considerations

9. Design Decisions and Trade-offs

10. Requirements Traceability

11. References

Appendix A - Interface Contracts

Appendix B - Data Dictionary Summary

## 1. Introduction

### 1.1 Purpose

This Software Design Document defines the architecture, design entities, interfaces, data structures, processing rules, constraints, and significant design decisions for the Civic Issue Matchmaker. It translates the approved Software Requirements Specification into an implementation blueprint that developers, testers, maintainers, and project stakeholders can use during construction and verification.

### 1.2 Scope

The Civic Issue Matchmaker is a software service that aggregates eligible open tasks from authorized civic-technology repositories and recommends appropriate tasks to volunteers. The system maintains volunteer profiles, collects and normalizes repository task metadata, computes compatibility scores, provides ranked recommendations with explanations, supports task saving and participation state changes, records feedback and history, sends notifications, and permits authorized repository maintainers and administrators to manage corrections and source configuration.

The design does not assume a specific repository vendor, cloud provider, database product, or frontend framework. Repository systems remain authoritative for task content and status. The Matchmaker stores normalized copies and derived metadata required for search, recommendation, history, notification, and administration.

### 1.3 Intended Audience

The intended audience includes the Group 12 development team, course instructors, system testers, repository maintainers, system administrators, and future developers responsible for implementation or maintenance.

### 1.4 Definitions, Acronyms, and Abbreviations

| Term | Definition |
| --- | --- |
| API | Application Programming Interface used to exchange structured requests and responses. |
| Civic technology | Technology intended to improve public services, government operations, or civic participation. |
| Repository | An authorized external project source containing tasks or work items. |
| Task metadata | Structured information about a task, including title, description, source, labels, skills, difficulty, status, and estimated effort. |
| Volunteer | A user seeking a civic-technology task to which they may contribute. |
| Maintainer | An authorized user responsible for one or more participating repositories. |
| Compatibility score | A derived value representing the fit between a volunteer profile and an open task. |
| SDD | Software Design Description. |
| SRS | Software Requirements Specification. |
| RBAC | Role-Based Access Control. |

### 1.5 References

- IEEE Computer Society. (1998). IEEE Std 1016-1998: IEEE Recommended Practice for Software Design Descriptions (reaffirmed 2009).

- IEEE Computer Society. (1998). IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.

- Group 12. (2026). Civic Issue Matchmaker Software Requirements Specification, Version 1.0.

- Code for America. Civic Issue Finder repository, used as project inspiration.

### 1.6 Document Overview

Section 2 presents the system context and architecture. Section 3 organizes the design using decomposition, dependency, interface, and detail views. Section 4 defines each major component. Sections 5 and 6 specify interfaces and data. Sections 7 through 9 address constraints, security, and design decisions. Section 10 maps SRS requirements to design entities.

## 2. System Overview and Architecture

### 2.1 Product Perspective

The system is a multi-user web application positioned between volunteers and participating repository services. It does not replace the source repositories. Instead, it periodically retrieves authorized task data, stores normalized records, calculates recommendations, and provides role-specific interfaces for volunteers, repository maintainers, and administrators.

### 2.2 Architectural Style

The design uses a layered modular architecture with service-oriented internal boundaries. The presentation layer handles browser interactions; the application layer coordinates use cases; domain services implement matching, participation, notification, and administrative rules; integration adapters isolate repository-specific APIs; and the persistence layer stores normalized and derived data. This separation supports maintainability, source portability, role isolation, and testability.

Figure 1. Layered architecture of the Civic Issue Matchmaker.

### 2.3 Architectural Responsibilities

| Layer / Element | Primary Responsibility |
| --- | --- |
| Web Client | Presents responsive role-appropriate views and collects user input. |
| Presentation Layer | Validates request shape, applies session checks, and maps domain results to views or API responses. |
| Application Services | Coordinates end-to-end use cases and transaction boundaries. |
| Repository Integration | Connects to authorized sources, handles rate limits and failures, and converts source records into canonical form. |
| Matching Engine | Calculates compatibility scores, ranks tasks, and produces explanation factors. |
| Participation Service | Maintains saved, claimed, in-progress, released, and completed task states with concurrency protection. |
| Notification Service | Creates and delivers notification events while recording delivery outcomes. |
| Administration Service | Manages repository configuration, users, roles, source health, and operational reporting. |
| Relational Database | Persists users, sources, tasks, metadata corrections, recommendations, history, feedback, notifications, and logs. |

### 2.4 Deployment View

A typical deployment consists of a browser client, one or more stateless application instances, a relational database, a scheduler or background worker for source scans and notification delivery, and network access to authorized repository APIs and an optional email provider. Application instances may be replicated behind a reverse proxy. Shared database constraints and transactional operations prevent conflicting task claims across instances.

### 2.5 Quality Attribute Strategy

- Performance: indexed task and recommendation queries, pagination, cached source data, and bounded recommendation candidate sets.

- Availability: cached task information remains viewable during temporary source outages.

- Security: salted password hashing, RBAC, secure sessions, input validation, protected transport, and audit logging.

- Maintainability: adapters isolate external repository APIs and domain services isolate business rules.

- Portability: standards-based browser interfaces and platform-independent server components.

## 3. Design Views

### 3.1 Decomposition View

The system is partitioned into design entities that can be implemented, tested, and modified with limited impact on unrelated functions. Figure 2 shows the major entities and their primary relationships.

Figure 2. Major component relationships and shared data dependencies.

### 3.2 Dependency View

The Recommendation Engine depends on current normalized task data, volunteer profile attributes, participation history, and feedback. The Task Aggregator depends on repository adapters and source configuration. Participation depends on task availability and database transaction support. Notifications depend on domain events produced by aggregation, recommendation, and participation operations. Administrative functions depend on RBAC and audit logging.

### 3.3 Interface View

External interactions occur through browser-based HTTPS requests, repository APIs, and optional email delivery. Internal interactions use typed service interfaces and persistent domain records. Component contracts avoid exposing repository-specific data structures beyond the integration layer.

Figure 3. Simplified use case diagram for the Civic Issue Matchmaker.

### 3.4 Detail View

Detailed processing rules for registration, scanning, matching, participation, notification, and correction are defined in Section 4. Each component description identifies its purpose, inputs, outputs, dependencies, processing, and data.

## 4. Detailed Component Design

### 4.1 Account and Profile Management

Purpose: Maintains authentication identities, roles, volunteer profile attributes, maintainer authorization, account settings, and lifecycle operations.

Inputs: Registration data, credentials, external identity assertions, profile fields, role requests, account deletion requests.

Outputs: Authenticated session, validated profile, role decision, update confirmation, account deletion result.

Processing. Validate unique email; hash passwords using a slow salted algorithm; verify credentials; create a secure session; authorize requested role; preserve accepted profile data on validation errors; reauthenticate before sensitive changes.

Primary data. User, RoleAssignment, Session, VolunteerProfile, MaintainerRepositoryAccess.

### 4.2 Repository Connector

Purpose: Provides a uniform interface for authorized repository services and isolates vendor-specific APIs, authentication methods, pagination, rate limits, and response formats.

Inputs: Source configuration, credentials or tokens, last scan cursor, scheduling request.

Outputs: Canonical source task records, scan status, failure details, next cursor.

Processing. Select the adapter matching the source type; authenticate; request changed or open tasks; follow pagination; validate responses; map source fields to canonical fields; retry transient failures with backoff; preserve prior successful data on failure.

Primary data: RepositorySource, SourceCredentialReference, ScanRun, RawTaskSnapshot.

### 4.3 Task Aggregation and Metadata Management

Purpose: Stores normalized open tasks, tracks authoritative source identity, applies maintainer corrections, and preserves the most recent successful source state.

Inputs: Canonical task records, previous task state, correction overlays, scan timestamps.

Outputs: Created or updated Task records, closed-task markers, change events, source health status.

Processing: Update and insert using the unique source-task mapping; detect new, changed, closed, or reopened tasks; preserve correction overlays separately from derived data; invalidate affected recommendation snapshots; emit availability events.

Primary data: Task, TaskLabel, RequiredSkill, MetadataCorrection, ScanRun.

### 4.4 Recommendation and Matching Engine

Purpose: Calculates a compatibility score for each eligible volunteer-task pairing, ranks results, and explains major score factors.

Inputs: Volunteer profile, active filters, eligible task set, participation history, and explicit feedback.

Outputs: Ranked Recommendation objects with score and explanation.

Processing. Filter out closed or actively claimed tasks; compute weighted factors for skill fit, interests, experience, difficulty preference, availability, and estimated effort; apply bounded history/feedback adjustments; normalize score; produce top explanatory factors; sort by compatibility and selected secondary order.

Primary data: Recommendation, MatchFactor, UserPreference, Feedback, ParticipationHistory.

Figure 4. Volunteer Task Matching Activity Diagram

### 4.5 Task Participation and History

Purpose: Controls saved, claimed, in-progress, released, and completed task states and maintains a chronological history.

Inputs: User ID, task ID, requested transition, optional note, or completion marker.

Outputs: Updated participation state, history event, conflict, or validation response.

Processing. Verify task availability and legal transition; perform atomic claim using a transaction and unique active-claim constraint; record event timestamp; release or complete as requested; trigger notifications; never represent participation as source-repository acceptance.

Primary data. Participation, ParticipationEvent, Task.

### 4.6 Feedback Management

Purpose: Records recommendation relevance feedback and uses prior completed-task history as bounded input to future recommendations.

Inputs: User ID, task ID, relevant/not relevant rating, optional explanation up to 1,000 characters.

Outputs: Stored feedback and recalculation trigger.

Processing: Validate ownership and length; store immutable feedback event; update derived preference signals asynchronously or on next recommendation request.

Primary data: Feedback, DerivedPreferenceSignal.

### 4.7 Notification Management

Purpose: Creates user-visible notifications for newly eligible tasks and claim events and records delivery outcomes.

Inputs: Domain event, user notification settings, recipient address, template data.

Outputs: In-app notification, optional email request, delivery status, retry record.

Processing: Check user preference; create an idempotent notification event; render channel template; deliver through configured provider; store success or failure; retry transient failures without duplicating visible events.

Primary data: Notification, NotificationDelivery, UserNotificationPreference.

### 4.8 Maintainer Metadata Correction

Purpose: Allows authorized maintainers to review and correct derived task fields while preserving source-provided authoritative content.

Inputs: Maintainer identity, repository authorization, task ID, field name, corrected value, reason.

Outputs: Correction record, updated effective metadata, audit event.

Processing: Authorize against the task repository; permit only approved derived fields; validate value; store correction separately; recompute effective metadata and affected recommendations; retain original source value.

Primary data: MetadataCorrection, MaintainerRepositoryAccess, AuditEvent.

### 4.9 Administration and Operations

Purpose: Manages repository sources, roles, system health, scan scheduling, notification status, and operational logs.

Input: Administrator commands, source configuration, role changes, report filters.

Output: Updated configuration, health dashboard, operational report, audit entry.

Processing. Apply RBAC; validate source configuration; enable or disable sources; schedule scans; inspect scan failures; manage user roles; record every privileged change.

Primary data: RepositorySource, RoleAssignment, ScanRun, AuditEvent, SystemSetting.

### 4.10 Compatibility Scoring Algorithm

The initial implementation uses a transparent weighted scoring model rather than an opaque predictive model. Each factor is normalized to a value between 0 and 1. A configurable weighted sum produces a 0-100 compatibility score. The design permits weight adjustment by administrators without changing source task data.

| Factor | Example Weight | Computation |
| --- | --- | --- |
| Required skill fit | 35% | Ratio of required skills satisfied, with optional partial credit for related skills. |
| Interest or topic fit | 20% | Overlap between volunteer interests and task labels/topics. |
| Experience and difficulty fit | 15% | Alignment between experience level and task difficulty. |
| Availability and effort fit | 15% | Whether estimated effort fits the volunteer time commitment. |
| Preferred repository or location | 5% | Optional match against saved preferences. |
| History and explicit feedback | 10% | Bounded adjustment from completed tasks and relevant/not-relevant ratings. |

Final score = 100 x sum(weight_i x factor_i). Explanations identify the highest positive and negative factors, for example, "Strong Python skill match; estimated effort fits your availability; difficulty is slightly above your preference."

Figure 5. Recommendation generation and atomic task claim sequence.

## 5. Interface Design

### 5.1 User Interfaces

| Interface | Primary Elements |
| --- | --- |
| Volunteer dashboard | Profile completion summary, filters, ranked task cards, explanation text, save/claim controls, notification indicator. |
| Task detail | Authoritative source link, title, description, status, repository, labels, required skills, estimated effort, effective corrected metadata, participation controls. |
| Profile editor | Skills, experience, interests, preferred difficulty, available time, notification settings. |
| History and feedback | Chronological participation events, completion status, relevance rating, optional explanation. |
| Maintainer workspace | Authorized repositories, aggregated tasks, metadata review, correction form, correction history. |
| Administrator console | Repository source configuration, scan status, users and roles, audit events, notification delivery status. |

All primary workflows must remain usable within a 360-by-1920 CSS pixel viewport without horizontal scrolling. Validation messages appear adjacent to or clearly associated with the relevant input. Keyboard navigation and visible focus indicators are required for all interactive controls.

### 5.2 Internal Service Interfaces

| Interface | Representative Operations |
| --- | --- |
| AccountService | register(), authenticate(), updateProfile(), requestRole(), deleteAccount() |
| RepositoryAdapter | validateConfiguration(), fetchOpenTasks(cursor), fetchTask(sourceId), testConnection() |
| AggregationService | scanSource(), upsertTask(), markMissingTasks(), applyCorrection() |
| RecommendationService | recommend(userId, filters), explain(recommendationId), invalidate(taskId) |
| ParticipationService | save(), claim(), start(), release(), complete(), getHistory() |
| NotificationService | createEvent(), deliver(), retry(), dismiss() |
| AdministrationService | addSource(), disableSource(), updateSchedule(), assignRole(), getHealthReport() |

### 5.3 External Repository Interface

Each repository adapter must support authenticated read access to eligible task information, pagination, rate-limit handling, timeout handling, and a stable mapping from the local Task record to the authoritative source identifier. The adapter returns canonical fields and retains the source URL so users can open the authoritative task page. Unsupported or unavailable fields remain null and are not invented unless a documented derivation rule exists.

### 5.4 Communication Interfaces

- Browser traffic uses HTTPS with secure cookies or an equivalent protected session mechanism.

- Repository traffic uses HTTPS and source-supported authentication. Tokens are stored outside user-visible pages and logs.

- Internal APIs use structured request and response objects with explicit validation errors.

- Notification delivery uses an email provider adapter; in-app notifications remain available even when external delivery fails.

### 5.5 Error Handling

User-facing errors must identify the operation that failed and provide a safe next action without exposing secrets or stack traces. Repository failures are recorded with source, time, operation, and sanitized diagnostic context. A failed scan must not delete the most recent successfully retrieved task data. Claim conflicts return a clear message that the task is no longer available.

## 6. Data Design

### 6.1 Data Model

Figure 6. Logical entity relationship overview.

### 6.2 Core Entities

| Entity | Purpose | Key Integrity Rules |
| --- | --- | --- |
| User | Stores identity, role, profile, and preferences. | Unique email; password stored only as salted hash; private profile access restricted. |
| Repository | Stores authorized source configuration and health state. | Unique source identity; secrets referenced securely; disabled sources are not scanned. |
| Task | Stores canonical and effective task metadata. | Unique (repository_id, source_task_id); source URL retained; source status authoritative. |
| Recommendation | Stores a user-task score and explanation snapshot. | Unique per user, task, and generation snapshot; invalidated when inputs materially change. |
| Participation | Stores the current user-task relationship. | At most one active claim per task; valid state-transition rules. |
| Feedback | Stores explicit relevance feedback. | One current rating per user-task pair or append-only events with latest projection. |
| Notification | Stores visible events and delivery outcomes. | Idempotency key prevents duplicate events. |
| MetadataCorrection | Stores maintainer corrections separately from source values. | Only authorized maintainers; only permitted fields; full audit history. |

### 6.3 Data Flow

Repository scan data flows through a source adapter into canonical validation and then into Task records. Effective task metadata is produced by combining source values, permitted derivations, and authorized correction overlays. Recommendation requests combine effective task data with volunteer profile and history. Participation changes create state events and notification events. Administrative operations create audit events. External repository data is never overwritten at the source by this system.

### 6.4 Transaction and Concurrency Design

Task claim operations use a database transaction, and a uniqueness or conditional-update rule that allows only one active claimant for a task. Profile updates, corrections, and source scans use optimistic version checks where concurrent modification is possible. Scan update and inserts are idempotent so a repeated scan does not duplicate tasks. Notification creation uses idempotency keys derived from event type, user, and domain event identifier.

### 6.5 Retention and Backup

The system creates recoverable daily backups and retains at least seven daily backups. Profile deletion removes or irreversibly de-identifies personal profile data within the required period while retaining only records that must legally or operationally remain. Audit and participation history retention is defined by policy and must not preserve unnecessary authentication secrets.

## 7. Design Constraints

| Constraint Area | Design Constraint |
| --- | --- |
| Repository authority | The source repository remains authoritative for task content, status, and contribution acceptance. |
| Authorized access | Only configured repository interfaces and permitted credentials may be used. |
| Technology neutrality | The SRS does not require a specific language, hosting provider, database product, or matching technique. |
| Performance | Recommendation results target 5 seconds for at least 95% of requests under 100 concurrent active users; common profile and task views target 3 seconds for at least 95% of requests. |
| Scale | The design supports at least 500 simultaneous authenticated sessions and a scheduled scan of 50 repositories containing up to 100,000 open and closed task records within 60 minutes when sources respond within documented limits. |
| Availability | Monthly service availability target is at least 99.0%, excluding announced maintenance. |
| Browser support | Current and immediately preceding major versions of Chrome, Firefox, Edge, and Safari on desktop and mobile. |
| Accessibility | Implemented workflows should satisfy WCAG 2.1 Level AA testable criteria. |
| Privacy | The system must avoid exposing one volunteer's private profile, history, feedback, or notification data to another volunteer. |

## 8. Security, Privacy, and Safety Considerations

### 8.1 Authentication and Session Security

- Store authentication secrets only as non-reversible salted password hashes or protected external identity references.

- Require reauthentication before account deletion or credential changes.

- Use secure, HttpOnly, SameSite session cookies or an equivalent protected mechanism.

- Invalidate inactive authenticated sessions after 30 minutes and allow explicit logout.

- Apply rate limiting and monitoring to login and password recovery operations.

### 8.2 Authorization

RBAC distinguishes volunteers, repository maintainers, and system administrators. Maintainer permissions are additionally scoped to specific repositories. Server-side authorization is required for every privileged operation; interface visibility alone is not considered protection.

### 8.3 Data Protection and Privacy

- Protect authenticated network traffic against disclosure and alteration.

- Do not expose source credentials or secret tokens in pages, feedback, logs, or diagnostics.

- Validate file, text, identifier, URL, and filter input before use.

- Limit profile visibility to the owner and authorized administrators according to policy.

- Record privileged configuration changes and authentication failures in audit logs without recording secrets.

### 8.4 Operational Safety and Misrepresentation

The system must not imply that a recommendation guarantees acceptance by a source repository or that participation within the Matchmaker constitutes an accepted contribution. Task detail pages link to the authoritative source and label derived or maintainer-corrected metadata appropriately. Cached data displays its last successful update time when a repository is unavailable.

### 8.5 Threat and Failure Mitigations

| Risk | Mitigation |
| --- | --- |
| Unauthorized account access | Password hashing, secure sessions, rate limiting, reauthentication, audit logging. |
| Malicious or malformed source data | Schema validation, output encoding, size limits, safe URL handling, and source isolation. |
| Duplicate task claims | Transactional claim operation and unique active-claim constraint. |
| Repository outage or rate limiting | Backoff, bounded retries, source health state, and cached last successful data. |
| Incorrect recommendations | Transparent explanations, user filters, feedback, bounded weights, and no acceptance guarantee. |
| Improper maintainer correction | Repository-scoped authorization, permitted-field list, immutable audit history, and preserved source value. |
| Notification duplication | Idempotency keys and recorded delivery state. |

## 9. Design Decisions and Trade-offs

| Decision | Rationale and Trade-off |
| --- | --- |
| Layered modular architecture | Chosen to separate user interfaces, business rules, source integration, and storage. It adds interface definitions but reduces coupling and improves testing. |
| Adapter pattern for repositories | Chosen because repository APIs and authentication differ. The cost is additional adapter code; the benefit is portability and failure isolation. |
| Transparent weighted recommendation model | Chosen for explainability, controllability, and feasibility. A complex machine-learning model could discover patterns but would be harder to validate and explain with limited project data. |
| Canonical local task store | Chosen to provide fast search, caching, history, and operation during temporary source outages. The trade-off is synchronization complexity and the need to show freshness. |
| Separate correction overlays | Chosen to preserve source authority while allowing maintainers to correct derived metadata. Overwriting imported values would destroy provenance. |
| Event-based notifications | Chosen to decouple business operations from channel delivery. It introduces event persistence but prevents email failure from blocking task operations. |
| Atomic participation claims | Chosen to satisfy concurrency requirements. Database-enforced consistency is preferred over user-interface-only checks. |
| Stateless application instances | Chosen to support horizontal scaling. Shared session or token validation and database coordination are required. |

## 10. Requirements Traceability

| SRS Requirement Group | Design Entities | Design Evidence |
| --- | --- | --- |
| UI-1 to UI-5 | Presentation Layer; all role-specific interfaces | Responsive role views, adjacent validation, task source links, preserved profile input. |
| SI-1 to SI-4 | Repository Connector; Task Aggregator; Administration Service | Authorized scans, source identifiers, failure handling, source configuration. |
| CI-1 to CI-3 | Presentation Layer; Repository Adapter; transport configuration | Protected communication, request validation, clear failures. |
| FR-1 to FR-6 | Account and Profile Management | Registration, authentication, profile management, roles, deletion. |
| FR-7 to FR-13 | Repository Connector; Task Aggregator; Metadata Correction | Scheduled scans, canonical storage, filtering, cached data, corrections. |
| FR-14 to FR-20 | Recommendation Engine | Compatibility scoring, ranking, explanations, filtering and exclusion rules. |
| FR-21 to FR-26 | Participation; Feedback and History | Saved/claimed/completed states, history, feedback, bounded learning input, authoritative source link. |
| FR-27 to FR-31 | Notification Management | Preferences, time-sensitive events, visible notifications, delivery outcomes. |
| PR-1 to PR-5 | Caching, indexes, pagination, stateless deployment, background workers | Response, session, and scan performance targets. |
| DC-1 to DC-5 | Repository Adapter; security design; correction overlays | Authorized source access, mapping, secret protection, role enforcement, provenance. |
| RA-1 to RA-5 | Deployment, caching, transaction design, backups | Availability, cached data, consistency, recoverability. |
| SP-1 to SP-7 | Authentication, RBAC, transport, audit and deletion services | Security and privacy requirements. |
| US-1 to US-4 | Responsive accessible presentation design | First-use, validation, state visibility, keyboard access. |
| MP-1 to MP-4 | Adapters, diagnostics, browser standards, canonical data model | Maintainability and portability. |
| OR-1 to OR-5 | Accessibility, privacy, export, source attribution, recommendation disclaimer | Other requirements and safeguards. |

## 11. References

Code for America. (n.d.). Civic Issue Finder. GitHub repository. Project inspiration referenced by the Group 12 SRS.

Group 12. (2026). Civic Issue Matchmaker Software Requirements Specification (Version 1.0). EGN 4950C - Senior Design I.

Institute of Electrical and Electronics Engineers. (1998). IEEE Std 1016-1998: IEEE Recommended Practice for Software Design Descriptions (reaffirmed 2009).

Institute of Electrical and Electronics Engineers. (1998). IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications.

Graphviz. (n.d.). Graphviz: Graph visualization software.

Graphviz. (n.d.). DOT language documentation.

Python Software Foundation. (n.d.). Python 3 documentation.

Pillow contributors. (n.d.). Pillow documentation.

World Wide Web Consortium. (2018). Web Content Accessibility Guidelines (WCAG) 2.1.

## Appendix A - Interface Contracts

| Operation | Request | Success Result | Representative Errors |
| --- | --- | --- | --- |
| POST /accounts | Email, password or external identity, profile starter fields | Created account and authenticated session | Duplicate email, weak credential, invalid field. |
| POST /sessions | Credential or external identity assertion | Authenticated session and role set | Invalid credential, locked/rate-limited account. |
| GET /recommendations | Filters, pagination, sort option | Ranked tasks, scores, explanations, freshness time | Profile incomplete, service temporarily unavailable. |
| POST /tasks/{id}/claim | Task identifier, expected version | Claimed participation state | Task closed, already claimed, stale version, unauthorized. |
| POST /tasks/{id}/feedback | Relevance rating, optional explanation | Stored feedback event | Invalid length, unknown task, unauthorized. |
| POST /maintainer/tasks/{id}/corrections | Field, corrected value, reason | Correction and effective metadata | Repository not authorized, field not correctable, invalid value. |
| POST /admin/repositories | Source type, URL, schedule, secret reference | Validated source configuration | Unsupported source, unreachable source, invalid authorization. |

## Appendix B - Data Dictionary Summary

| Data Element | Type / Format | Validation and Meaning |
| --- | --- | --- |
| compatibility_score | Decimal 0-100 | Derived match quality; not a guarantee of acceptance or success. |
| participation_state | Enum | saved, claimed, in_progress, released, completed. |
| task_status | Enum / source mapping | open, closed, or other explicitly mapped source status. |
| metadata_version | Integer | Incremented when source or correction inputs change. |
| scan_status | Enum | scheduled, running, succeeded, partially_failed, failed. |
| notification_delivery_status | Enum | pending, delivered, failed, suppressed. |
| last_successful_scan_at | UTC timestamp | Freshness marker for cached task data. |
| source_task_id | String | Stable authoritative identifier within a repository. |
| correction_reason | Text | Maintainer explanation retained in audit history. |
| session_last_activity | UTC timestamp | Used to enforce inactivity timeout. |
