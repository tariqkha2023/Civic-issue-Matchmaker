import React, { useEffect, useState } from 'react';
import { api } from '../api';

export default function Maintainer({ onError }) {
  const [tasks, setTasks] = useState(null), [editing, setEditing] = useState(null), [form, setForm] = useState({}), [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  const [q,setQ]=useState(''),[page,setPage]=useState(1),[total,setTotal]=useState(0);
  useEffect(() => { let active=true; const timer=setTimeout(()=>api('/curator/issues?'+new URLSearchParams({q,page})).then(d=>{if(active){setTasks(d.items);setTotal(d.total);}}).catch(e=>{if(active){setError(e.message);if(e.status===401)onError(e);}}),200);return()=>{active=false;clearTimeout(timer);}; }, [q,page]);
  const edit = t => { setEditing(t); setMessage(''); setForm({ skills: t.metadata.skills.join(', '), topics: t.metadata.topics.join(', '), difficulty: t.metadata.difficulty || '', effort: t.metadata.effort ?? '', rationale: t.metadata.rationale || '' }); };
  const update = (key, value) => setForm(f => ({ ...f, [key]: value }));
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    const split = value => value.split(',').map(s => s.trim()).filter(Boolean);
    try {
      const updated = await api(`/maintainer/tasks/${editing.id}/metadata`, { method: 'PUT', body: { skills: split(form.skills), topics: split(form.topics), difficulty: form.difficulty || null, effort: form.effort === '' ? null : Number(form.effort), rationale: form.rationale, expected_source_updated_at: editing.upstream?.updated_at || null } });
      setTasks(ts => ts.map(t => t.id === updated.id ? updated : t)); setEditing(null); setMessage('Metadata updated. Source values were preserved and the change was recorded.');
    } catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(false); }
  };
  return <><section className="pageHead"><div><span className="eyebrow">CURATOR WORKSPACE</span><h1>Review metadata</h1><p>Review and correct metadata for your assigned civic-tech repositories.</p></div></section><section className="pageBody discovery">
    {error && <p className="msg error" role="alert">{error}</p>}{message && <p className="msg success" role="status">{message}</p>}
    <label>Search issue titles<input value={q} onChange={e=>{setQ(e.target.value);setPage(1);}}/></label>
    {editing ? <section className="panel form"><h2>{editing.title}</h2><p className="muted">Corrections affect discovery and matching. The original issue metadata remains stored.</p><form onSubmit={submit}>
      {editing.metadata.ai_evidence?.length>0&&<section><h3>AI suggestions and source evidence</h3><ul>{editing.metadata.ai_evidence.map((e,i)=><li key={i}><strong>{e.skill}</strong> ({e.basis || 'explicit'}): {e.rationale} {e.quote && <q>{e.quote}</q>}</li>)}</ul><p className="muted">Review suggestions against the source. Your saved correction takes priority.</p></section>}
      <label>Required skills (comma separated)<input value={form.skills} onChange={e => update('skills', e.target.value)}/></label>
      <label>Civic topics (comma separated)<input value={form.topics} onChange={e => update('topics', e.target.value)}/></label>
      <label>Difficulty<select value={form.difficulty} onChange={e => update('difficulty', e.target.value)}><option value="">Unknown</option>{['Beginner', 'Intermediate', 'Advanced'].map(d => <option key={d}>{d}</option>)}</select></label>
      <label>Estimated hours<input type="number" min="0" max="10000" step="any" value={form.effort} onChange={e => update('effort', e.target.value)}/></label>
      <label>Correction rationale<textarea required value={form.rationale} maxLength={1000} onChange={e=>update('rationale',e.target.value)}/></label><div className="taskActions"><button className="btn primary" disabled={busy}>Save metadata</button><button type="button" className="btn secondary" disabled={busy} onClick={() => setEditing(null)}>Cancel</button></div></form></section>
      : tasks === null ? <p role="status">Loading assigned issues…</p> : tasks.length === 0 ? <p className="panel">No issues assigned. Ask an administrator to assign a repository or check source synchronization.</p> : tasks.map(t => <article className="panel taskCard" key={t.id}><span className="eyebrow">{t.repository} · {t.upstream?.number ? 'GitHub #' + t.upstream.number : 'Archived local record'}</span><h2>{t.title}</h2><div className="tags"><span>{t.metadata.difficulty || 'Unknown difficulty'}</span><span>{t.metadata.effort ?? '?'} hours</span>{t.metadata.skills.map(s => <span key={s}>{s}</span>)}</div>{t.metadata.needs_review && <p className="msg info">Source changed; re-review needed.</p>}{t.url&&<p><a href={t.url} target="_blank" rel="noopener noreferrer">Inspect source issue ↗</a></p>}<button className="btn secondary" onClick={() => edit(t)}>Edit metadata</button><button className="btn ghost" onClick={async()=>{try{await api(`/maintainer/tasks/${t.id}/metadata`,{method:'DELETE'});const d=await api('/curator/issues?'+new URLSearchParams({q,page}));setTasks(d.items);setMessage('Override reset to source-derived metadata.');}catch(e){setError(e.message);}}}>Reset override</button></article>)}
    {!editing&&total>20&&<nav className="pagination" aria-label="Review pages"><button className="btn secondary" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>{page} / {Math.ceil(total/20)}</span><button className="btn secondary" disabled={page*20>=total} onClick={()=>setPage(p=>p+1)}>Next</button></nav>}
  </section></>;
}
