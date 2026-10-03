import React, { useEffect, useState } from 'react';
import { api } from '../api';
import AddTask from './AddTask';
import { DEMO_REPOSITORY, DEMO_NAME } from '../demo';

const defaults = { q: '', repository: '', topic: '', skill: '', difficulty: '', max_effort: '', status: 'open', sort: 'compatibility' };
const date = value => value ? new Date(value * 1000).toLocaleString() : 'Never synced';

export default function Home({ savedOnly, repositoryOnly, go, onError }) {
  const [adding, setAdding] = useState(false);
  const initialFilters = { ...defaults, ...(repositoryOnly ? { repository: DEMO_REPOSITORY, sort: 'recency' } : {}) };
  const [filters, setFilters] = useState(initialFilters);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [detail, setDetail] = useState(null);
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState('');
  useEffect(() => {
    let active = true;
    api('/repositories').then(value => { if (active) setRepos(value); }).catch(e => { if (active) { setError(e.message); if (e.status === 401) onError(e); } });
    return () => { active = false; };
  }, [reload]);
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ page, ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== '')) });
        const result = await api(savedOnly ? '/me/saved' : '/recommendations?' + params);
        if (active) setData(savedOnly ? { items: result, total: result.length } : result);
      } catch (e) { if (active) { setError(e.message); if (e.status === 401) onError(e); } }
      finally { if (active) setLoading(false); }
    }, 200);
    return () => { active = false; clearTimeout(timer); };
  }, [filters, page, savedOnly, reload]);
  const update = (key, value) => { setFilters(f => ({ ...f, [key]: value })); setPage(1); };
  const toggleSave = async task => {
    setBusy(task.id); setMessage('');
    try {
      await api('/me/saved/' + task.id, { method: task.saved ? 'DELETE' : 'PUT' });
      setMessage(task.saved ? 'Task removed from your saved list.' : 'Task saved.');
      setReload(v => v + 1);
      if (detail?.id === task.id) setDetail(t => ({ ...t, saved: !task.saved }));
    } catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(null); }
  };
  const participate = async (task, action) => {
    setBusy(task.id); setError(''); setMessage('');
    try {
      const updated = await api(`/tasks/${task.id}/participation`, { method: 'POST', body: { action } });
      setReload(v => v + 1);
      if (detail?.id === task.id) setDetail({ ...updated, saved: task.saved });
      setMessage(action === 'claimed' ? 'Task claimed. View it in Participation.' : action === 'completed' ? 'Contribution marked complete.' : 'Task released. Another volunteer can now claim it.');
    } catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(null); }
  };
  const openDetail = async id => {
    setBusy(id);
    try { setDetail(await api('/tasks/' + id)); }
    catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(null); }
  };
  const taskCard = (task, expanded = false) => <article className="panel taskCard" key={task.id}>
    <div className="taskHeader"><span className="eyebrow">{task.source === 'demo' ? 'Demo repository' : task.source === 'manual' ? 'Manually added' : task.source} · {task.source === 'demo' ? DEMO_NAME : task.repository}</span><span className="score">{task.score == null ? 'Unscored' : `${task.score}% match`}</span></div>
    <h2>{expanded ? task.title : <button className="titleButton" onClick={() => openDetail(task.id)} disabled={busy === task.id}>{task.title}</button>}</h2>
    <div className="tags"><span>Issue #{task.id}</span><span>{task.status}</span><span>{task.metadata.difficulty || 'Difficulty unknown'}</span><span>{task.metadata.effort == null ? 'Effort unknown' : `${task.metadata.effort} hours`}</span>{task.metadata.skills.map(s => <span key={s}>{s}</span>)}{task.metadata.topics.map(t => <span key={'topic-' + t}>{t}</span>)}</div>
    <p className={expanded ? 'taskDescription expanded' : 'taskDescription'}>{task.description || 'No description provided.'}</p>
    {task.metadata.location && <p className="issueLocation">📍 {task.metadata.location}</p>}
    {expanded && task.metadata.organizer && <p className="muted">Organizer: {task.metadata.organizer}</p>}
    <ul className="explanations">{task.explanations.map((text, i) => <li key={i}>{text}</li>)}</ul>
    {expanded && <><p className="muted">Labels: {task.labels.join(', ') || 'None supplied'}</p><p className="muted">{task.metadata.provenance}</p></>}
    <p className="freshness">{['manual', 'demo'].includes(task.source) ? `Added: ${date(task.first_seen)}` : `Last successful sync: ${date(task.last_successful_scan)}`}</p>
    {task.source_error && <p className="msg error">{task.source_error} Displaying cached data.</p>}
    <div className="taskActions">{task.participation?.claimed_by_me ? <><button className="btn primary" disabled={busy === task.id} onClick={() => participate(task, 'completed')}>Mark complete</button><button className="btn secondary" disabled={busy === task.id} onClick={() => participate(task, 'released')}>Release task</button></> : <button className="btn primary" disabled={busy === task.id || task.status !== 'open' || task.participation?.claimed || task.participation?.completed_by_me} onClick={() => participate(task, 'claimed')}>{task.participation?.completed_by_me ? 'Completed by you' : task.participation?.claimed ? 'Already claimed' : 'Claim task'}</button>}{task.url && <a className="btn primary" href={task.url} target="_blank" rel="noopener noreferrer">Open source issue ↗</a>}<button className="btn secondary" disabled={busy === task.id || (!task.saved && task.status !== 'open')} onClick={() => toggleSave(task)}>{busy === task.id ? 'Please wait…' : task.saved ? 'Unsave task' : 'Save task'}</button></div>
  </article>;
  return <><section className="pageHead"><div><span className="eyebrow">{savedOnly ? 'YOUR SHORTLIST' : repositoryOnly ? 'LOCAL DEMO REPOSITORY' : 'MAKE A CIVIC CONTRIBUTION'}</span><h1>{savedOnly ? 'Saved tasks' : repositoryOnly ? DEMO_NAME : 'Discover your next task'}</h1><p>{savedOnly ? 'Return to work you want to explore.' : repositoryOnly ? 'Browse the community issue collection and add new issues for the demo.' : 'Find community issues that fit your skills, interests, and available time.'}</p></div>{!savedOnly && <button className="btn primary" onClick={() => { setAdding(true); setDetail(null); setMessage(''); }}>Create issue</button>}</section>
    <section className="pageBody discovery">
      {!savedOnly && <div className="demoBanner"><div><strong>Community Care demo</strong><p>Fictional civic issues for the presentation. Issues are stored in our local demo repository.</p></div>{!repositoryOnly && <button className="btn secondary" onClick={() => go('repository')}>View repository</button>}</div>}
      {adding ? <AddTask onError={onError} onCancel={() => setAdding(false)} onCreated={() => { setAdding(false); setFilters({ ...initialFilters, sort: 'recency' }); setPage(1); setReload(v => v + 1); setMessage('Issue created. It is now available in Discover and the demo repository.'); }}/> : detail ? <><button className="btn secondary" onClick={() => setDetail(null)}>← Back to tasks</button>{taskCard(detail, true)}</> : <>
      {!savedOnly && <section className="filters" aria-label="Recommendation filters"><div className="filterHead"><strong>Search and filters</strong><button onClick={() => { setFilters(initialFilters); setPage(1); }}>Clear all</button></div>
        <label>Search<input type="search" value={filters.q} onChange={e => update('q', e.target.value)} placeholder="Search titles, descriptions, and labels"/></label>
        <div className="filterGrid">
          <label>Repository<select disabled={repositoryOnly} value={filters.repository} onChange={e => update('repository', e.target.value)}><option value="">Any repository</option>{[...new Set(repos.map(r => r.path))].map(r => <option key={r} value={r}>{r === DEMO_REPOSITORY ? DEMO_NAME : r}</option>)}</select></label>
          <label>Topic<input value={filters.topic} onChange={e => update('topic', e.target.value)} placeholder="e.g. Transportation"/></label>
          <label>Required skill<input value={filters.skill} onChange={e => update('skill', e.target.value)} placeholder="e.g. Communication"/></label>
          <label>Difficulty<select value={filters.difficulty} onChange={e => update('difficulty', e.target.value)}><option value="">Any difficulty</option>{['Beginner', 'Intermediate', 'Advanced'].map(v => <option key={v}>{v}</option>)}</select></label>
          <label>Maximum estimated hours<input type="number" min="0" max="10000" value={filters.max_effort} onChange={e => update('max_effort', e.target.value)} placeholder="Any effort"/></label>
          <label>Status<select value={filters.status} onChange={e => update('status', e.target.value)}><option value="open">Open</option><option value="closed">Closed</option><option value="all">All statuses</option></select></label>
          <label>Sort<select value={filters.sort} onChange={e => update('sort', e.target.value)}>{[['compatibility', 'Best match'], ['recency', 'Most recently discovered'], ['difficulty', 'Lowest difficulty'], ['effort', 'Lowest effort']].map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
        </div><p className="muted">Effort filters exclude tasks with unknown estimates. Topics and skills use exact names from task metadata.</p>
      </section>}
      {!savedOnly && data.profile_incomplete && <div className="msg info">Complete your skills, interests, and availability for more useful matches. <button className="textButton" onClick={() => go('profile')}>Edit profile</button></div>}
      {!savedOnly && repos.filter(r => r.error).map(r => <p className="msg error" key={r.id}>{r.path}: {r.error} Last successful sync: {date(r.last_successful_scan)}.</p>)}
      {loading ? <p role="status">Loading tasks…</p> : !error && <><p className="resultCount">{data.total} {savedOnly ? 'saved tasks' : 'matching tasks'}</p>{data.items.length ? <div className="taskList">{data.items.map(t => taskCard(t))}</div> : <div className="panel emptyState"><h2>{savedOnly ? 'Your shortlist starts here' : 'No tasks found'}</h2><p>{savedOnly ? 'Save an open task from Discover to keep it here.' : 'Create a community issue to get started, or clear your filters to see more tasks.'}</p>{savedOnly && <button className="btn primary" onClick={() => go('home')}>Discover tasks</button>}</div>}
        {!savedOnly && data.total > 12 && <nav className="pagination" aria-label="Results pages"><button className="btn secondary" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button><span>Page {page} of {Math.ceil(data.total / 12)}</span><button className="btn secondary" disabled={page * 12 >= data.total} onClick={() => setPage(p => p + 1)}>Next</button></nav>}</>}
      </>}
      {error && <div className="msg error" role="alert">{error} <button className="textButton" onClick={() => setReload(v => v + 1)}>Retry</button></div>}
      {message && <p className="msg success" role="status">{message}</p>}
      <p className="muted disclaimer">Recommendations are guidance, not a guarantee of acceptance or success. Demo issues are fictional; adding or saving one does not arrange a real volunteer placement.</p>
    </section></>;
}
