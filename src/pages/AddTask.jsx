import React, { useState } from 'react';
import { api } from '../api';
import { DEMO_NAME, CIVIC_TOPICS } from '../demo';

export default function AddTask({ onCreated, onCancel, onError }) {
  const [form, setForm] = useState({ title: '', description: '', location: '', organizer: '', skills: '', topic: '', difficulty: 'Beginner', effort: '' });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const update = (key, value) => { setForm(f => ({ ...f, [key]: value })); setErrors(e => ({ ...e, [key]: '' })); };
  const submit = async e => {
    e.preventDefault(); setError('');
    const next = {};
    for (const key of ['title']) if (form[key].trim().length < 2) next[key] = 'Enter at least two characters.';
    const skills = [...new Set(form.skills.split(',').map(v => v.trim()).filter(Boolean))];
    if (skills.length > 30 || skills.some(v => v.length > 100)) next.skills = 'Use at most 30 skills, each up to 100 characters.';
    if (form.effort !== '' && (!Number.isFinite(Number(form.effort)) || Number(form.effort) < 0 || Number(form.effort) > 10000)) next.effort = 'Enter hours between 0 and 10,000, or leave blank.';
    setErrors(next); if (Object.keys(next).length) return;
    setBusy(true);
    try { onCreated(await api('/issues', { method: 'POST', body: { ...form, skills, difficulty: form.difficulty || null, effort: form.effort === '' ? null : Number(form.effort) } })); }
    catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(false); }
  };
  const input = (key, label, props = {}) => <label key={key} htmlFor={'task-' + key}>{label}<input aria-label={label} id={'task-' + key} value={form[key]} onChange={e => update(key, e.target.value)} aria-invalid={!!errors[key]} aria-describedby={errors[key] ? key + '-task-error' : undefined} {...props}/>{errors[key] && <span className="fieldError" id={key + '-task-error'}>{errors[key]}</span>}</label>;
  return <section className="panel form addTaskPanel" aria-labelledby="add-task-title"><h2 id="add-task-title">Create issue</h2><p className="muted">Add a community issue to the demo repository. It will appear in Discover immediately and remain available after refresh.</p>
    <form onSubmit={submit} noValidate>
      <p className="repositoryDestination"><span className="eyebrow">DEMO REPOSITORY</span><strong>{DEMO_NAME}</strong></p>
      {input('title', 'Issue title', { maxLength: 200, autoFocus: true })}
      <label htmlFor="task-description">Description<textarea id="task-description" value={form.description} onChange={e => update('description', e.target.value)} maxLength={10000} rows={4}/></label>
      <div className="profileGrid">
        {input('location', 'Location (optional)', { maxLength: 200, placeholder: 'e.g. Riverside Community Kitchen' })}
        {input('organizer', 'Organizer (optional)', { maxLength: 100, placeholder: 'e.g. Community Meals Team' })}
        {input('skills', 'Required skills (comma separated)', { placeholder: 'Food preparation, Communication, Teamwork' })}
        {input('topic', 'Civic topic (optional)', { maxLength: 100, placeholder: 'e.g. Food security', list: 'civic-topics' })}
        <label htmlFor="task-difficulty">Difficulty<select id="task-difficulty" value={form.difficulty} onChange={e => update('difficulty', e.target.value)}><option value="">Unknown</option>{['Beginner', 'Intermediate', 'Advanced'].map(level => <option key={level}>{level}</option>)}</select></label>
        {input('effort', 'Estimated hours (optional)', { type: 'number', min: 0, max: 10000, step: 'any', placeholder: 'Leave blank if unknown' })}

      </div>
      <datalist id="civic-topics">{CIVIC_TOPICS.map(topic => <option value={topic} key={topic}/>)}</datalist>
      {error && <p className="msg error" role="alert">{error}</p>}
      <div className="taskActions"><button className="btn primary" disabled={busy}>{busy ? 'Creating…' : 'Create issue'}</button><button className="btn secondary" type="button" disabled={busy} onClick={onCancel}>Cancel</button></div>
    </form>
  </section>;
}
