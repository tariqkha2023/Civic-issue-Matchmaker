# Civic Issue Matchmaker – Search & Filters

- a search bar and the filter panel (topic, difficulty, required skill, maximum effort, repository, sort by, clear all)
- Login and Register buttons in the top bar (`#/login`, `#/register`)
- the left sidebar from civic-issue-mock, reduced to the **Maintainer** and **Administration** buttons (everything else is empty)
- Maintainer and Administration are locked: clicking either one asks for a username and password first

## Role access (demo credentials)

| Role           | Username     | Password        |
| -------------- | ------------ | --------------- |
| Maintainer     | `maintainer` | `maintainer123` |
| Administration | `admin`      | `admin123`      |

Each role has its own login. Access is kept in memory only, so refreshing the page locks both again; "Sign out" locks the current role.

**These credentials are for demo only.** They live in `src/roles.js` and are checked in the browser, so anyone can read
them in the page's JavaScript. Before real use, replace the check in `src/pages/RoleLogin.jsx` (marked `TODO`) with a call to your backend.

## Run
    npm install
    npm run dev
