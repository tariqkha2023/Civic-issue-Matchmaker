# Civic Issue Matchmaker

The halfway milestone is a connected volunteer MVP: register, edit a persistent
profile, browse imported GitHub/GitLab issues, receive explained recommendations,
and save tasks to a private shortlist. React/Vite powers the interface; FastAPI
and SQLAlchemy persist accounts, sessions, profiles, sources, tasks, and saved lists.
The backend work from `main`/`feat-andre` and the interface from
`origin/tariq-frontend` are combined here without deleting either application.

## Run the MVP

Requires Python 3.11+ and Node 18+ (Node 22 recommended). PostgreSQL 16 via Docker
is the recommended development database. SQLite is supported for a local demo.
Run commands from the repository root unless a step explicitly changes directory.

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
docker compose up -d
npm ci
```

On Windows use `py -3 -m venv backend/.venv`,
`backend\.venv\Scripts\Activate.ps1`, and
`Copy-Item backend/.env.example backend/.env` instead of the first two commands
and `cp`. If Docker is unavailable, set `DATABASE_URL=sqlite:///./civic-dev.db`
in `backend/.env`; omit `docker compose up -d`. The SQLite file persists locally.
The initial tables are created automatically on backend startup or source commands.

Start the backend in one terminal:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Start the frontend from the repository root in a second terminal:

```bash
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to the backend on port 8000;
this keeps authentication cookies and requests on the same browser origin.
If Vite chooses a different port, free port 5173 or update `APP_ORIGIN` to match.
Health checks remain at http://127.0.0.1:8000/health and `/health/db`.
Interactive API documentation is at http://127.0.0.1:8000/docs.

## Presentation demo: community issues

The demo uses **Community Care / Civic Issues**, a fictional local repository.
It contains 18 sample issues: soup kitchen shifts, pothole repair coordination,
food pantry support, park cleanup, gardening, accessibility surveys, tutoring,
and other community work. No GitHub/GitLab connection is used in the demo.

To populate a fresh database, run inside `backend` with the virtual environment active:

```bash
python -m app.demo
```

This adds missing samples without deleting accounts, overwriting issues, or creating
duplicates on subsequent runs. On **Discover**, choose **Create issue**, enter an
issue title and optional description, location, organizer, skills, topic, difficulty,
and estimated hours. New issues join the demo repository, appear in Discover, and
persist across refreshes and server restarts. The **Repository** navigation item
shows the populated issue collection. All sample places and requests are fictional.

For a simple presentation walkthrough:

1. Set your profile skills to `Food preparation, Communication` and interests to
   `Food security`, with Beginner experience/difficulty and 3 available hours.
2. Open Discover and inspect the soup kitchen match and its explanations.
3. Open Repository to show the collection of civic issues.
4. Create a new community issue, then find it in Discover and Repository.
5. Save an issue, open Saved tasks, and refresh to demonstrate persistence.

## Configure and import repository sources

Source configuration is an operator command in this milestone. Volunteers cannot
add arbitrary sources or grant themselves privileged access. Only configure
repositories whose access is permitted and which are appropriate civic projects.
With the backend virtual environment active, run inside `backend`:

```bash
python -m app.manage add-source github OWNER/REPOSITORY
python -m app.manage add-source gitlab NAMESPACE/PROJECT
python -m app.manage list-sources
python -m app.manage scan
```

Replace uppercase paths with actual repository paths. By default all open issues
are eligible; optionally add `--label "good first issue"` to `add-source`.
Repeat `--label` to select issues with any matching label. Re-running `add-source`
updates selection labels and re-enables the existing source. Disable a source with
`python -m app.manage disable-source ID`. Set `GITHUB_TOKEN` or `GITLAB_TOKEN` in
`backend/.env` if the authorized source requires credentials; credentials are never
stored in task records or returned by the API.

Scans are manual in this milestone. Re-run `python -m app.manage scan` to refresh.
A successful complete scan updates existing tasks, inserts new tasks without
duplicates, and marks previously imported issues that are absent as closed.
A failed or malformed scan rolls back changes and retains the previous snapshot,
its freshness timestamp, and a sanitized source error.

Skills derive from exact labels such as `python`, `react`, `documentation`, or
`skill:python`. Topics use `topic:Transportation`; difficulty uses `beginner`,
`intermediate`, `advanced`, `difficulty:beginner`, or `good first issue`.
Effort uses `effort:2h`. Other labels stay visible but do not invent metadata.
Profile topics and skill names match without case sensitivity.

The SDD weights are skill fit 35%, topic fit 20%, experience/difficulty fit 15%,
time/effort fit 15%, and optional repository preference 5%. The planned 10%
history/feedback factor is deferred. Available factors are renormalized; missing
metadata contributes no fabricated value. Tasks without usable matching metadata
are explicitly unscored. Scores express fit, not acceptance guarantees.

## Verify

```bash
python -m pytest
ruff check backend
npm run build
```

The tests use isolated databases for workflow checks and preserve existing connector
tests. Backend CI runs these workflows against PostgreSQL in a separate schema per
test; local tests default to SQLite. Set `TEST_DATABASE_URL` to exercise a local
PostgreSQL database (the test account must be allowed to create schemas). For the browser suite:

```bash
npm ci
npx playwright install chromium
npm run test:e2e
```

Browser tests start their own backend with a disposable `.e2e/civic.db` SQLite database and frontend
on port 5174, so the LAN frontend can stay running. The suite covers registration,
profile persistence, recommendations, saved tasks, logout/login, and layout overflow at 360, 1440, and 1920 pixels.

## Milestone boundaries

Implemented: volunteer authentication and private persisted profiles; operator source
configuration; manual atomic GitHub/GitLab imports; explained ranked recommendations;
search, metadata filters, sorting and pagination; task details and source links;
private saved lists; validation and responsive layouts.

Remaining: claims and participation transitions/history, feedback and adaptive
scoring, repository-scoped maintainer authorization and audited corrections,
notifications, administrative web tools, scheduled imports/backoff, account
deletion/export, backups, production hosting, full accessibility audit and load tests.
Privileged demo-login screens and fake notification/profile data are not part of
the connected application. Production hosting must use HTTPS, `COOKIE_SECURE=true`,
correct `APP_ORIGIN`, a managed database and deployment-specific controls.
Schema creation handles this initial MVP; versioned migrations remain future work.

---

## Earlier backend setup reference

## Getting Started (MAC INSTALLATION) - (WINDOWS -see below)

### Requirements

Before beginning, make sure you have:

- Git

### 1. Clone the project from GitHub

Open a terminal and run:

```bash
git clone https://github.com/tariqkha2023/Civic-issue-Matchmaker.git
```

This downloads the project to your computer and automatically connects your local Git repository to the shared GitHub repository.

Then enter the project folder which already has the following name, and call terminal:

```bash
cd Civic-issue-Matchmaker
```

You can VERIFY the GitHub connection with:

```bash
git remote -v
```

You should see the shared GitHub repository listed as `origin`.

### 2. Run the backend setup script

From the project root (Civic-issue-Matchmaker), run:

```bash
./setup_backend.sh
```

At the end this will:

- check that Python 3.12 is installed
- create a local Python virtual environment named `.venv` if one does not already exist
- install the correct Python packages that are listed in `backend/requirements.txt`

### 3. Activate the virtual environment

After the setup script finishes, (you will be back at the root) enter this to activate the environment manually:

```bash
source backend/.venv/bin/activate
```

Once activated, your terminal should show something such as:

```text
(.venv)
```

This means Python and `pip` (the Python package installer) are now using the project's isolated virtual environment.

### 4. Start the FastAPI backend

Move into the backend folder with this command:

```bash
cd backend
```

Then start the development server using this:

```bash
uvicorn app.main:app --reload
```

You should see a some kind of message showing that Uvicorn is running at:

```text
http://127.0.0.1:8000
```

### 5. Verify that the backend is working

Open this address in your browser:

```text
http://127.0.0.1:8000/health
```

You should receive:

```json
{
  "status": "ok"
}
```

### 6. After every session working on the project: 

To leave the virtual environment, run:

```bash
deactivate
```

## For Future Sessions working on the project

Before starting work, enter the project master folder and get the latest changes from GitHub,
(that is, any updates from everyone collaborating):

```bash
cd Civic-issue-Matchmaker
git pull
```

Then activate the backend environment:

```bash
source backend/.venv/bin/activate
```

Start the backend:

```bash
cd backend
uvicorn app.main:app --reload
```


## Basic Git Workflow

Before starting work:

```bash
git pull
```

After making changes:

```bash
git add .
git commit -m "Describe your changes"
git push
```





--------------------------------------------





## Windows Backend Setup

### 1. Clone the project from GitHub

Open PowerShell and run:

```powershell
git clone https://github.com/tariqkha2023/Civic-issue-Matchmaker.git
```

Then enter the project root folder with:

```powershell
cd Civic-issue-Matchmaker
```

You can verify the GitHub connection with:

```powershell
git remote -v
```

You should see the shared GitHub repository listed as `origin`.

### 2. Run the Windows backend setup script

From the project root, run:

```powershell
.\setup_backend.ps1
```

This will:

- check that Python 3.12 is installed
- create a local Python virtual environment named `.venv` if one does not already exist
- install the required Python packages listed in `backend\requirements.txt`

### If PowerShell blocks the setup script

If PowerShell reports that script execution is disabled, run this and then try the setup script again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This change only applies to the current PowerShell session.

Then try again, run:

```powershell
.\setup_backend.ps1
```

### 3. Activate the virtual environment

After the setup script finishes, (back at the root folder) activate the environment manually:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Once activated, your PowerShell prompt should show something such as:

```text
(.venv)
```

This means Python and `pip` (pythong package installer) are now using the project's isolated virtual environment.

### 4. Start the FastAPI backend

Move into the backend folder with:

```powershell
cd backend
```

Then start the development server with:

```powershell
uvicorn app.main:app --reload
```

Uvicorn should start and display an address such as:

```text
http://127.0.0.1:8000
```

### 5. Verify that the backend is working

Open this address in your browser:

```text
http://127.0.0.1:8000/health
```

You should receive:

```json
{
  "status": "ok"
}
```

### 6. Everytime you are finished with a session working on the project

To leave the virtual environment, run:

```powershell
deactivate
```

## For Future working sessions

Before starting work, enter the project root folder and get the latest changes from GitHub:

```powershell
cd Civic-issue-Matchmaker
git pull
```

Then activate the virtual environment:

```powershell
.\backend\.venv\Scripts\Activate.ps1
```

Start the backend:

```powershell
cd backend
uvicorn app.main:app --reload
```



--------------------------------------------------------------------------------


## Updating an Existing Backend Setup

Use these instructions AFTER you already completed the original backend setup 

### Prerequisite

"Docker Desktop" MUST be installed and running before using the update script.
Confirm that it is indeed installed, becuase you must open it first, and verify in terminal that it is working

Verify Docker Installation with:

```bash
docker --version
docker compose version
```

---

### Mac / Linux

From the project root, run:

```bash
git pull
./update_backend.sh
```

The update script will automatically:

- reuse the existing Python virtual environment
- install any new backend dependencies
- create `backend/.env` if it does not already exist
- start the PostgreSQL development database with Docker Compose
- run Ruff checks
- run the backend tests



### Windows PowerShell

From the project root folder/directory, run:

```powershell
git pull
.\update_backend.ps1
```

The update script will automatically:

- reuse the existing Python virtual environment
- install any new backend dependencies
- create `backend\.env` if it does not already exist
- start the PostgreSQL development database with Docker Compose
- run Ruff checks
- run the backend tests



## Verify the Backend..... with..

### Mac / Linux

From the project root:

```bash
source backend/.venv/bin/activate
cd backend
uvicorn app.main:app --reload
```

### Windows PowerShell

From the project root:

```powershell
backend\.venv\Scripts\Activate.ps1
cd backend
uvicorn app.main:app --reload
```


### Backend Health Check

Open browser::


http://127.0.0.1:8000/health

Expected response:

```json
{"status":"ok"}
```

### Database Health Check

Open browser:

http://127.0.0.1:8000/health/db


Expected response:

```json
{"database":"ok"}
```

If both endpoints return the expected responses, the FastAPI backend and PostgreSQL development database are working correctly.


### Account roles and the presentation demo

Public registration creates a **Volunteer** account. Volunteers can discover, save,
claim, release, and mark civic tasks complete, then review their private Participation
history. A database constraint permits only one active volunteer claim per task.
Completing a contribution records participation; it does not close the source issue.

**Maintainers** get a Manage issues workspace for repositories assigned by an
administrator. They can correct skills, civic topics, difficulty, and estimated hours.
Corrections are stored separately from original source metadata and recorded in the
audit log; discovery and matching use the corrected values.

**Administrators** get an Administration workspace for assigning roles and maintainer
repositories, enabling/disabling sources, and reviewing recent audit activity.
Every role retains volunteer access. The last administrator cannot be demoted.
Privileged access is checked on the server, including repository-level assignments.

To create presentation accounts and seed the fictional civic repository, run from
`backend` with the same database configuration as the server:

```sh
.venv/bin/python -m app.bootstrap
```

This prints a separately generated password for each new account:
`volunteer@civic.demo`, `maintainer@civic.demo`, and `administrator@civic.demo`.
Passwords are stored as hashes. Rerunning preserves existing accounts and does not
reset passwords. Keep the printed credentials for the presentation.
The bootstrap command is an explicit local setup operation, not a public API.

The application applies additive schema version 1 at startup, introducing role,
repository-access, active-claim, history, metadata-correction, and audit tables
without replacing existing users or issues.

### Architecture and current scope

The responsive React client is the presentation layer. `app/main.py` and
`app/application.py` handle HTTP validation and coordinate requests. `app/accounts.py`,
`app/tasks.py`, `app/discovery.py`, `app/services.py`, `app/matching.py`, and existing
connector/ingestion modules contain domain operations. `app/store.py` and
`app/migrations.py` define relational persistence and additive schema initialization.

This is the agreed approximate 50% demonstration scope. The local fake repository
remains the presentation source. Scheduled scanning, live repository integration,
feedback-driven matching, notifications/email, and advanced administration/settings
are deferred. Existing external connector code is retained for later integration.
