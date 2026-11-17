# Context research in the main application

## Audit (16 November 2026)

The local application contained 3,539 open issues, 2,389 accepted issue-text
interpretations and 1,150 cached rejections. The 20 records in
[data/discovery-reviews.json](../data/discovery-reviews.json) were the only researched
backgrounds; all 20 matched their source text. None of the AI enrichment records had
a background field. The existing enrichment prompt received issue text and short
project metadata, not linked documentation. The missing backgrounds therefore were
not a card-rendering failure. Counts describe that local snapshot, not live GitHub.

This implementation is part of the application backend and real Discover API.
It does not create a separate preview or sample search page. Administration's
**Context research coverage** panel and administrator-only `GET /api/admin/research`
report current coverage, pending interpretation and the latest job's audit record.
The existing issue-text enrichment panel remains independent.

## Data flow

1. `app.research collect` verifies a public GitHub repository, retrieves its README,
   root CONTRIBUTING.md, the first 20 issue comments, and directly linked issues or
   text files in that repository. README/document caches are shared across tasks.
2. Collection stores a bounded evidence bundle in `issue_research`, including the
   original issue, retrieved text, source URLs, retrieval times and limitations.
   This stage uses no OpenRouter requests and needs no API key.
3. Explicit `app.research interpret --budget ...` uses the existing OpenRouter
   integration and model, passing the evidence bundle to a structured research
   prompt. It returns summary, background, motivation, work, skill suggestions and
   uncertainties. Each claim has source citations with exact supporting quotations.
4. Valid results feed the same Discover search, filters, match scoring and cards as
   all other issues. Background is searchable at the existing lower-priority project
   context tier. Unknowns and provenance are not searchable facts. Citation quotes
   and collection limitations remain in expandable details.

The original 20 human-researched explanations retain priority. Existing enrichment
records, original issue text and user data are preserved. Three additive tables store
research documents, issue bundles/results and run history:
`research_documents`, `issue_research`, `research_runs`. No existing table is replaced.

## Evidence and matching

Background may cite project documentation. Summary, motivation and work also need
an original-issue citation, so project-wide features cannot establish task scope.
The validator rejects missing/fabricated quotations and schema violations. It does
not prove that an interpretation is semantically correct; human review remains
necessary, especially for contradictions and implied meaning.

Skills always remain suggestions. They need issue-level quotations plus a skill
name or supported activity pattern; a technology occurring only in project docs
cannot become a task skill. New suggestions carry the existing inferred weight
(0.5); source skills and curator corrections retain precedence. Experience, hours,
and readiness are not generated or added to scoring.

## Operator commands

Run from the repository root with the backend environment installed. Set
`DATABASE_URL` to the **same database used by the running application** before both
steps. Back up an existing database first. The job applies the normal additive
migrations. Do not point it at a disposable preview database if you want results in
the main application.

```sh
# No paid AI calls. Select up to 20 eligible issues across repositories.
PYTHONPATH=backend backend/.venv/bin/python -m app.research collect --limit 20

# Optional explicit selection, using task IDs from your application's database.
PYTHONPATH=backend backend/.venv/bin/python -m app.research collect --task-id 123 --limit 1

# PAID step, only after agreeing on budget and configuring OPENROUTER_API_KEY.
PYTHONPATH=backend backend/.venv/bin/python -m app.research interpret --limit 20 --budget 0.10
```

Do not paste keys into source code or commit them. No key is needed for browsing.
There is no paid action attached to a page load, search, background worker or admin
status request. Jobs select enabled public GitHub sources and open issues, with a
maximum of 100 attempted issues per invocation. Selection rotates through repositories
in descending task-ID order; it is a varied deterministic batch, not a random sample.
Default selection skips issues already covered by the saved human research. Explicit
`--task-id` selection permits collecting those issues for comparison.

Interpretation requires an explicit $0.001–$2 budget. Each request reserves its full
conservative ceiling before submission. The ledger reports reserved ceilings, not
exact invoices. Requests are sequential, capped at 3,000 output tokens and use the
existing provider price caps. Provider failures stop the job and retain the full
reservation because a failed response could still have incurred a charge. A lease
prevents concurrent research jobs. Account spending limits remain a useful extra cap.

## Freshness and retries

Bundles expire after 30 days, measured from their oldest collected source. Source
text, labels, project metadata or research-version changes invalidate a bundle.
Results also require an exact bundle hash and the current model. Reading stale or
malformed research falls back to existing enrichment/source text without network work.
Collection does not automatically retry fresh bundles; interpretation skips already
attempted current bundles, including schema rejections. To explicitly refresh sources
and retry, run `collect --refresh` for the selected IDs, then `interpret` with a budget.
Project-document changes become visible on refresh or expiry, not through continuous
monitoring. A refreshed shared document does not retroactively rewrite saved bundles.

## Current boundaries and rollout

The first collector intentionally fetches only public GitHub API endpoints, without
a credential, redirects, arbitrary hosts or recursive crawling. It does not inspect
external websites, screenshots, attachments, unlinked code, or comments beyond the
first 20. Cross-repository links and missing CONTRIBUTING.md files are not fetched.
Sources are capped at seven retrieval attempts per issue plus repository verification,
128 KB per response and 12,000 characters per source. These omissions are recorded.
An absent document does not become an invented explanation. Anonymous GitHub quotas
may limit collection; failed attempts can be retried in a later explicit run.

Next expansion: curated official documentation hosts, targeted code selection,
more discussion pagination and human-reviewed accuracy evaluation. Do not advertise
this initial collector as having the complete project story.

Research tables persist in the configured application database. The existing public
snapshot importer/exporter still handles its original issue/enrichment schema; it
**does not distribute these new research records**. A public-only research export
with evidence validation is a follow-up before distributing generated research to
teammates; do not share a whole database containing user accounts as a substitute.

Validate a small batch for factual accuracy, newcomer comprehension, useful skill
suggestions and search quality before expanding. Implementation tests use mocked
providers; they demonstrate integration and safeguards, not actual AI quality.

## Discover result tabs

**All results** retains the usual eligibility, filters and pagination. **Researched
results** applies `researched_only=true` before pagination and totals, requiring a
nonempty, source-current background from saved project research or validated cached
AI research. Collected sources without an interpretation do not qualify. Search,
project/skill/cause/status filters and scores work identically in both tabs; switching
tabs preserves filters and resets to page one. Arrow keys, Home and End select tabs.

Cards follow the reviewed examples: plain-language headline, original title,
What this project does, Background, Motivation, Work described, Suggested skills,
and Skills recorded in original metadata. The original-metadata section uses source
skills rather than treating AI or curator additions as original issue metadata.
