import React, { useEffect, useState } from 'react';
import { api } from '../api';

const defaults = { q: '', repository: '', topic: '', skill: '', difficulty: '', max_effort: '', status: 'open', sort: 'compatibility', assignment: '' };
const time = t => t ? new Date(t * 1000).toLocaleString() : 'Not synchronized yet';

export default function Home({ savedOnly, selectedProject = '', go, onError }) {
  const [filters, setFilters] = useState({ ...defaults, repository: selectedProject });
  const [projects, setProjects] = useState([]), [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1), [reload, setReload] = useState(0), [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState(null), [error, setError] = useState(''), [message, setMessage] = useState('');
  const [explanation, setExplanation] = useState('');
  const fail = e => { setError(e.message); if (e.status === 401) onError(e); };
  useEffect(() => { api('/projects').then(setProjects).catch(fail); }, []);
  useEffect(() => {
    let active = true; setLoading(true); setError('');
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ page, ...Object.fromEntries(Object.entries(filters).filter(([,v]) => v !== '')) });
        const result = await api(savedOnly ? '/me/saved' : '/recommendations?' + params);
        if (active) setData(savedOnly ? { items: result, total: result.length } : result);
      } catch (e) { if (active) fail(e); } finally { if (active) setLoading(false); }
    }, 200);
    return () => { active = false; clearTimeout(timer); };
  }, [filters, page, savedOnly, reload]);
  const update = (key, value) => { setFilters(f => ({ ...f, [key]: value })); setPage(1); };
  const action = async (task, kind, relevant) => {
    setBusy(task.id); setError(''); setMessage('');
    try {
      if (kind === 'save') {
        await api('/me/saved/' + task.id, { method: task.saved ? 'DELETE' : 'PUT' });
        setMessage(task.saved ? 'Bookmark removed.' : 'Issue saved.');
      } else if (kind === 'track') {
        await api(`/tasks/${task.id}/contributions`, { method: 'POST' });
        setMessage('Contribution tracked locally. Request any GitHub assignment from the source project.');
      } else {
        await api(`/tasks/${task.id}/feedback`, { method: 'PUT', body: { relevant, explanation } });
        setMessage('Feedback saved. Your feedback helps rank equally matched issues.');
      }
      if (detail?.id === task.id) setDetail(await api('/tasks/' + task.id));
      setReload(x => x + 1);
    } catch (e) { fail(e); } finally { setBusy(null); }
  };
  const open = async task => { setError(''); setBusy(task.id); try { setDetail(await api('/tasks/' + task.id)); setExplanation(''); } catch (e) { fail(e); } finally { setBusy(null); } };
  const card = (t, expanded = false) => <article className="panel taskCard" key={t.id}>
    <div className="taskHeader"><span className="eyebrow">{t.repository} {t.upstream?.number ? `· GitHub #${t.upstream.number}` : '· Archived local record'}</span><span className="score">{t.score == null ? 'Limited information' : `${t.score}% fit`}</span></div>
    <h2>{expanded ? t.title : <button className="titleButton" onClick={() => open(t)}>{t.title}</button>}</h2>
    <div className="tags"><span>{t.status}</span><span>{t.upstream?.assignees?.length ? 'Assigned upstream: ' + t.upstream.assignees.join(', ') : 'No upstream assignee recorded'}</span><span>{t.metadata.difficulty || 'Difficulty unknown'}</span><span>{t.metadata.effort == null ? 'Effort unknown' : t.metadata.effort + ' hours'}</span>{t.metadata.skills.map(s => <span key={s}>{s}{t.metadata.skill_weights?.[s] === 0.5 ? ' · AI inferred' : ''}</span>)}{t.metadata.topics.map(s => <span key={'topic'+s}>{s}</span>)}</div>
    <p className={'taskDescription' + (expanded ? ' expanded' : '')}>{t.description || 'No description supplied.'}</p>
    <ul className="explanations">{t.explanations.map((s,i) => <li key={i}>{s}</li>)}</ul>
    <p className="muted">Evidence coverage: {t.coverage ?? 0}% · {t.metadata_origin}. Evidence-backed fit awards matching points out of 100. Missing information limits the score; it does not establish a mismatch.</p>
    {t.metadata.needs_review && <p className="msg info">Source content changed after the curator review. Metadata needs re-review.</p>}
    <p className="freshness">Last successful source update: {time(t.last_successful_scan)}</p>
    {t.source_error && <p className="msg error">{t.source_error} Showing the previous snapshot.</p>}
    {(!t.source_enabled || t.upstream?.available === false) && <p className="msg info">Source disabled or issue unavailable. Your history is preserved.</p>}
    {expanded && t.metadata.ai_evidence?.length > 0 && <section><h3>AI-extracted requirements</h3><p className="muted">Model: {t.metadata.ai_model}. AI suggestions may be mistaken. Inferred skills carry half weight; curator corrections take priority.</p><ul>{t.metadata.ai_evidence.map((e,i)=><li key={i}><strong>{e.skill}</strong> ({e.basis === 'inferred' ? 'AI inferred' : 'AI identified as stated'}): {e.rationale && <span>{e.rationale} </span>}{e.quote && <q>{e.quote}</q>}</li>)}</ul></section>}
    {expanded && <><p className="muted">Original labels: {t.labels.join(', ') || 'None'}. {t.metadata.provenance}</p><p className="muted">Project languages (context, not required issue skills): {(t.metadata.project_languages || []).join(', ') || 'Unknown'}.</p>{t.metadata.rationale && <p>Curator rationale: {t.metadata.rationale}</p>}</>}
    <div className="taskActions">
      {t.url && <a className="btn primary" href={t.url} target="_blank" rel="noopener noreferrer">Open on GitHub ↗</a>}
      <button className="btn secondary" disabled={busy === t.id || (!t.saved && t.status !== 'open')} onClick={() => action(t,'save')}>{t.saved ? 'Unsave issue' : 'Save issue'}</button>
      <button className="btn secondary" disabled={busy === t.id || t.tracking || t.status !== 'open' || !t.source_enabled || t.upstream?.available === false} onClick={() => action(t,'track')}>{t.tracking ? 'Tracking contribution' : 'Track contribution'}</button>
    </div>
    {expanded && <section className="feedbackBox"><h3>Was this recommendation relevant?</h3><label>Feedback explanation (optional)<textarea value={explanation} maxLength={1000} onChange={e => setExplanation(e.target.value)}/></label><div className="taskActions"><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',true)}>Relevant</button><button className="btn secondary" disabled={busy === t.id} onClick={() => action(t,'feedback',false)}>Not relevant</button></div>{t.feedback && <p className="muted">Your current rating: {t.feedback.relevant ? 'Relevant' : 'Not relevant'}. {t.feedback.explanation}</p>}</section>}
  </article>;
  return <><section className="pageHead"><div><span className="eyebrow">CONTRIBUTE TECHNICAL SKILLS TO CIVIC CAUSES</span><h1>{savedOnly ? 'Saved issues' : 'Discover civic-tech issues'}</h1><p>{savedOnly ? 'Your private bookmarks across source projects.' : 'Real GitHub issues, explained matches, and a clear path to contributing.'}</p></div></section><section className="pageBody discovery">
    <p className="demoBanner">GitHub remains authoritative. Local tracking does not reserve an issue, assign you upstream, or guarantee acceptance.</p>
    {message && <p className="msg success" role="status">{message}</p>}{error && <p className="msg error" role="alert">{error} <button className="textButton" onClick={() => setReload(x=>x+1)}>Retry</button></p>}
    {detail ? <><button className="btn secondary" onClick={() => setDetail(null)}>← Back to issues</button>{card(detail,true)}</> : <>
      {!savedOnly && <section className="filters"><div className="filterHead"><strong>Search and filters</strong><button onClick={() => {setFilters(defaults);setPage(1);}}>Clear all</button></div><label>Search<input type="search" value={filters.q} onChange={e => update('q',e.target.value)} placeholder="Search titles, descriptions, and labels"/></label><div className="filterGrid">
        <label>Project<select value={filters.repository} onChange={e=>update('repository',e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.path}>{p.name}</option>)}</select></label>
        <label>Civic topic<input value={filters.topic} onChange={e=>update('topic',e.target.value)} placeholder="e.g. Open mapping"/></label>
        <label>Required skill<input value={filters.skill} onChange={e=>update('skill',e.target.value)} placeholder="e.g. javascript"/></label>
        <label>Difficulty<select value={filters.difficulty} onChange={e=>update('difficulty',e.target.value)}><option value="">Any difficulty</option>{['Beginner','Intermediate','Advanced'].map(d=><option key={d}>{d}</option>)}</select></label>
        <label>Maximum estimated hours<input type="number" min="0" max="10000" value={filters.max_effort} onChange={e=>update('max_effort',e.target.value)}/></label>
        <label>Source state<select value={filters.status} onChange={e=>update('status',e.target.value)}><option value="open">Open</option><option value="closed">Closed</option><option value="all">All states</option></select></label>
        <label>Upstream assignment<select value={filters.assignment} onChange={e=>update('assignment',e.target.value)}><option value="">Any assignment</option><option value="unassigned">Unassigned</option><option value="assigned">Assigned</option></select></label>
        <label>Sort<select value={filters.sort} onChange={e=>update('sort',e.target.value)}><option value="compatibility">Best fit</option><option value="recency">Recently discovered</option><option value="difficulty">Lowest difficulty</option><option value="effort">Lowest effort</option></select></label>
      </div><p className="muted">Topic/skill filters use exact names. An effort limit excludes unknown estimates. Filters do not restrict ingestion.</p></section>}
      {!savedOnly && data.profile_incomplete && <p className="msg info">Add technical skills, civic interests, and availability for more useful matching. <button className="textButton" onClick={()=>go('profile')}>Edit profile</button></p>}
      {loading ? <p role="status">Loading issues…</p> : <><p className="resultCount">{data.total} {savedOnly ? 'saved issues' : 'matching issues'}</p><div className="taskList">{data.items.map(t=>card(t))}</div>{!data.items.length && <div className="panel emptyState"><h2>{savedOnly ? 'No saved issues yet' : 'No issues found'}</h2><p>Clear filters or inspect Projects for synchronization progress. Initial scans publish only after all pages have been collected.</p><button className="btn secondary" onClick={()=>go('repository')}>View projects</button></div>}{!savedOnly && data.total>12 && <nav className="pagination" aria-label="Results pages"><button className="btn secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {Math.ceil(data.total/12)}</span><button className="btn secondary" disabled={page*12>=data.total} onClick={()=>setPage(p=>p+1)}>Next</button></nav>}</>}
    </>}
  </section></>;
}
