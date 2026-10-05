# EGN 4950C - Senior Design I

SOFTWARE REQUIREMENTS SPECIFICATION
Civic Issue Matchmaker

Group 12

Prepared in accordance with IEEE Std 830-1998

Version 1.0
July 2026

| Team Members | Role |
| --- | --- |
| Davian Brooks | Collaborating author |
| Michael Anstett | Collaborating author |
| Tariq Khan | Collaborating author |
| Andre Walia | Collaborating author |
| David Landivar | Collaborating author |

All team members collaborated on the complete document.

## Revision History

| Version | Date | Authors | Description |
| --- | --- | --- | --- |
| 1.0 | July 2026 | Davian Brooks; Michael Anstett; Tariq Khan; Andre Walia; David Landivar | Initial IEEE 830-1998 SRS with course-specific materials placed in appendixes. |

## Table of Contents

1. Introduction 3

1.1 Purpose 3

1.2 Scope 3

1.3 Definitions, Acronyms, and Abbreviations 3

1.4 References 4

1.5 Overview 4

2. Overall Description 4

2.1 Product Perspective 4

2.2 Product Functions 4

2.3 User Characteristics 4

2.4 Constraints 4

2.5 Assumptions and Dependencies 5

3. Specific Requirements 5

3.1 External Interface Requirements 5

3.2 System Features 6

3.3 Performance Requirements 9

3.4 Design Constraints 9

3.5 Software System Attributes 9

3.6 Other Requirements 10

Appendix A - Project Summary and Scenarios 11

Appendix B - IEEE Standard Confirmation 12

Appendix C - Feasibility of Implementation 12

Appendix D - Credits and Authorship 12

Appendix E - AI-Assisted Iterative Process 12

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the externally observable requirements for the Civic Issue Matchmaker. It establishes the required functions, external interfaces, performance characteristics, constraints, and software quality attributes of the product before design and implementation. The intended audience includes the project sponsor, course instructor, development team, testers, repository maintainers, volunteers, and other stakeholders who must evaluate or verify the product.

### 1.2 Scope

The Civic Issue Matchmaker is a software system that connects volunteers with suitable open tasks from participating civic-technology repositories. The product aggregates eligible tasks, records task metadata, allows volunteers to describe their skills and interests, calculates task compatibility, presents ranked recommendations with explanations, and supports task-status and feedback workflows. Repository maintainers can review and correct task metadata associated with repositories they manage.

The product is intended to reduce the effort required for volunteers to locate suitable civic-technology work and to help maintainers attract qualified contributors. The product will not perform source-code development on behalf of a volunteer, guarantee acceptance of a contribution, replace the workflow of the source repository, or determine whether a volunteer is legally or professionally qualified for work outside the participating repository.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
| --- | --- |
| API | Application Programming Interface; an interface through which software systems exchange data or requests. |
| Civic technology | Technology intended to improve public services, government operations, or civic participation. |
| Compatibility score | A numeric value that represents the degree of fit between a volunteer profile and an open task. |
| Maintainer | An authorized user responsible for one or more participating repositories. |
| Open task | A repository issue or work item that remains available for volunteer contribution. |
| Repository | A managed collection of project artifacts and work items from which tasks may be aggregated. |
| SRS | Software Requirements Specification. |
| Task metadata | Structured information describing a task, including title, source, status, topic, required skills, and estimated effort. |
| Volunteer | A user seeking a civic-technology task to which they may contribute. |

### 1.4 References

IEEE Computer Society. IEEE Std 830-1998, IEEE Recommended Practice for Software Requirements Specifications. Approved 25 June 1998.

Code for America. Civic Issue Finder repository. Referenced as background for the project concept; access location supplied in Appendix A.

### 1.5 Overview

Section 2 describes the product perspective, principal functions, intended users, constraints, assumptions, and dependencies. Section 3 specifies external interfaces, system features, performance requirements, design constraints, software system attributes, and other requirements. The appendixes contain course-specific materials that are not essential parts of the IEEE 830 SRS structure.

## 2. Overall Description

### 2.1 Product Perspective

The Civic Issue Matchmaker is an independent service that operates between participating repository sources and its users. It reads eligible task information from external repository services and provides a separate interface for volunteer profiles, recommendations, maintainer corrections, feedback, and notifications. The source repository remains the authoritative location for task content and contribution activity. The Matchmaker stores only the information needed to provide its own functions and maintains synchronization with the source when that source is available.

### 2.2 Product Functions

- Create and manage user accounts and role-appropriate profiles.

- Aggregate eligible open tasks from a configurable set of participating repositories.

- Extract and maintain task metadata, including status, topic, skills, and effort.

- Compare volunteer profiles with open tasks and calculate compatibility scores.

- Present ranked recommendations and plain-language explanations.

- Allow volunteers to filter, sort, claim, track, and provide feedback on tasks.

- Allow maintainers to review and correct task metadata for repositories they manage.

- Notify users about relevant task and claim events.

- Continue limited recommendation service when a source repository is temporarily unavailable.

### 2.3 User Characteristics

| User Class | Description | Expected Skill | Primary Goals |
| --- | --- | --- | --- |
| Volunteer | A person seeking a civic-technology task. | Basic web literacy; civic-technology experience is not required. | Create a profile, discover suitable work, understand recommendations, and track participation. |
| Repository Maintainer | A person authorized to represent a participating repository. | Familiarity with the repository and its task labels or workflow. | Verify task data, correct metadata, and observe claims. |
| System Administrator | A person responsible for system configuration and operation. | Technical administration knowledge. | Manage sources, availability, security, and operational settings. |

### 2.4 Constraints

- The system shall interact only with repository sources for which access is authorized and technically available.

- The system shall not require a particular programming language, hosting provider, database product, or matching technique.

- The system shall preserve the source repository as the authoritative location for task content and contribution workflow.

- The system shall limit maintainer actions to repositories for which the maintainer has been authorized.

- The system shall comply with applicable institutional policies and laws governing personal information.

### 2.5 Assumptions and Dependencies

- Participating repository services provide sufficient task data and a permitted means of access.

- Repository labels and descriptions may be incomplete or inconsistent; maintainers may correct derived metadata.

- Users provide accurate profile information and are responsible for deciding whether to accept a recommendation.

- External repository availability and rate limits are outside the direct control of the product.

- Notification delivery depends on the availability of the selected notification channel.

- The initial release is intended for modern desktop and mobile web browsers.

## 3. Specific Requirements

Each requirement has a unique identifier. Essential requirements are mandatory for product acceptance. Conditional requirements are desirable but do not make the product unacceptable if omitted by agreement. Requirements are organized by feature in accordance with the feature-oriented template in Annex A.5 of IEEE Std 830-1998.

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

UI-1 [Essential] The system shall provide role-appropriate interfaces for volunteers, repository maintainers, and system administrators.

UI-2 [Essential] The system shall display validation feedback adjacent to, or clearly associated with, the input that caused the validation failure.

UI-3 [Essential] The system shall present each recommendation with the task title, source repository, current status, compatibility information, and a link or control that opens the authoritative task page.

UI-4 [Essential] The system shall preserve a user's entered profile data when validation fails, except for secret authentication values.

UI-5 [Essential] The system shall adapt its interface to viewport widths from 360 through 1920 CSS pixels without requiring horizontal scrolling for primary workflows.

#### 3.1.2 Hardware Interfaces

The product has no specialized hardware interface requirements. It shall operate using standard client and server computing hardware appropriate to the deployed workload.

#### 3.1.3 Software Interfaces

SI-1 [Essential] The system shall retrieve eligible task data from each configured repository source through an interface permitted by that source.

SI-2 [Essential] The system shall record the source identifier and authoritative source location for every aggregated task.

SI-3 [Essential] The system shall detect and handle source responses indicating authorization failure, rate limiting, malformed data, or temporary unavailability.

SI-4 [Essential] The system shall provide an administrative mechanism for adding, disabling, and updating repository-source configurations without changing application source code.

#### 3.1.4 Communications Interfaces

CI-1 [Essential] The system shall protect all authenticated network communication against disclosure and alteration while in transit.

CI-2 [Essential] The system shall reject network requests that do not conform to the supported request format or authorization rules.

CI-3 [Essential] The system shall provide a clear error response when an external communication operation cannot be completed.

### 3.2 System Features

#### 3.2.1 Account and Profile Management

##### 3.2.1.1 Introduction/Purpose

This feature identifies users and stores the information required to provide role-appropriate functions and recommendations.

##### 3.2.1.2 Stimulus/Response Sequence

1. A new user requests registration or an existing user requests authentication.

1. The system validates the request and establishes the user identity or returns a specific failure message.

1. A volunteer creates or updates profile information; a maintainer requests access to an authorized repository.

1. The system validates and stores accepted changes and displays the current profile or authorization state.

##### 3.2.1.3 Associated Functional Requirements

FR-1 [Essential] The system shall allow a user to create an account using an email address and password or an approved external identity service.

FR-2 [Essential] The system shall allow a user to authenticate and terminate an authenticated session.

FR-3 [Essential] The system shall allow a volunteer to create and edit a profile containing skills, experience levels, interest areas, preferred task difficulty, and available time commitment.

FR-4 [Essential] The system shall allow a user to hold a volunteer role, a repository-maintainer role, or both.

FR-5 [Essential] The system shall verify maintainer authorization before granting access to maintainer functions for a repository.

FR-6 [Essential] The system shall allow a user to request permanent deletion of the account and associated personal profile data.

#### 3.2.2 Task Aggregation and Metadata Management

##### 3.2.2.1 Introduction/Purpose

This feature obtains eligible tasks from participating repositories and maintains the structured data used by the matching feature.

##### 3.2.2.2 Stimulus/Response Sequence

1. A scheduled scan begins or an authorized administrator requests a scan.

1. The system requests task data from each enabled source and validates the response.

1. The system creates or updates local task records and identifies tasks that are no longer open.

1. A maintainer reviews a task and may submit corrected metadata.

1. The system stores the correction and uses it for subsequent recommendations.

##### 3.2.2.3 Associated Functional Requirements

FR-7 [Essential] The system shall scan each enabled repository source at least once every 60 minutes unless the source configuration specifies a longer interval.

FR-8 [Essential] The system shall identify eligible open tasks according to configurable source-specific selection rules.

FR-9 [Essential] The system shall store, for each aggregated task, its title, description, source repository, authoritative source location, source identifier, current status, labels, topic, required skills, and estimated effort when those values are available or can be derived.

FR-10 [Essential] The system shall update each aggregated task to reflect a detected open, claimed, or closed state no later than the next successful scan of its source.

FR-11 [Essential] The system shall preserve the most recent successfully retrieved task data when a source scan fails.

FR-12 [Essential] The system shall allow an authorized maintainer to review and correct derived topic, skill, difficulty, and effort metadata for tasks in the maintainer's repository.

FR-13 [Essential] The system shall record the identity, time, original value, and corrected value for each maintainer correction.

#### 3.2.3 Matching and Recommendation

##### 3.2.3.1 Introduction/Purpose

This feature compares volunteer preferences and capabilities with available tasks and explains the resulting recommendations.

##### 3.2.3.2 Stimulus/Response Sequence

1. A volunteer requests recommendations or changes profile or filter criteria.

1. The system selects currently eligible tasks and calculates a compatibility score for each selected task.

1. The system ranks the tasks and displays the results with explanations.

1. The volunteer may change filters or sort order, causing the system to present an updated result set.

##### 3.2.3.3 Associated Functional Requirements

FR-14 [Essential] The system shall calculate a compatibility score for each pairing of a requesting volunteer and an eligible open task.

FR-15 [Essential] The compatibility score shall consider the volunteer's skills, experience, interests, preferred difficulty, and available time, and the corresponding task metadata when those values are present.

FR-16 [Essential] The system shall present recommended tasks in descending compatibility order by default.

FR-17 [Essential] The system shall provide, for each recommendation, a human-readable explanation identifying at least two factors that increased or decreased the task's compatibility score.

FR-18 [Essential] The system shall allow a volunteer to filter recommendations by repository, topic, difficulty, estimated effort, required skill, and task status.

FR-19 [Essential] The system shall allow a volunteer to sort recommendation results by compatibility, recency, difficulty, or estimated effort.

FR-20 [Essential] The system shall exclude closed tasks and tasks known to be claimed by another volunteer from the default active recommendation list.

#### 3.2.4 Task Participation, History, and Feedback

##### 3.2.4.1 Introduction/Purpose

This feature lets volunteers record their relationship to a task and provide information that improves later recommendations.

##### 3.2.4.2 Stimulus/Response Sequence

1. A volunteer selects a recommended task and requests a participation-state change.

1. The system validates task availability and records the requested state or explains why the request cannot be completed.

1. The volunteer may submit relevance feedback or mark the task completed.

1. The system records the event and uses eligible history and feedback during later matching.

##### 3.2.4.3 Associated Functional Requirements

FR-21 [Essential] The system shall allow a volunteer to mark an open task as saved, claimed, in progress, released, or completed.

FR-22 [Essential] The system shall prevent two volunteers from simultaneously holding an active claim to the same task within the Matchmaker.

FR-23 [Essential] The system shall maintain a chronological history of a volunteer's saved, claimed, released, and completed tasks.

FR-24 [Essential] The system shall allow a volunteer to rate a recommendation as relevant or not relevant and optionally provide a textual explanation of up to 1,000 characters.

FR-25 [Conditional] The system shall use completed-task history and explicit relevance feedback as inputs to subsequent compatibility calculations.

FR-26 [Essential] The system shall provide a control that opens the authoritative repository page for a selected task.

#### 3.2.5 Notifications

##### 3.2.5.1 Introduction/Purpose

This feature informs users of relevant changes without requiring them to repeatedly inspect the system.

##### 3.2.5.2 Stimulus/Response Sequence

1. A newly aggregated or updated task meets a volunteer's saved notification criteria, or a volunteer claims a maintainer's task.

1. The system creates a notification event.

1. The system delivers the event through each enabled notification channel and records the delivery outcome.

1. The recipient can view or dismiss the notification.

##### 3.2.5.3 Associated Functional Requirements

FR-27 [Essential] The system shall allow a volunteer to enable or disable notifications for newly available tasks that meet saved criteria.

FR-28 [Essential] The system shall notify an opted-in volunteer within 15 minutes after a successful scan identifies a newly eligible task meeting the volunteer's saved criteria.

FR-29 [Conditional] The system should notify an opted-in maintainer when a volunteer claims a task from the maintainer's repository.

FR-30 [Essential] The system shall allow each user to view and dismiss notifications generated for that user.

FR-31 [Essential] The system shall record whether each notification delivery succeeded or failed.

### 3.3 Performance Requirements

PR-1 [Essential] The system shall return the first page of recommendation results within 5 seconds for at least 95 percent of requests under a load of 100 concurrent active users, measured over a 30-minute test period.

PR-2 [Essential] The system shall return profile, task-detail, and task-history views within 3 seconds for at least 95 percent of requests under the load defined in PR-1.

PR-3 [Essential] The system shall support at least 500 simultaneously authenticated user sessions without loss of stored data or incorrect authorization decisions.

PR-4 [Essential] The system shall complete a scan of 50 repositories containing a combined total of 100,000 open and closed task records within 60 minutes when the sources respond within their documented limits.

PR-5 [Essential] The system shall make a successfully retrieved new or changed task eligible for recommendation within 5 minutes after completion of the scan that retrieved it.

### 3.4 Design Constraints

DC-1 [Essential] The system shall use only repository interfaces and task data that the project is authorized to access.

DC-2 [Essential] The system shall maintain a unique mapping between each local task record and its authoritative source identifier.

DC-3 [Essential] The system shall not expose credentials or secret access tokens in user-visible pages, logs, notifications, or exported diagnostic information.

DC-4 [Essential] The system shall separate volunteer, maintainer, and administrator permissions so that each protected operation is available only to authorized roles.

DC-5 [Essential] The system shall retain maintainer corrections separately from automatically derived metadata so that a later scan does not silently overwrite a correction.

### 3.5 Software System Attributes

#### 3.5.1 Reliability and Availability

RA-1 [Essential] The system shall provide monthly service availability of at least 99.0 percent, excluding announced maintenance periods totaling no more than 4 hours per month.

RA-2 [Essential] The system shall continue to display the most recent cached recommendations and task details when one or more repository sources are temporarily unavailable.

RA-3 [Essential] The system shall identify cached task data with the time of the most recent successful source update.

RA-4 [Essential] The system shall recover from an interrupted repository scan without corrupting previously stored task data.

RA-5 [Essential] The system shall create a recoverable backup of user, task, correction, claim, and feedback data at least once every 24 hours and retain at least seven daily backups.

#### 3.5.2 Security and Privacy

SP-1 [Essential] The system shall store authentication secrets only in a non-reversible, salted cryptographic representation suitable for password verification.

SP-2 [Essential] The system shall require reauthentication before an account deletion or credential change is completed.

SP-3 [Essential] The system shall prevent one volunteer from viewing another volunteer's private profile, history, feedback, or notification data.

SP-4 [Essential] The system shall expose to a maintainer only the volunteer information required to evaluate or coordinate an active claim, as defined by system policy.

SP-5 [Essential] The system shall invalidate an authenticated session after 30 minutes of inactivity and shall allow a user to explicitly sign out.

SP-6 [Essential] The system shall record successful and failed authentication attempts, authorization failures, maintainer corrections, and administrative configuration changes with time and actor information.

SP-7 [Essential] The system shall remove or irreversibly anonymize deleted personal profile data within 30 days of a verified deletion request, except where retention is legally required.

#### 3.5.3 Usability

US-1 [Essential] At least 80 percent of five representative first-time volunteer test participants shall complete account creation, profile creation, and opening one recommended task within 5 minutes without assistance.

US-2 [Essential] The system shall explain each validation failure using a message that identifies the invalid field and the corrective action required.

US-3 [Essential] The system shall provide a visible indication when recommendation results are filtered, sorted, stale, empty, or unavailable.

US-4 [Essential] The system shall provide keyboard access to all controls required for account, profile, recommendation, task-status, feedback, and maintainer-correction workflows.

#### 3.5.4 Maintainability and Portability

MP-1 [Essential] The system shall allow an authorized administrator to add or disable a repository source without redeploying the complete application.

MP-2 [Essential] The system shall record operational errors with sufficient context to identify the failed operation, time, source, and affected record without recording secret credentials.

MP-3 [Essential] The system shall support the current and immediately preceding major versions of Chrome, Firefox, Edge, and Safari on desktop and mobile platforms at the time of release.

MP-4 [Essential] The system shall permit the matching rules or model to be replaced without requiring changes to the external repository-source interfaces or user-profile data format.

### 3.6 Other Requirements

OR-1 [Essential] The user interface shall satisfy the testable success criteria of WCAG 2.1 Level AA that apply to the implemented content and workflows.

OR-2 [Essential] The system shall display a privacy notice before collecting personal profile information.

OR-3 [Essential] The system shall allow a user to obtain a machine-readable copy of the user's stored profile, participation history, and submitted feedback.

OR-4 [Essential] The system shall display the authoritative repository's applicable contribution and conduct information when that information is supplied by the source or maintainer.

OR-5 [Essential] The system shall not represent a recommendation as a guarantee that the volunteer will be accepted, qualified, or successful.

## Appendix A - Project Summary and Scenarios

This appendix contains course-required materials that are not separate essential sections of the IEEE 830 prototype SRS outline.

### A.1 Project Summary

Civic-technology projects depend on volunteer developers, designers, researchers, and subject-matter contributors. Open tasks are often distributed across many repositories with inconsistent labels and descriptions, requiring volunteers to manually locate tasks and judge whether each task fits their skills, interests, and available time. This friction can discourage first-time contributors and leave useful civic work unresolved.

The Civic Issue Matchmaker addresses this problem by aggregating eligible tasks from participating civic-technology repositories, maintaining structured task metadata, comparing tasks with volunteer profiles, and presenting ranked recommendations with explanations. Volunteers can refine recommendations, record participation, and provide feedback. Authorized maintainers can review and correct task metadata. The product remains independent of any particular programming language, hosting platform, data store, or matching algorithm.

Reference implementation for inspiration: Code for America, Civic Issue Finder, https://github.com/codeforamerica/civic-issue-finder

### A.2 Scenarios

#### Scenario 1 - First-Time Volunteer Finds a Matching Task

Amara is a computer science student who wants to contribute to civic-technology projects. She creates an account and a profile that lists Python, basic web development, a few hours of weekly availability, and an interest in accessibility. The system compares her profile with eligible open tasks and presents a ranked list. Each result identifies why it fits. Amara filters the list, opens one task in its authoritative repository, and records that she has claimed it.

#### Scenario 2 - Returning Volunteer Refines Recommendations

Diego returns after completing two tasks. He updates his experience level and asks for tasks in a selected topic and a higher difficulty range. The system uses his current profile, completion history, and filters to re-rank available tasks. A task already claimed by another volunteer is omitted from the default active list.

#### Scenario 3 - Repository Maintainer Corrects Task Metadata

Priya is authorized for a participating repository. She reviews aggregated tasks and notices that one task has an incorrect required skill and difficulty estimate. She submits corrections. The system records the original values, corrected values, time, and actor, and uses the corrections in later matching.

#### Scenario 4 - Source Repository Is Temporarily Unavailable

During a civic hackathon, volunteers request recommendations while one repository source is unreachable. The system continues to display cached tasks and recommendations, marks the data with the most recent successful update time, and resumes synchronization after the source becomes available.

#### Scenario 5 - Account Deletion and Privacy

A volunteer requests account deletion. The system requires reauthentication, confirms the request, removes access immediately, and deletes or anonymizes the volunteer's personal profile data within the specified period while preserving only data that must legally remain.

## Appendix B - IEEE Standard Confirmation

The team reviewed IEEE Std 830-1998 before preparing this SRS. The main body follows the prototype SRS structure in Clause 5 and uses the feature-oriented organization for Section 3 shown in Annex A.5. Requirements are individually identified and written to be correct, unambiguous, complete, internally consistent, ranked for necessity, verifiable, modifiable, and traceable. Product requirements are kept in the SRS; course administration, authorship, feasibility discussion, scenarios, and AI-process documentation are placed in appendixes rather than inserted as product requirements.

## Appendix C - Feasibility of Implementation

The defined scope is feasible for a senior design team because the product relies on commonly available repository interfaces, standard account and authorization functions, structured task metadata, and a replaceable matching component. The essential workflows can be delivered incrementally: account and profile management; aggregation from a limited set of repositories; rule-based or statistical matching; recommendations; maintainer correction; participation tracking; and notifications.

The measurable performance targets are sized for a student project while still requiring meaningful engineering and testing. The largest risks are inconsistent source metadata, repository rate limits, synchronization failures, authorization mistakes, and recommendation quality. These risks are reduced by source-specific selection rules, caching, explicit correction records, role-based access controls, measurable load tests, and explanations that expose the factors used by matching. No requirement depends on unavailable proprietary technology.

## Appendix D - Credits and Authorship

All five team members collaborated on the project summary, scenarios, functional requirements, non-functional requirements, IEEE organization, feasibility review, revision review, and final presentation of the submission.

| Team Member | Components | Role |
| --- | --- | --- |
| Davian Brooks | All components | Collaborating author and reviewer |
| Michael Anstett | All components | Collaborating author and reviewer |
| Tariq Khan | All components | Collaborating author and reviewer |
| Andre Walia | All components | Collaborating author and reviewer |
| David Landivar | All components | Collaborating author and reviewer |

## Appendix E - AI-Assisted Iterative Process

AI assistance was used to reorganize and revise the requirements. The team remains responsible for validating the final content. The interaction used for this version is documented below.

### E.1 Prompt 1

Using the attached example of  a Software Requirements Specification (SRS) document that strictly follows IEEE Std 8301998 (prototype SRS structure) for a project  "Civic Issue Matchmaker" from https://github.com/codeforamerica/civic-issue-finder,  which aggregates open tasks from participating civictechnology repositories and matches volunteers to tasks; produce a clear, concise, and testable SRS that uses "shall" for essential requirements and "should" for conditional/desirable requirements, marks each requirement with a unique identifier, and keeps requirements implementable and verifiable for our group (assignment instructions and rubric are supplied); the SRS must include Introduction, Overall Description, Specific Requirements (external interfaces, system features organized by feature with unique IDs, performance, design constraints, software attributes, other requirements), and Appendices for course materials, and must follow only the IEEE standard (omit nonIEEE Canvas material) while placing any extra course or rubric material in an appendix, using the below information:

Civic Issue Matchmaker

Authors: Davian Brooks; Michael Anstett; Tariq Khan; Andre Walia; David Landivar

Introduction: Connect volunteers with suitable open tasks from participating civic-technology repositories by aggregating tasks, recording task metadata, matching volunteers to tasks, and presenting ranked recommendations with explanations.

Scope:

- Aggregate eligible open tasks from authorized repositories.

- Store task metadata: title, description, source id, authoritative URL, status, labels, topic, required skills, estimated effort.

- Allow volunteers to create profiles (skills, experience, interests, preferred difficulty, available time).

- Compute a compatibility score between volunteer profiles and tasks and present ranked recommendations with plainlanguage explanations.

- Allow maintainers to review and correct derived metadata for repositories they manage.

- Provide notifications for newly matching tasks and claim events.

- Cache most recent task data when sources are temporarily unavailable.

Primary users:

- Volunteer

- Repository Maintainer

- System Administrator

Essential nonfunctional targets:

- Availability: ≥ 99.0% monthly (excluding limited maintenance).

- Recommendation latency: first page within 5 s for 95% of requests under 100 concurrent users.

- Scan cadence: default scan interval hourly per enabled source.

- Backups: daily, retain at least seven daily backups.

- Security: store authentication secrets in non-reversible salted form; session timeout 30 minutes.

Core data model

- User: Identifies an account holder and their roles; stores contact and authentication info, role(s), profile details about skills and preferences, and lifecycle timestamps.

- Repository Source: Describes an external task provider, its access configuration, selection rules, enabled state, and last synchronization metadata.

- Task Record: Represents an aggregated work item with a link to its authoritative source, descriptive fields, labels or topic tags, required capabilities, effort estimate, current status, and any maintainer-supplied corrections.

- Claim: Tracks a user’s interaction with a task (saved, claimed, in progress, released, completed) along with relevant timestamps and state history.

- Notification: Captures a user-targeted event, the criteria that triggered it, delivery channel and timing, and the outcome of delivery.

Features List:

1. Account creation and authentication (email/password; external identity optional).

1. Profile creation/editing for volunteers.

1. Scheduled scanning of configured repositories; create/update local TaskRecord entries.

1. Maintainer correction UI and audit log of corrections.

1. Matching engine that computes compatibility scores and returns ranked results with explanations.

1. Recommendation filters and sorting (repository, topic, difficulty, effort, status).

1. Claiming workflow with concurrency protection (prevent simultaneous active claims).

1. Notification delivery and delivery outcome recording.

1. Export of a user's profile and participation history in machine-readable form.

### E.2 Output 1

The generated output is Version 1.0 of this document. It reorganized the product requirements into the IEEE 830 prototype structure, used the feature-oriented organization for specific requirements, separated external interfaces, performance, constraints, and software attributes, converted vague statements into measurable shall/should requirements, ranked requirements as essential or conditional, and moved course-only materials into Appendixes A through E.

### E.3 Team Review and Revision

The team reviewed the generated document for correctness against the approved project scope, revise any requirement that does not reflect stakeholder intent, and retain future prompts and outputs if additional AI-assisted revisions are made before submission.
