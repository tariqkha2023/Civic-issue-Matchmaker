# Course: EGN4950C 

# Group 12

# **Civil Issue Matchmaker-Work Breakdown Structure (WBS)**

# Authors: Davian Brooks, Michael Anstett, Tariq Khan, Andre Walia, David Landivar

*Duration: August to December*

| **WBS Code** | **Task Name**                                        | **Description**                                                                                                                            | **Responsible Party** | **Start Date** | **Due Date**   | **Duration** | **Dependencies**  |
|--------------|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-----------------------|----------------|----------------|--------------|-------------------|
| 1.1          | 1.1 Teams Planner & Agile Board Setup                | Configure MS Teams Planner board, buckets, sprint cadence, task cards, and team notification rules.                                        | Davian Brooks         | 08/24/2026     | 08/28/2026     | 0.5 Week     | None              |
| 1.2          | 1.2 SDD/SRS Baseline & Tech Stack Review             | Review SRS v1.0 and SDD v1.0 specifications; finalize repo layout, API contracts, and database schema conventions.                         | Davian Brooks         | 08/24/2026     | 09/04/2026     | 2 Weeks      | 1.1               |
| 1.3          | 1.3 CI/CD Pipeline & Dev Server Setup                | Establish automated CI build runner, linter checks, containerized database containers, and staging deployment server.                      | David Landivar        | 08/31/2026     | 09/11/2026     | 2 Weeks      | 1.1               |
| 1.4          | 1.4 Progress Tracking & Risk Management              | Monitor bi-weekly sprint velocity, track blockers on Teams Planner, manage architectural updates, and update audit logs.                   | Davian Brooks         | 08/24/2026     | 12/11/2026     | 16 Weeks     | 1.0               |
| **M1**       | **M1: Dev Infrastructure & Planner Operational**     | **MILESTONE: Teams Planner board configured, CI/CD pipeline operational, baseline architecture verified, dev environment ready.**          | **Davian Brooks**     | **09/11/2026** | **09/11/2026** | **-**        | **1.1, 1.2, 1.3** |
| 2.1          | 2.1 Repository Connector Base Interface              | Implement abstract adapter interface for external task sources isolating rate limits and auth headers.                                     | Andre Walia           | 09/07/2026     | 09/18/2026     | 2 Weeks      | 1.3               |
| 2.2          | 2.2 GitHub REST/GraphQL Adapter                      | Build concrete adapter for GitHub Civic Repositories / Code for America issue finder APIs.                                                 | David Landivar        | 09/14/2026     | 09/25/2026     | 2 Weeks      | 2.1               |
| 2.3          | 2.3 Secondary Repository Adapter (GitLab)            | Develop a secondary adapter for GitLab civic projects to prove multi-source repository portability.                                        | David Landivar        | 09/21/2026     | 10/02/2026     | 2 Weeks      | 2.1               |
| 2.4          | 2.4 Task Aggregation & Canonical Storage Engine      | Extract and map source tasks into local canonical Task records (title, description, source URL, skills, effort).                           | Andre Walia           | 09/21/2026     | 10/09/2026     | 3 Weeks      | 2.2               |
| 2.5          | 2.5 Scheduled Scan Worker & State Tracker            | Build automated background cron worker scanning enabled sources every 60 mins and detect open/closed tasks.                                | Andre Walia           | 09/28/2026     | 10/09/2026     | 2 Weeks      | 2.4               |
| 2.6          | 2.6 Source Outage Fault Tolerance & Diagnostics      | Ensure failed scans to preserve last successful cached task data without corruption and log diagnostics.                                   | Andre Walia           | 10/05/2026     | 10/16/2026     | 2 Weeks      | 2.5               |
| **M2**       | **M2: Data Aggregation Pipeline Live**               | **MILESTONE: Repository adapters successfully** **scraping, mapping, and storing task metadata from GitHub/GitLab on a 60-min interval.**  | **Andre Walia**       | **10/16/2026** | **10/16/2026** | **-**        | **2.5, 2.6**      |
| 3.1          | 3.1 Database Schema & Relational Migrations          | Design and implement SQL tables for Users, Repositories, Tasks, Recommendations, Claims, Feedback, and Audit logs.                         | Michael Anstett       | 09/14/2026     | 09/25/2026     | 2 Weeks      | 1.3               |
| 3.2          | 3.2 User Identity & Authentication Service           | Implement registration, login, session tokens, and password hashing using Bcrypt/Argon2 salted representation.                             | David Landivar        | 09/21/2026     | 10/02/2026     | 2 Weeks      | 3.1               |
| 3.3          | 3.3 Volunteer Profile Management Engine              | Build CRUD operations for volunteer profiles including skills, experience level, interest topics, and weekly availability.                 | Michael Anstett       | 09/28/2026     | 10/09/2026     | 2 Weeks      | 3.2               |
| 3.4          | 3.4 RBAC Authorization & Session Inactivity Timeout  | Implement role enforcement (Volunteer, Maintainer, Admin) and automated 30-minute session inactivity expiration.                           | Michael Anstett       | 10/05/2026     | 10/16/2026     | 2 Weeks      | 3.2               |
| 3.5          | 3.5 Privacy Compliance, Export & Account Deletion    | Develop permanent account deletion workflow, data anonymization engine, and machine-readable JSON data export.                             | Michael Anstett       | 10/12/2026     | 10/23/2026     | 2 Weeks      | 3.3               |
| **M3**       | **M3: Auth & Volunteer Profiles Baseline**           | **MILESTONE: Secure authentication, role enforcement, profile CRUD operations, session management, and privacy compliance verified.**      | **Michael Anstett**   | **10/23/2026** | **10/23/2026** | **-**        | **3.4, 3.5**      |
| 4.1          | 4.1 Matching Engine Framework & Architecture         | Establish modular matching service architecture, separating profile extraction, task filtering, and scoring calculations.                  | Michael Anstett       | 09/28/2026     | 10/16/2026     | 3 Weeks      | 2.4, 3.3          |
| 4.2          | 4.2 Weighted Multi-Factor Scoring Algorithm          | Implement 0-100 compatibility formula: Skills (35%), Interests (20%), Experience (15%), Effort (15%), Location (5%), History (10%).        | Michael Anstett       | 10/12/2026     | 10/23/2026     | 2 Weeks      | 4.1               |
| 4.3          | 4.3 Plain-Language Explanation Generator             | Generate dynamic human-readable explanation strings identifying top positive and negative match factors for each task.                     | Michael Anstett       | 10/19/2026     | 10/30/2026     | 2 Weeks      | 4.2               |
| 4.4          | 4.4 Recommendation Filtering & Exclusions Engine     | Build multi-criteria search filters (repo, topic, difficulty, effort, skill) and exclude closed or claimed tasks from feed.                | Michael Anstett       | 10/26/2026     | 11/06/2026     | 2 Weeks      | 4.3               |
| **M4**       | **M4: Matching Engine & Recommendation Live**        | **MILESTONE: Recommendation engine generating ranked task feeds with compatibility scores, explanations, and filtering live in API.**      | **Michael Anstett**   | **11/06/2026** | **11/06/2026** | **-**        | **4.3, 4.4**      |
| 5.1          | 5.1 Participation State Machine Service              | Manage task participation states (Saved, Claimed, In Progress, Released, Completed) with chronological event logging.                      | Davian Brooks         | 10/12/2026     | 10/23/2026     | 2 Weeks      | 3.2, 2.4          |
| 5.2          | 5.2 Atomic Task Claim Concurrency Control Engine     | Implement database transactions and active-claim unique constraints to prevent double claims by concurrent volunteers.                     | Davian Brooks         | 10/19/2026     | 10/30/2026     | 2 Weeks      | 5.1               |
| 5.3          | 5.3 Relevance Feedback & Bounded Learning Engine     | Capture relevant/not relevant ratings with text explanations (up to 1,000 chars) and feed history into matching adjustments.               | Davian Brooks         | 10/26/2026     | 11/06/2026     | 2 Weeks      | 5.1               |
| 5.4          | 5.4 Notification Event Engine & In-App Alerts        | Create notification events for newly matching tasks and maintainer alerts when tasks are claimed, complete with delivery logs.             | Davian Brooks         | 11/02/2026     | 11/13/2026     | 2 Weeks      | 5.1               |
| **M5**       | **M5: Participation & Notifications Operational**    | **MILESTONE: Atomic claim engine, state transitions, explicit feedback collection, and automated in-app/email notifications verified.**    | **Davian Brooks**     | **11/13/2026** | **11/13/2026** | **-**        | **5.2, 5.4**      |
| 6.1          | 6.1 Maintainer Metadata Correction Overlay Service   | Allow authorized maintainers to review/correct task tags, difficulty, and skills while preserving original source data.                    | Andre Walia           | 10/26/2026     | 11/06/2026     | 2 Weeks      | 2.4, 3.4          |
| 6.2          | 6.2 System Administration & Source Config            | Build an admin interface to add, disable, or adjust scan intervals for repository sources without redeploying code.                        | Andre Walia           | 11/02/2026     | 11/13/2026     | 2 Weeks      | 2.1, 3.4          |
| 6.3          | 6.3 System Health Monitor & Audit Logging Service    | Capture operational logs, failed scan metrics, privileged role changes, and auth failures without exposing secrets.                        | Andre Walia           | 11/09/2026     | 11/20/2026     | 2 Weeks      | 6.2               |
| 7.1          | 7.1 Responsive Client App Shell & Design System      | Create a responsive layout shell supporting 360px to 1920px viewports with horizontal scrolling.                                           | Tariq Khan            | 10/05/2026     | 10/16/2026     | 2 Weeks      | 1.3               |
| 7.2          | 7.2 Volunteer Dashboard & Profile Forms UI           | Implement profile editor with adjacent validation messaging and form state preservation on validation failure.                             | Tariq Khan            | 10/12/2026     | 10/23/2026     | 2 Weeks      | 7.1, 3.3          |
| 7.3          | 7.3 Recommendation Feed, Task Details & Source Links | Build task recommendation feed displaying title, repo, compatibility score, explanation factors, and authoritative source links.           | Tariq Khan            | 10/26/2026     | 11/06/2026     | 2 Weeks      | 7.1, 4.4          |
| 7.4          | 7.4 Maintainer Workspace & Admin Console UI          | Build views for repository maintainers to submit task corrections and system administrators to manage sources and logs.                    | Tariq Khan            | 11/02/2026     | 11/13/2026     | 2 Weeks      | 7.1, 6.1          |
| 7.5          | 7.5 WCAG 2.1 AA Accessibility & Keyboard Nav         | Implement visible focus rings, ARIA labels, semantic markup, and full keyboard control across all core workflows.                          | Tariq Khan            | 11/09/2026     | 11/20/2026     | 2 Weeks      | 7.3, 7.4          |
| **M6**       | **M6: Full Application Frontend UI Baseline**        | **MILESTONE: Responsive UI complete across desktop/mobile viewports; full frontend integrated with backend APIs and WCAG compliant.**      | **Tariq Khan**        | **11/20/2026** | **11/20/2026** | **-**        | **7.3, 7.4, 7.5** |
| 8.1          | 8.1 Automated Test Suite (Unit & Integration)        | Develop unit tests for matching algorithms and integration tests for repository aggregation and claim state transitions.                   | Andre Walia           | 11/09/2026     | 11/20/2026     | 2 Weeks      | M4, M5            |
| 8.2          | 8.2 Performance & Load Testing Verification          | Verify PR-1 (\<5s recommendation latency @ 100 users), PR-2 (\<3s profile latency), PR-3 (500 sessions), and PR-4 (50 repos/100k records). | David Landivar        | 11/16/2026     | 11/27/2026     | 2 Weeks      | 8.1               |
| 8.3          | 8.3 Security Audit, RBAC & Privacy Testing           | Verify password hash security, HTTPS transport, secret masking, RBAC isolation, session expiration, and profile privacy.                   | David Landivar        | 11/23/2026     | 12/04/2026     | 2 Weeks      | 8.1               |
| 8.4          | 8.4 First-Time Volunteer Usability Trial             | Execute formal usability trial with representative users verifying \>=80% complete onboarding & claim within 5 mins.                       | David Landivar        | 11/23/2026     | 12/04/2026     | 2 Weeks      | M6                |
| **M7**       | **M7: QA Verification & Security Audit Complete**    | **MILESTONE: All SRS performance benchmarks (PR-1 to PR-5), security rules (SP-1 to SP-7), and usability targets (US-1) formally passed.** | **David Landivar**    | **12/04/2026** | **12/04/2026** | **-**        | **8.2, 8.3, 8.4** |
| 9.1          | 9.1 Production Cloud Deployment & Backups            | Deploy application to production host, configure SSL certificates, set up automated 24-hr DB backup retention.                             | David Landivar        | 11/23/2026     | 12/04/2026     | 2 Weeks      | M7                |
| 9.2          | 9.2 Final Software Documentation & User Manuals      | Compile complete technical documentation, developer API references, maintainer user guides, and final report.                              | Davian Brooks         | 12/01/2026     | 12/08/2026     | 1 Week       | 9.1               |
| 9.3          | 9.3 Senior Design II Presentation & Demo             | Prepare final presentation slides, conduct live product demonstrations for course instructors/sponsors, and deliver final code repo.       | Davian Brooks         | 12/07/2026     | 12/11/2026     | 1 Week       | 9.2               |
| **M8**       | **M8: Final Senior Design II Project Handover**      | **MILESTONE: Successful final presentation, live system deployed in production, documentation handed over, course completion achieved.**   | **Davian Brooks**     | **12/11/2026** | **12/11/2026** | \-           | **9.3**           |

***\*\*Note: Assignments and Due dates are subject to change***

**Team Member Task Allocation & Responsibilities**

**1. Davian Brooks (Project Manager & Frontend Lead)**

-   **Primary Responsibilities:** Overall project management, schedule tracking on Teams Planner, responsive UI architecture, WCAG 2.1 AA accessibility compliance, and final presentation lead.

-   **Key Deliverables:**

    -   Lead UI/UX design and implementation.

    -   Administer usability testing with first-time volunteer participants.

    -   Coordinate final report compilation and showcase presentation.

**2. Michael Anstett (Backend & Security Lead)**

-   **Primary Responsibilities:** Application service coordination, authentication/authorization (RBAC), profile management services, and technical documentation.

-   **Key Deliverables:**

    -   Implement authentication, session handling, and RBAC.

    -   Build volunteer profile and account deletion API.

    -   Implement maintainer correction processing logic.

    -   Lead technical documentation and API specification assembly.

**3. Tariq Khan (Data & Repository Integration Lead)**

-   **Primary Responsibilities:** Relational database design, persistence layer, repository connector adapters, and automated task aggregation engine.

-   **Key Deliverables:**

    -   Design and implement relational database schema and migration scripts.

    -   Develop external repository connector adapters for source integration.

    -   Build hourly task aggregation and normalization engine.

    -   Lead Data Pipeline Milestone.

**4. Andre Walia (Algorithm & Matching Lead)**

-   **Primary Responsibilities:** Recommendation engine design, weighted compatibility scoring algorithm, explanation factor generator, and feedback loop integration.

-   **Key Deliverables:**

    -   Build multi-factor compatibility scoring engine.

    -   Implement human-readable explanation generator and filter/sort APIs.

    -   Integrate volunteer relevance feedback and history learning loop.

    -   Lead Recommendation Integration Milestone.

**5. David Landivar (Systems, QA, & Infrastructure Lead)**

-   **Primary Responsibilities:** DevOps/CI-CD, concurrency control, notification service, production deployment, and system verification/testing.

-   **Key Deliverables:**

    -   Setup developer environment, Docker, and CI/CD deployment pipelines.

    -   Implement atomic task claiming concurrency protection.

    -   Build event-driven notification manager service.

    -   Lead automated performance/load testing and production backup setup.

**Key Project Milestones Summary**

**Milestone 1 (M1) – Aggregation & Data Pipeline Operational (Oct 09, 2026)**

*Criteria:* Automated background scanner successfully fetches, normalizes, and stores tasks from external repositories with metadata preserved.

**Milestone 2 (M2) – Recommendation Engine Integrated (Oct 23, 2026)**

*Criteria:* Matching algorithm successfully computes compatibility scores and generates multi-factor explanations for volunteer profiles.

**Milestone 3 (M3) – Full System Integration Completed (Nov 13, 2026)**

*Criteria:* Responsive frontend interface fully connected to application services, enabling end-to-end user workflows from account registration to task claiming.

**Milestone 4 (M4) – System Verification Passed (Nov 27, 2026)**

*Criteria:* System passes all latency (\<5s), concurrency (100 active users), security, accessibility, and usability benchmarks specified in the SRS.

**Milestone 5 (M5) – Final Deployment & Presentation Completed (Dec 11, 2026)**

*Criteria:* Software successfully deployed to production environment with daily backups enabled; final report and presentation delivered.

*\*\*Note: Completion dates subject to change*
