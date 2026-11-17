import React, { useEffect, useRef } from 'react';
import { issueSummary } from '../issueSummary';

const time = t => t ? new Date(t * 1000).toLocaleString() : 'Not synchronized yet';

export default function DiscoverIssue({ task: t, profile, expanded, busy, open, action, explanation, setExplanation }) {
  const heading = useRef(null);
  useEffect(() => { if (expanded) heading.current?.focus(); }, [expanded]);
  const meta = t.metadata;
  const interpretation = meta.interpretation;
  const review = t.reviewed_context;
  const questions = t.clarifications?.questions || [];
  const summary = review?.summary || interpretation?.summary?.text;
  const profileSkills = new Set((profile?.skills || []).map(s => s.toLowerCase()));
  const matched = meta.skills.filter(s => profileSkills.has(s.toLowerCase()));
  const missing = meta.skills.filter(s => !profileSkills.has(s.toLowerCase()));
  const suggestions = [...(meta.research_evidence || []), ...(meta.ai_evidence || []).filter(e => !meta.research_evidence?.some(r => r.skill === e.skill))].filter(e => inferredSkill(e.skill));
  function inferredSkill(skill) { return meta.skills.includes(skill) && meta.skill_weights?.[skill] === 0.5; }
  const excerpt = issueSummary(t.description);
  const inferred = meta.skills.filter(s => meta.skill_weights?.[s] === 0.5);
  return <article className="panel taskCard discoverIssue">
    <div className="taskHeader"><span className="eyebrow">{t.repository} · {t.upstream?.number ? `GitHub #${t.upstream.number}` : 'Archived local record'}</span><span className="issueState">{t.status || 'State unknown'}</span></div>
    <h2 ref={heading} tabIndex={expanded ? -1 : undefined}>{expanded ? summary || t.title : <button className="titleButton" disabled={busy === t.id} onClick={() => open(t)}>{summary || t.title}</button>}</h2>
    <p className="originalTitle">Original title: {t.title}</p>
    {!summary && <p className="issueExcerpt">{excerpt || (t.description ? 'No readable prose excerpt. Expand the original issue text for details.' : 'No description supplied.')}</p>}
    <section className="issueInterpretation" aria-label="Task overview">
      <div className="projectContext"><h3>What this project does</h3><p>{review?.project || t.project?.mission || 'Project description not provided.'}</p></div>
      <h3>Background</h3><p>{review?.background || 'Task-specific background is not available yet. The project description above provides general context.'}</p>
      <h3>Motivation</h3>
      <p>{review?.purpose || interpretation?.objective?.text || 'The reason for this change has not been established from the available information.'}</p>
      <h3>Work described</h3>
      {review?.work ? <p>{review.work}</p> : interpretation?.activities?.length > 0 ? <ul>{interpretation.activities.map((item,i) => <li key={i}>{item.text}</li>)}</ul> : <p>A separate breakdown of the work is not available. Check the original issue text for details.</p>}
    </section>
    {t.search_match && <p className="searchReason">{({source: 'Found in original posting', interpreted: 'Found in task description or reviewed metadata', suggested_skill: 'Suggested skill match', inferred_concept: 'Found through AI-inferred related terminology; this is not a confirmed skill requirement.', background: 'Related through project background'})[t.search_match]}{t.search_related_wording ? ' · related wording' : ''}</p>}
    <section className="suggestedSkills" aria-label="Suggested skills"><h3>Suggested skills</h3><p className="muted">These may help with the described work; they are not confirmed requirements.</p><div className="tags">{inferred.length ? inferred.map(s => <span key={s}>{s}</span>) : <p>No task-specific inferred skills available.</p>}</div>{suggestions.length > 0 && <details><summary>Why these skills are suggested</summary>{suggestions.map(e => <div key={e.skill}><h4>{e.skill}</h4><p>{e.rationale}</p>{e.quote && <blockquote>{e.quote}</blockquote>}<p className="muted">{meta.research_evidence?.some(r => r.skill === e.skill) ? 'Saved context research' : 'Cached AI suggestion'}</p></div>)}</details>}</section>
    <section className="recordedSkills"><h3>Skills recorded in original metadata</h3><p>{t.source_skills?.join(', ') || 'None recorded. This does not mean no skills are needed.'}</p></section>
    {questions.length > 0 && <section className="interpretationUncertainty"><h3>What still needs clarification</h3><ul>{questions.map((question,i) => <li key={i}>{question}</li>)}</ul></section>}
    <dl className="issueFacts"><div><dt>Civic cause</dt><dd>{meta.topics.join(', ') || 'Unknown'}</dd></div></dl>
    <p className="assignmentNote">{t.upstream?.assignees?.length ? 'Assigned on GitHub: ' + t.upstream.assignees.join(', ') : 'No GitHub assignee recorded'}. Check the discussion and contribution guide before starting.</p>
    <section className="matchOverview" aria-label="Match score">
      <strong>{t.score == null ? 'Not enough information to score' : `${t.score}/100 match score`}</strong>
      <p>{t.score == null ? 'Issue-specific skills and your profile skills are both needed. This is not a zero score.' : 'How closely your skills and civic interests match the available issue information. A high score does not guarantee this task is right for you.'}</p>
      {t.score != null && profile && <p className="matchSkills">Matched skills: {matched.join(', ') || 'none'}. Not in your profile: {missing.join(', ') || 'none'}.</p>}
      <details className="matchBasis"><summary>What this match is based on</summary>
        <p>{!meta.skills.length ? 'This issue has no assessed skills yet, so we cannot compare it with your profile.' : inferred.length === meta.skills.length ? 'The skills used for matching are all inferred suggestions. Confirm them with the project before relying on the score.' : inferred.length ? 'Matching uses recorded and inferred skills. Inferred suggestions carry half the weight of stated or curator-reviewed skills.' : 'Matching uses recorded issue skills. Check the original issue to confirm what the project needs.'}</p>
        <p>{meta.topics.length ? 'Civic causes also contribute when you have listed interests in your profile.' : 'No civic cause is recorded for this issue, so it cannot contribute to the score.'} Missing information is left out of the calculation. Even a 100/100 match may be based on limited information.</p>
      </details>
    </section>
    {t.source_error && <p className="msg error">{t.source_error} Showing the previous snapshot.</p>}
    {(!t.source_enabled || t.upstream?.available === false) && <p className="msg info">Source disabled or issue unavailable. Your history is preserved.</p>}
    <div className="taskActions">
      {t.url && <a className="btn primary" href={t.url} target="_blank" rel="noopener noreferrer">Open on GitHub ↗</a>}
      <button className="btn secondary" disabled={busy === t.id || (!t.saved && t.status !== 'open')} onClick={() => action(t,'save')}>{t.saved ? 'Unsave issue' : 'Save issue'}</button>
      <button className="btn secondary" disabled={busy === t.id || t.tracking || t.status !== 'open' || !t.source_enabled || t.upstream?.available === false} onClick={() => action(t,'track')}>{t.tracking ? 'Tracking contribution' : 'Track contribution'}</button>
    </div>
    <details><summary>Match details and source metadata</summary>
      <p className="muted">Task explanation: {review?.kind === 'ai_research' ? 'cached AI interpretation of researched sources' : review ? 'saved project research' : summary ? 'AI interpretation' : 'original issue excerpt'}. Check the original posting for current requirements.</p>
      {review?.citations && <section><h3>Research evidence</h3><p className="muted">Generated: {time(review.generated_at)}. Citations establish traceability, not guaranteed accuracy.</p>{['summary', 'background', 'motivation', 'work'].filter(key => review.citations[key]).map(key => <div key={key}><h4>{({summary: 'Task summary', background: 'Background', motivation: 'Motivation', work: 'Work described'})[key]}</h4>{review.citations[key].citations.map((citation,i) => <blockquote key={i}>{citation.quote} <a href={citation.source} target="_blank" rel="noopener noreferrer">Source</a></blockquote>)}</div>)}</section>}
      {t.clarifications?.review_notes?.length > 0 && <section><h3>Review limitations</h3><ul>{t.clarifications.review_notes.map((note,i) => <li key={i}>{note}</li>)}</ul></section>}
      {interpretation && <section><h3>Interpretation evidence</h3><p className="muted">These excerpts ground the interpretation, but do not guarantee it is correct. Related terms do not add matching points.</p>
        <ul>{[interpretation.summary, interpretation.objective, ...(interpretation.activities || [])].filter(Boolean).map((item,i) => <li key={i}>{item.text} — <q>{item.source_quote}</q></li>)}</ul>
        {interpretation.concepts?.length > 0 && <><h3>Related search terms</h3><ul>{interpretation.concepts.map((item,i) => <li key={i}>{item.text} ({item.basis === 'inferred' ? 'AI inferred' : 'source term'}) — <q>{item.source_quote}</q></li>)}</ul></>}
      </section>}
      <ul className="explanations">{t.explanations.map((s,i) => <li key={i}>{s}</li>)}</ul>
      <p className="muted">Evidence availability: {t.coverage == null ? 'Unknown' : `${t.coverage}%`} · {t.metadata_origin}. Coverage describes available evidence, not your suitability.</p>
      <div className="tags">{meta.skills.map(s => <span key={s}>{s}{inferred.includes(s) ? ' · inferred' : ''}</span>)}</div>
      {meta.needs_review && <p className="msg info">Source content changed after the curator review. Metadata needs re-review.</p>}
      {meta.ai_evidence?.length > 0 && <section><h3>AI-extracted requirements</h3><p className="muted">Model: {meta.ai_model}. AI suggestions may be mistaken. Inferred skills carry half weight; curator corrections take priority.</p><ul>{meta.ai_evidence.map((e,i)=><li key={i}><strong>{e.skill}</strong> ({e.basis === 'inferred' ? 'AI inferred' : 'AI identified as stated'}): {e.rationale && <span>{e.rationale} </span>}{e.quote && <q>{e.quote}</q>}</li>)}</ul></section>}
      {review && <section><h3>Context research and sources</h3><p className="muted">{review.provenance} These explanations are interpretations, not confirmed requirements.</p><ul>{[...new Set([review.project_url, ...review.sources])].filter(url => url?.startsWith('https://')).map(url => <li key={url}><a href={url} target="_blank" rel="noopener noreferrer">{url}</a></li>)}</ul></section>}
      <p className="muted">Original labels: {t.labels.join(', ') || 'None'}. {meta.provenance}</p>
      <p className="muted">Project languages (context, not required issue skills): {(meta.project_languages || t.project?.languages || []).join(', ') || 'Unknown'}.</p>
      {meta.rationale && <p>Curator rationale: {meta.rationale}</p>}
      <p className="freshness">Last successful source update: {time(t.last_successful_scan)}</p>
    </details>
    <details><summary>Original issue text (Markdown)</summary><pre className="originalIssue">{t.description || 'No description supplied.'}</pre></details>
    {expanded && <section className="feedbackBox"><h3>Was this recommendation relevant?</h3><label>Feedback explanation (optional)<textarea value={explanation} maxLength={1000} onChange={e => setExplanation(e.target.value)}/></label><div className="taskActions"><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',true)}>Relevant</button><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',false)}>Not relevant</button></div>{t.feedback && <p className="muted">Your current rating: {t.feedback.relevant ? 'Relevant' : 'Not relevant'}. {t.feedback.explanation}</p>}</section>}
  </article>;
}
