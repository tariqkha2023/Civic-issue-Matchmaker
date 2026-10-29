# AI enrichment and match scoring

This describes the current working-tree implementation. See [developer handoff](DEVELOPER_HANDOFF.md) for commit/data-distribution status.

## What the AI does

OpenRouter serves `deepseek/deepseek-v3.2`. The versioned production prompt is in `backend/app/enrichment_prompt.py`, currently `minimal-requirements-v2`.

The model receives public issue title/body/labels (first 14,000 characters combined) and curated public project mission/topics/languages. It does not receive account profiles, credentials, private messages or participation data, and does not calculate fit percentages.

It returns up to four skills, each with:

- a reusable skill name;
- an explicit/inferred basis;
- a rationale specific to the requested change;
- an optional source quote.

The prompt requests the smallest defensible set, excludes merely helpful technologies, and allows inference from the requested change plus project context. Context is not a list of mandatory skills for every issue. Difficulty is requested only when explicitly supported. AI never estimates effort.

Basic JSON/schema validation remains. Inferred skills are **not** discarded for lacking literal keywords or quotes. A model claim marked explicit without a matching source quote is kept but downgraded to inferred. Labels/rationales can still be wrong; matching quotes are not proof that a skill is necessary.

## Why this prompt replaced the original

The original prompt plus strict quote/keyword filters supplied skills for only 3 of a purposive 19-issue comparison sample. Applying no semantic filters to the same original responses supplied skills for 11. The revised prompt and public project context supplied skills for all 19, with zero format errors in that trial.

This was a development comparison, **not an independent accuracy measurement**. Some inferred additions were unnecessary. User-approved handling is visible inference labels, reduced influence, explanations and curator override—not a claim of verified qualifications. Local comparison reports remain ignored in `.local-tools/`.

## When calls happen

Only an explicit operator enrichment run calls OpenRouter:

```bash
# From backend/, with its Python environment active
python -m app.enrichment --limit 50 --budget 0.05
```

`--workers` accepts 1..8; default 4. `--limit` is attempted issues, at most 10,000; `--budget` is at most $2 per invocation. A process lease prevents overlapping jobs. New/changed issues must be processed in another explicit run.

The current initial job uses eight workers and a $1.70 ceiling, after earlier experiments. Check its progress and previous account usage before starting another paid run. A per-run ceiling does not reset the overall user spending target.

Browsing, sign-in, profile changes and hourly GitHub synchronization do not call the AI. Scanning may change issue text and thereby invalidate its cached analysis; the next explicit enrichment run refreshes it.

## Cache and provenance

`IssueEnrichment` stores fields, model, source/context fingerprint, timestamp and conservative cost estimate. `EnrichmentRun` records progress and spend. Source text, project context, model and prompt/extraction version participate in cache validity. Empty and schema-rejected results are also cached; provider failures remain retryable.

Original label-derived metadata is preserved. Valid AI skills are merged; explicit source-label skills retain full weight. Curator corrections take precedence, and curator-approved skills receive full weight. AI suggestions remain visible as suggestions with rationale/quotes.

A distributable snapshot must retain public project context, source text/IDs and enrichment fields/hash/version together. Copying just titles or scores will not preserve the cache. User profiles must never be bundled with public metadata.

The included [public bundle](../data/README.md) carries those values together.
`python -m app.snapshot setup` restores its valid cached requirements before
creating local accounts. `ENABLE_WORKER=false` keeps first launch offline; no
new enrichment requests are made by setup, import or browsing.

## Fixed-scale scoring: evidence-v4

The model that renormalized partial evidence to 100% was replaced because it produced a whole page of indistinguishable 100% matches.

The current score earns points on a **fixed 100-point scale**:

| Factor | Maximum points |
|---|---:|
| Skills | 60 |
| Difficulty versus experience and preference | 20 |
| Civic interests/topics | 15 |
| Explicit effort versus weekly availability | 5 |

A percentage requires at least one assessed issue skill and profile skills. Otherwise the UI shows Limited information.

For each assessed skill, weight is 1 for stated/source/curator-reviewed requirements and 0.5 for AI-inferred requirements. With `N` assessed skills:

```text
skill points = 60 × sum(weights of skills matched by the profile) / N
```

This is equivalent to the code's weighted alignment multiplied by average evidence weight. An inferred matched skill earns half the points of a stated matched skill. Unknown dimensions earn no points and remain unknown; their absence does not establish a mismatch. Points are not renormalized upward.

Topics earn up to 15 proportionally to matching civic interests. Difficulty earns up to 20 using the documented experience/preference comparison in `matching.py`. Explicit effort earns up to 5 as `min(1, available_hours / estimated_hours)`; no AI effort estimate is supplied.

Examples with all assessed skills matching and the topic matching:

| Available metadata | Score |
|---|---:|
| Stated skills and topic only | 75 |
| AI-inferred skills and topic only | 45 |
| Stated skills, topic, matching difficulty | 95 |
| Stated skills, topic, matching difficulty and sufficient explicit time | 100 |

Repository preferences, own relevance feedback and completed activity affect ordering of equal-score results, not the percentage. Ties are legitimate when evidence and alignment are equivalent.

Evidence coverage is the maximum points supported by known metadata, including the inference discount. It is separate from fit: a 45-point ceiling is not a claim that the person fails the unassessed requirements. The UI explains the available evidence ceiling and missing skills. Neither score nor coverage is a calibrated probability of acceptance or successful completion.

## Cost controls and progress

Requests reserve conservative input/output costs before submission, including concurrent in-flight requests. Provider routing caps are $0.35 per million input tokens and $0.60 per million output tokens; output is limited to 1,800 tokens. Actual charges vary with provider/input length; record costs include conservative estimates and should not be advertised as exact billing.

Use Administration → AI issue enrichment or authenticated `GET /api/admin/enrichment` to inspect processed/eligible counts, skill-bearing results, schema rejections, running state and latest run spend. The active local log is `/tmp/civic-enrichment-revised.log`. The UI reports current-prompt valid caches, not all historical attempts.

Set an OpenRouter key/account spending limit as an additional guard. Keep `OPENROUTER_API_KEY` in ignored `backend/.env`; never print or commit it. Teammates with a correctly restored public cache do not need their own AI key to browse.
