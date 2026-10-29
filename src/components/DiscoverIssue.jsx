import React, { useEffect, useRef } from 'react';
import { issueSummary } from '../issueSummary';

const time = t => t ? new Date(t * 1000).toLocaleString() : 'Not synchronized yet';

export default function DiscoverIssue({ task: t, expanded, busy, open, action, explanation, setExplanation }) {
  const heading = useRef(null);
  useEffect(() => { if (expanded) heading.current?.focus(); }, [expanded]);
  const meta = t.metadata;
  const excerpt = issueSummary(t.description);
  const inferred = meta.skills.filter(s => meta.skill_weights?.[s] === 0.5);
  const assessed = meta.skills.filter(s => !inferred.includes(s));
  return <article className="panel taskCard discoverIssue">
    <div className="projectContext">
      <span className="eyebrow">Project mission</span>
      <strong>{t.project?.name || t.repository}</strong>
      <p>{t.project?.mission || 'Project mission not provided.'}</p>
    </div>
    <div className="taskHeader"><span className="eyebrow">{t.repository} · {t.upstream?.number ? `GitHub #${t.upstream.number}` : 'Archived local record'}</span><span className="issueState">{t.status || 'State unknown'}</span></div>
    <h2 ref={heading} tabIndex={expanded ? -1 : undefined}>{expanded ? t.title : <button className="titleButton" disabled={busy === t.id} onClick={() => open(t)}>{t.title}</button>}</h2>
    <p className="issueExcerpt">{excerpt || (t.description ? 'No readable prose excerpt. Expand the original issue text for details.' : 'No description supplied.')}</p>
    {excerpt && <p className="excerptLabel">Excerpt from the issue description</p>}
    <dl className="issueFacts">
      <div><dt>Civic cause</dt><dd>{meta.topics.join(', ') || 'Unknown'}</dd></div>
      <div><dt>Technical skills</dt><dd>{assessed.join(', ') || 'Unknown'}{inferred.length > 0 && <span className="muted"> · Additional suggestions in match details</span>}</dd></div>
      <div><dt>Experience</dt><dd>{meta.difficulty || 'Unknown'}</dd></div>
      <div><dt>Estimated effort</dt><dd>{meta.effort == null ? 'Unknown' : `${meta.effort} hours`}</dd></div>
    </dl>
    <p className="assignmentNote">{t.upstream?.assignees?.length ? 'Assigned on GitHub: ' + t.upstream.assignees.join(', ') : 'No GitHub assignee recorded'}. Check the discussion and contribution guide before starting.</p>
    <div className="matchOverview"><strong>{t.score == null ? 'Not enough information to score' : `${t.score}/100 match score`}</strong><p>{t.score == null ? 'Issue-specific skills and your profile skills are both needed. This is not a zero score.' : 'Based on recorded skills, civic interests, experience, and availability. Missing information can lower the score; it does not establish a mismatch.'}</p></div>
    {t.source_error && <p className="msg error">{t.source_error} Showing the previous snapshot.</p>}
    {(!t.source_enabled || t.upstream?.available === false) && <p className="msg info">Source disabled or issue unavailable. Your history is preserved.</p>}
    <div className="taskActions">
      {t.url && <a className="btn primary" href={t.url} target="_blank" rel="noopener noreferrer">Open on GitHub ↗</a>}
      <button className="btn secondary" disabled={busy === t.id || (!t.saved && t.status !== 'open')} onClick={() => action(t,'save')}>{t.saved ? 'Unsave issue' : 'Save issue'}</button>
      <button className="btn secondary" disabled={busy === t.id || t.tracking || t.status !== 'open' || !t.source_enabled || t.upstream?.available === false} onClick={() => action(t,'track')}>{t.tracking ? 'Tracking contribution' : 'Track contribution'}</button>
    </div>
    <details><summary>Match details and source metadata</summary>
      <ul className="explanations">{t.explanations.map((s,i) => <li key={i}>{s}</li>)}</ul>
      <p className="muted">Evidence coverage: {t.coverage == null ? 'Unknown' : `${t.coverage}%`} · {t.metadata_origin}. Coverage describes available evidence, not your suitability.</p>
      <div className="tags">{meta.skills.map(s => <span key={s}>{s}{inferred.includes(s) ? ' · AI inferred' : ''}</span>)}</div>
      {meta.needs_review && <p className="msg info">Source content changed after the curator review. Metadata needs re-review.</p>}
      {meta.ai_evidence?.length > 0 && <section><h3>AI-extracted requirements</h3><p className="muted">Model: {meta.ai_model}. AI suggestions may be mistaken. Inferred skills carry half weight; curator corrections take priority.</p><ul>{meta.ai_evidence.map((e,i)=><li key={i}><strong>{e.skill}</strong> ({e.basis === 'inferred' ? 'AI inferred' : 'AI identified as stated'}): {e.rationale && <span>{e.rationale} </span>}{e.quote && <q>{e.quote}</q>}</li>)}</ul></section>}
      <p className="muted">Original labels: {t.labels.join(', ') || 'None'}. {meta.provenance}</p>
      <p className="muted">Project languages (context, not required issue skills): {(meta.project_languages || t.project?.languages || []).join(', ') || 'Unknown'}.</p>
      {meta.rationale && <p>Curator rationale: {meta.rationale}</p>}
      <p className="freshness">Last successful source update: {time(t.last_successful_scan)}</p>
    </details>
    <details><summary>Original issue text (Markdown)</summary><pre className="originalIssue">{t.description || 'No description supplied.'}</pre></details>
    {expanded && <section className="feedbackBox"><h3>Was this recommendation relevant?</h3><label>Feedback explanation (optional)<textarea value={explanation} maxLength={1000} onChange={e => setExplanation(e.target.value)}/></label><div className="taskActions"><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',true)}>Relevant</button><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',false)}>Not relevant</button></div>{t.feedback && <p className="muted">Your current rating: {t.feedback.relevant ? 'Relevant' : 'Not relevant'}. {t.feedback.explanation}</p>}</section>}
  </article>;
}
