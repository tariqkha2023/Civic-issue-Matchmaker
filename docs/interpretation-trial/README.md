# Context and skill discovery pilot

Open `/docs/interpretation-trial/discover.html` on the local Vite server. This is a standalone test version of Discover for the same 20 issues, not a change to the authenticated application or backend scoring.

## Teammate review

From your existing repository checkout, with your own work saved first:

```sh
git fetch origin
git switch feat/context-search-review
npm ci
npm run dev
```

Open the local address printed by Vite and append `/docs/interpretation-trial/discover.html`. For example, if Vite prints `http://localhost:5173/`, open `http://localhost:5173/docs/interpretation-trial/discover.html`.

Only the 20 saved examples are searched. No backend, database setup, API key or AI credits are needed. The larger issue collection has not been reprocessed. Nothing needs to be merged into main to review this page.

Try searching `frontend` with suggested skills enabled, then disable them to compare. Try `potholes` for a background-context match, or combine a civic cause with a skill. Review whether the explanations make sense without project knowledge, the skill suggestions have convincing evidence, and the results fit your query. Report confusing wording and irrelevant matches by GitHub issue number from each result's source link.

The [saved explanations](context-review.json) were researched in the chat, using original issues and linked public documentation. The [suggested skills](suggested-skills.json) have task-specific rationales and verbatim supporting excerpts. They are possibilities, not confirmed requirements. The broad internationalization tracker deliberately has no suggestions until a subtask is selected.

[Filter metadata](sample-metadata.json) was exported on November 13, 2026 through a read-only SQLite connection. It includes only the sample IDs, recorded issue state, assignment category, original skills and existing curated project topics. It contains no user accounts or credentials. Recorded GitHub information may be stale. All sample issues lack original skill metadata; previous AI language guesses are not promoted to confirmed requirements.

The search module checks only designated fields, in this order:

1. Title, summary, motivation, work and recorded skill names.
2. Original issue body.
3. Suggested skill names, when enabled.
4. Background, project purpose and civic topics.

Every query word must match. A small explicit synonym list and word-boundary matching support related wording; this is not embedding-based semantic search. Each result explains the weakest information tier needed to satisfy the query. Project, civic cause, skill, state and assignment filters combine with text search. Results paginate five at a time. Suggestion explanations, uncertainty notes and provenance are not search fields, although original issue text can itself mention unresolved information.

There are no AI calls, database writes, or changes to existing saving, tracking or authentication. Turning off suggested skills affects the search and skill filter; it does not hide the disclosed suggestions on cards. Production integration and user evaluation remain separate work.

The test profile panel lets reviewers select skills and civic interests without authentication. Choices stay in page memory only, reset on refresh, and do not filter or reorder results. Each card shows estimated compatibility using the union of original recorded skills and the researched skill suggestions, deduplicated case-insensitively with equal weight per skill. Skills contribute 80% and civic interests 20% when both factors are available; missing interests or topics normalize to skills alone. Missing profile or task skills yield no score. Nineteen sample issues have inferred skills and can score; the broad internationalization tracker remains unscored. Explanations list matching and missing skills, identify inferences, and distinguish estimates from probabilities of success. The suggested-skills search toggle does not affect scoring. Earlier AI language guesses remain excluded. The backend production scorer is unchanged.

Validation: `node --test docs/interpretation-trial/discovery-search.test.js docs/interpretation-trial/profile-match.test.js`. The preview needs HTTP hosting for its local JSON/module imports; use the existing `npm run dev` command.
