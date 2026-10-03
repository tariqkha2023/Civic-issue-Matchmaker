import React, { useEffect, useState } from 'react';
import { api } from '../api';

export default function Maintainer({ onError }) {
  const [tasks, setTasks] = useState(null), [editing, setEditing] = useState(null), [form, setForm] = useState({}), [busy, setBusy] = useState(false), [error, setError] = useState(''), [message, setMessage] = useState('');
  useEffect(() => { api('/maintainer/tasks').then(setTasks).catch(e => { setError(e.message); if (e.status === 401) onError(e); }); }, []);
  const edit = t => { setEditing(t); setMessage(''); setForm({ skills: t.metadata.skills.join(', '), topics: t.metadata.topics.join(', '), difficulty: t.metadata.difficulty || '', effort: t.metadata.effort ?? '' }); };
  const update = (key, value) => setForm(f => ({ ...f, [key]: value }));
  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    const split = value => value.split(',').map(s => s.trim()).filter(Boolean);
    try {
      const updated = await api(`/maintainer/tasks/${editing.id}/metadata`, { method: 'PUT', body: { skills: split(form.skills), topics: split(form.topics), difficulty: form.difficulty || null, effort: form.effort === '' ? null : Number(form.effort) } });
      setTasks(ts => ts.map(t => t.id === updated.id ? updated : t)); setEditing(null); setMessage('Metadata updated. Source values were preserved and the change was recorded.');
    } catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(false); }
  };
  return <><section className="pageHead"><div><span className="eyebrow">MAINTAINER WORKSPACE</span><h1>Manage issues</h1><p>Review and correct metadata for your assigned civic repositories.</p></div></section><section className="pageBody discovery">
    {error && <p className="msg error" role="alert">{error}</p>}{message && <p className="msg success" role="status">{message}</p>}
    {editing ? <section className="panel form"><h2>{editing.title}</h2><p className="muted">Corrections affect discovery and matching. The original issue metadata remains stored.</p><form onSubmit={submit}>
      <label>Required skills (comma separated)<input value={form.skills} onChange={e => update('skills', e.target.value)}/></label>
      <label>Civic topics (comma separated)<input value={form.topics} onChange={e => update('topics', e.target.value)}/></label>
      <label>Difficulty<select value={form.difficulty} onChange={e => update('difficulty', e.target.value)}><option value="">Unknown</option>{['Beginner', 'Intermediate', 'Advanced'].map(d => <option key={d}>{d}</option>)}</select></label>
      <label>Estimated hours<input type="number" min="0" max="10000" step="any" value={form.effort} onChange={e => update('effort', e.target.value)}/></label>
      <div className="taskActions"><button className="btn primary" disabled={busy}>Save metadata</button><button type="button" className="btn secondary" disabled={busy} onClick={() => setEditing(null)}>Cancel</button></div></form></section>
      : tasks === null ? <p role="status">Loading assigned issues…</p> : tasks.length === 0 ? <p className="panel">No issues assigned. Ask an administrator to assign a repository.</p> : tasks.map(t => <article className="panel taskCard" key={t.id}><span className="eyebrow">{t.repository} · Issue #{t.id}</span><h2>{t.title}</h2><div className="tags"><span>{t.metadata.difficulty || 'Unknown difficulty'}</span><span>{t.metadata.effort ?? '?'} hours</span>{t.metadata.skills.map(s => <span key={s}>{s}</span>)}</div><button className="btn secondary" onClick={() => edit(t)}>Edit metadata</button></article>)}
  </section></>;
}
