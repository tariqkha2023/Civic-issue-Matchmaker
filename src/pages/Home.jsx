import React, { useEffect, useState } from 'react';
import { api } from '../api';
import DiscoverIssue from '../components/DiscoverIssue';

const defaults = { q: '', repository: '', topic: '', skill: '', difficulty: '', max_effort: '', status: 'open', sort: 'compatibility', assignment: '' };

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
  const card = (t, expanded = false) => <DiscoverIssue key={t.id} task={t} expanded={expanded} busy={busy} open={open} action={action} explanation={explanation} setExplanation={setExplanation}/>;
  return <><section className="pageHead discoveryHead"><div><span className="eyebrow">CONTRIBUTE TECHNICAL SKILLS TO CIVIC CAUSES</span><h1>{savedOnly ? 'Saved issues' : 'Discover civic-tech issues'}</h1><p>{savedOnly ? 'Your private bookmarks across source projects.' : 'Use your technical skills to support public-interest projects. Find an individual GitHub task within a larger civic mission, then check with the project before starting.'}</p></div></section><section className="pageBody discovery">
    <div className="discoveryGuide"><p><strong>1. Find a cause</strong><span>Explore projects serving communities.</span></p><p><strong>2. Review a task</strong><span>Check the issue, skills, and discussion.</span></p><p><strong>3. Contribute on GitHub</strong><span>Save here or track your own progress.</span></p></div><p className="trackingNote">GitHub remains authoritative. Local tracking does not reserve an issue, assign you upstream, or guarantee acceptance.</p>
    {message && <p className="msg success" role="status">{message}</p>}{error && <p className="msg error" role="alert">{error} <button className="textButton" onClick={() => setReload(x=>x+1)}>Retry</button></p>}
    {detail ? <><button className="btn secondary" onClick={() => setDetail(null)}>← Back to issues</button>{card(detail,true)}</> : <>
      {!savedOnly && <section className="filters discoverFilters" aria-label="Search and filters"><div className="filterHead"><strong>Find an opportunity</strong><button onClick={() => {setFilters(defaults);setPage(1);}}>Clear all</button></div><label>Search<input type="search" value={filters.q} onChange={e => update('q',e.target.value)} placeholder="Search titles, descriptions, and labels"/></label><div className="filterGrid">
        <label>Civic cause<input value={filters.topic} onChange={e=>update('topic',e.target.value)} placeholder="e.g. Open mapping"/></label>
        <label>Technical skill<input value={filters.skill} onChange={e=>update('skill',e.target.value)} placeholder="e.g. javascript"/></label>
        <label>Experience level<select value={filters.difficulty} onChange={e=>update('difficulty',e.target.value)}><option value="">Any experience level</option>{['Beginner','Intermediate','Advanced'].map(d=><option key={d}>{d}</option>)}</select></label>
        <label>Project<select value={filters.repository} onChange={e=>update('repository',e.target.value)}><option value="">All projects</option>{projects.map(p=><option key={p.id} value={p.path}>{p.name}</option>)}</select></label>
        <label>Maximum estimated hours<input type="number" min="0" max="10000" value={filters.max_effort} onChange={e=>update('max_effort',e.target.value)}/></label>
        <label>GitHub issue state<select value={filters.status} onChange={e=>update('status',e.target.value)}><option value="open">Open</option><option value="closed">Closed</option><option value="all">All states</option></select></label>
        <label>GitHub assignment<select value={filters.assignment} onChange={e=>update('assignment',e.target.value)}><option value="">Any assignment</option><option value="unassigned">No assignee recorded</option><option value="assigned">Assigned</option></select></label>
        <label>Sort<select value={filters.sort} onChange={e=>update('sort',e.target.value)}><option value="compatibility">Highest match score</option><option value="recency">Recently discovered</option><option value="difficulty">Lowest difficulty</option><option value="effort">Lowest effort</option></select></label>
      </div><p className="muted">Civic cause and skill filters use exact names from issue metadata, including assessed skill suggestions. Experience and effort filters exclude unknown values. Open or unassigned does not mean ready to start.</p></section>}
      {!savedOnly && data.profile_incomplete && <p className="msg info">Add technical skills, civic interests, and availability for more useful matching. <button className="textButton" onClick={()=>go('profile')}>Edit profile</button></p>}
      {loading ? <p role="status">Loading issues…</p> : <><p className="resultCount" role="status">{data.total} {savedOnly ? 'saved issues' : 'matching issues'}</p><div className="taskList">{data.items.map(t=>card(t))}</div>{!data.items.length && <div className="panel emptyState"><h2>{savedOnly ? 'No saved issues yet' : 'No issues found'}</h2><p>Clear filters or inspect Projects for synchronization progress. Initial scans publish only after all pages have been collected.</p><button className="btn secondary" onClick={()=>go('repository')}>View projects</button></div>}{!savedOnly && data.total>12 && <nav className="pagination" aria-label="Results pages"><button className="btn secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {Math.ceil(data.total/12)}</span><button className="btn secondary" disabled={page*12>=data.total} onClick={()=>setPage(p=>p+1)}>Next</button></nav>}</>}
    </>}
  </section></>;
}
