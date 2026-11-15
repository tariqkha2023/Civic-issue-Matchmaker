# AI enrichment and match scoring

This describes the current working-tree implementation. See [developer handoff](DEVELOPER_HANDOFF.md) for commit/data-distribution status.

## What the AI does

OpenRouter serves `deepseek/deepseek-v3.2`. The versioned production prompt is in `backend/app/enrichment_prompt.py`, currently `issue-interpretation-v3`.

The model receives public issue title/body/labels (first 14,000 characters combined) and curated public project mission/topics/languages. It does not receive account profiles, credentials, private messages or participation data, and does not calculate fit percentages.

It returns up to four skills, each with:

- a reusable skill name;
- an explicit/inferred basis;
- a rationale specific to the requested change;
- an issue source quote supporting the requested activity (required for new extractions, including inference).

The prompt requests the smallest defensible set, excludes merely helpful technologies, and allows inference from the requested change plus project context. Context is not a list of mandatory skills for every issue. Difficulty is requested only when explicitly supported. AI never estimates effort.

New responses also contain a nullable `interpretation` with:

- `summary` and `objective`: nullable `{text, source_quote}` objects;
- `activities`: up to six source-backed descriptions of requested work;
- `concepts`: up to eight `{text, source_quote, basis}` search terms;
- `uncertainties`: up to six statements of missing or ambiguous information.

The schema bounds lengths, rejects unknown fields, and permits null/empty results.
Interpretation quotes must occur verbatim in the supplied issue text. Unsupported
quotes reject the response; malformed cached interpretations are hidden on read.
A concept absent from its quote is marked inferred. Uncertainties are displayed
but are not searched as if they were facts.

New skills without matching issue evidence are omitted. A quoted skill claim must
also name the skill or a recognized technology anchor to receive explicit weight.
Specific inferred technologies must have an anchor in the quote or be among the
supplied project languages. A small set of activity synonyms can support broader
inference (for example keyboard work → accessibility). Inference still earns half
weight. Unquoted difficulty is discarded. Original source labels and curator
corrections retain precedence. These conservative checks may omit useful inferred
skills; a curator can correct them.

Quote validation establishes traceability, **not semantic proof**: an AI paraphrase
or inference may still be mistaken or misread a negation. The UI labels the output
as AI interpretation, exposes supporting quotes, and keeps the original authoritative.
No new output has been evaluated using paid model calls during this implementation.

## Search and presentation

Search uses the existing SQL candidate query and a final check against valid metadata.
Each whitespace-separated query word must occur somewhere in the allowed fields,
in any order; matching is case-insensitive for ordinary English text. Original title,
body, labels, skills and civic topics remain searchable. Valid cached summaries,
objectives, activities and concepts add vocabulary without an embedding service or
vector database. For example, an issue about keyboard controls can be found using
an AI-supplied related term such as “accessible navigation.” Without such a cached
concept, search does not invent that expansion or call the model.

Only usable, source-current caches reach the final check. Rejected/stale cache text,
provenance, model names, reasoning and uncertainty statements do not create hits.
The response labels a hit as `source`, `interpreted`, or `inferred_concept`; the UI
explains expanded matches. Search terms never become required skills, civic topics,
or additional match points. Discover sorts by match score or recency.
This is bounded lexical retrieval over cached vocabulary, not general semantic search.

Discover uses a cached plain-language summary, objective, requested work and missing
information when available. Evidence and related terms stay expandable. Issues with
older/no AI interpretation keep the deterministic Markdown-cleaned source excerpt,
source metadata, original text disclosure and GitHub link.

## Historical requirements-prompt comparison

The original prompt plus strict quote/keyword filters supplied skills for only 3 of a purposive 19-issue comparison sample. Applying no semantic filters to the same original responses supplied skills for 11. The revised prompt and public project context supplied skills for all 19, with zero format errors in that trial.

This was a development comparison, **not an independent accuracy measurement**. Some inferred additions were unnecessary. User-approved handling is visible inference labels, reduced influence, explanations and curator override—not a claim of verified qualifications. Local comparison reports remain ignored in `.local-tools/`.

## When calls happen

Only an explicit operator enrichment run calls OpenRouter:

```bash
# From backend/, with its Python environment active
python -m app.enrichment --limit 50 --budget 0.05
```

`--workers` accepts 1..8; default 4. `--limit` is attempted issues, at most 10,000; `--budget` is at most $2 per invocation. A process lease prevents overlapping jobs. New/changed issues must be processed in another explicit run.

Before any paid run, check previous account usage and choose a small explicit limit and budget. A per-run ceiling does not reset an overall spending target. No bulk re-enrichment is required to use this version.

Browsing, sign-in, profile changes and hourly GitHub synchronization do not call the AI. Scanning may change issue text and thereby invalidate its cached analysis; the next explicit enrichment run refreshes it.

## Cache and provenance

`IssueEnrichment` stores fields, model, source/context fingerprint, timestamp and conservative cost estimate. `EnrichmentRun` records progress and spend. Source text, project context, model and prompt/extraction version participate in cache validity. Empty and schema-rejected results are also cached; provider failures remain retryable.

The one supported legacy version, `minimal-requirements-v2-production-v1`, keeps
its valid skills/difficulty when the issue, project context and model still match.
Its frozen prompt/schema is retained in [enrichment_prompt_legacy.py](../backend/app/enrichment_prompt_legacy.py).
Legacy caches never supply v3 interpretations. An explicit enrichment run sees the
old hash as upgrade-eligible; it does not silently rewrite hashes. Other version
changes and all source/context edits invalidate cached output. No database schema
migration is needed: interpretation is stored in the existing enrichment JSON.

Snapshot import/export accepts the exact v2 or v3 version/model/prompt combination
and validates source fingerprints against these supported versions. New nested
fields use an explicit public allowlist. The bundled 21,558 issues now include current v3 results for all 3,539 open
issues: 2,389 accepted interpretations and 1,150 cached validation rejections.
Rejected results remain source-derived; they do not automatically retry.

Original label-derived metadata is preserved. Valid AI skills are merged; explicit source-label skills retain full weight. Curator corrections take precedence, and curator-approved skills receive full weight. AI suggestions remain visible as suggestions with rationale/quotes.

A distributable snapshot must retain public project context, source text/IDs and enrichment fields/hash/version together. Copying just titles or scores will not preserve the cache. User profiles must never be bundled with public metadata.

The included [public bundle](../data/README.md) carries those values together.
`python -m app.snapshot setup` restores its valid cached requirements before
creating local accounts. `ENABLE_WORKER=false` keeps first launch offline; no
new enrichment requests are made by setup, import or browsing.

## Alignment and evidence: skills-interests-v5

Match scores use skills (80%) and civic interests (20%). An issue and profile must
both have skills, otherwise the score is unknown. Skill alignment is the sum of
matched skill weights divided by all assessed skill weights: source/stated/reviewed
skills weigh 1 and AI-inferred skills weigh 0.5. Civic alignment is the fraction of
issue topics matching profile interests.

When either side lacks civic-interest data, that factor is omitted and skills
account for the full score. Unknown is not a mismatch. Difficulty, experience,
effort and weekly availability never affect the score. Their stored fields and
legacy API filters remain compatible, but Discover removes those facts, filters
and sort choices. Profile completeness only requires skills and interests.

Evidence availability is separate: 80 times the average skill evidence weight,
plus 20 if issue topics exist. The API retains the `coverage` field for this
metric. Cards explain the inputs under “What this match is based on” inside the
match-score section; the numeric metric stays in advanced details. These are metadata indicators, not calibrated
confidence, task completeness, or guarantees that AI is correct.

For example, matching a single inferred skill without a known civic topic yields
100/100 alignment and evidence availability of 40. Matching a stated skill and topic
yields 100/100 with evidence availability of 100. The explanation distinguishes inferred skills from recorded ones.
Stronger evidence ranks first among equal scores, followed by existing relevance,
completion and repository preferences. Those tie breakers do not add score points.
Search concepts and descriptive prose never add matching points.

## Cost controls and progress

Requests reserve conservative input/output costs before submission, including concurrent in-flight requests. Provider routing caps are $0.35 per million input tokens and $0.60 per million output tokens; output is limited to 3,000 tokens for the larger structured response. Reservations include the serialized schema, prompt, source/context bytes and a framing allowance. Actual charges vary with provider/input length; record costs include conservative estimates and should not be advertised as exact billing.

Use Administration → AI issue enrichment or authenticated `GET /api/admin/enrichment` to inspect processed/eligible counts, skill-bearing results, schema rejections, running state and latest run spend. Processed counts include usable current and supported legacy caches, not every historical attempt.

Set an OpenRouter key/account spending limit as an additional guard. Keep `OPENROUTER_API_KEY` in ignored `backend/.env`; never print or commit it. Teammates with a correctly restored public cache do not need their own AI key to browse.
