# Teammate setup and data sharing

Group 26 — Civic Issue Matchmaker

## What is ready today

Follow the [README quick setup](../README.md#quick-local-setup) for macOS, Linux or Windows PowerShell. It covers Python/Node installation requirements, SQLite configuration, account creation, both servers and LAN access.

The current local `feat/github-issue-transition` branch includes the AI/matching/removal implementation in local commits. Before distributing a branch, use [the developer handoff](DEVELOPER_HANDOFF.md) to review its implementation and pending public-data distribution work.

## What a teammate needs

- Python 3.11+; Node.js 18+ (22 recommended); npm.
- The reviewed implementation branch.
- A new local `backend/.env` copied from `.env.example`; never share an operator's populated `.env`.
- Two terminals, one for the backend and one for Vite.
- Their own local database and accounts. Bootstrap prints fresh random demo passwords once. The fixed demo email addresses identify roles, not shared passwords.

| Email | Role |
|---|---|
| `volunteer@civic.demo` | Contributor |
| `maintainer@civic.demo` | Curator |
| `administrator@civic.demo` | Administrator |

## Important: imported data is currently local only

This host has downloaded all five GitHub trackers and is enriching open issues. **That data is not in Git yet.** Cloning the current committed branch does not reproduce the populated demo.

At present, a fresh setup starts without those issues, and its worker must download them. An operator `GITHUB_TOKEN` raises the public-read quota; initial issues publish only when each complete tracker scan finishes. AI extraction is a separate explicit command using an operator `OPENROUTER_API_KEY`; browsing never needs an AI call once metadata is cached.

For an offline setup, set `ENABLE_WORKER=false`. Without a supplied public snapshot, however, a fresh offline database has no imported issues. A data-import command is still pending; do not look for a nonexistent seed file or command.

## Planned easy handoff

The requested next deliverable is a public-only, versioned data snapshot and a safe restore command. It should let teammates:

1. Clone and install dependencies.
2. Configure a local SQLite database with source scanning initially disabled.
3. Restore the included public GitHub issues and cached AI requirements.
4. Bootstrap their own accounts and save their generated passwords.
5. Launch the two servers and use a populated Discover without GitHub/OpenRouter keys.
6. Optionally configure their own operator credentials later to refresh data.

The snapshot must include the AI prompt/model/context needed to preserve valid caches. Refreshing it must preserve existing private accounts and activity. [The handoff](DEVELOPER_HANDOFF.md#next-work-teammate-ready-public-data-distribution) gives implementation requirements.

## Do not distribute the live database

`backend/civic-dev.db` also holds password hashes, sessions, private messages and activity. Private backups contain the same information. Neither belongs in Git or a group setup archive. The public snapshot must be generated from an explicit allowlist of public fields/tables.

## First-run smoke check

After code and public-data distribution are complete:

- Sign in as each demo role using passwords generated on that machine.
- Confirm Projects contains the five sources and imported data.
- Save a profile, inspect Discover's score explanations and AI stated/inferred labels.
- Track an issue, remove the accidental tracking entry, and confirm it can be tracked again.
- Confirm curator edits and administrator progress controls are available only to the right roles.
- Restart both servers and confirm data persists.
- Confirm this works with both operator API keys absent and scanning disabled.

These are the handoff acceptance steps; snapshot-based setup has **not** been verified yet.
