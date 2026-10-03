import React, { useState } from 'react';
import { api } from '../api';

const levels = ['Beginner', 'Intermediate', 'Advanced'];
const list = value => [...new Set(value.split(',').map(v => v.trim()).filter(Boolean))];
export default function Profile({ user, onSaved, onError }) {
  const [form, setForm] = useState(() => ({ ...user.profile, skills: user.profile.skills.join(', '), interests: user.profile.interests.join(', '), repositories: user.profile.repositories.join(', ') }));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [errors, setErrors] = useState({});
  const update = (key, value) => { setForm(f => ({ ...f, [key]: value })); setMessage(''); setErrors(e => ({ ...e, [key]: '' })); };
  const save = async e => {
    e.preventDefault(); setMessage(''); setError('');
    const next = {};
    if (form.name.trim().length < 2) next.name = 'Enter a name with at least 2 characters.';
    if (form.hours === '' || !Number.isFinite(Number(form.hours)) || Number(form.hours) < 0 || Number(form.hours) > 168) next.hours = 'Enter availability between 0 and 168 hours.';
    for (const key of ['skills', 'interests', 'repositories']) {
      const values = list(form[key]);
      if (values.length > 30 || values.some(v => v.length > 100)) next[key] = 'Use at most 30 entries, each up to 100 characters.';
    }
    setErrors(next); if (Object.keys(next).length) return;
    setBusy(true);
    try {
      const updated = await api('/me/profile', { method: 'PUT', body: { ...form, hours: Number(form.hours), skills: list(form.skills), interests: list(form.interests), repositories: list(form.repositories) } });
      onSaved(updated); setMessage('Profile saved. Your recommendations will use these preferences.');
    } catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(false); }
  };
  return <><section className="pageHead"><div><span className="eyebrow">YOUR MATCHING PREFERENCES</span><h1>Volunteer profile</h1><p>Tell us what you know, what interests you, and how much time you have.</p></div></section>
    <section className="pageBody"><form className="panel form" noValidate onSubmit={save}>
      <div className="profileGrid">
      {[['name', 'Display name'], ['skills', 'Skills (comma separated)'], ['interests', 'Interests / civic topics (comma separated)'], ['repositories', 'Preferred repositories (owner/repo, comma separated)']].map(([key, label]) => <label key={key}>{label}<input value={form[key]} onChange={e => update(key, e.target.value)} aria-invalid={!!errors[key]} placeholder={key === 'skills' ? 'Food preparation, Communication, Gardening' : key === 'interests' ? 'Food security, Environment, Transportation' : ''}/>{errors[key] && <span className="fieldError">{errors[key]}</span>}</label>)}
      {[['level', 'Experience level'], ['difficulty', 'Preferred difficulty']].map(([key, label]) => <label key={key}>{label}<select value={form[key]} onChange={e => update(key, e.target.value)}>{levels.map(level => <option key={level}>{level}</option>)}</select></label>)}
      <label>Weekly availability (hours)<input type="number" min="0" max="168" step="0.5" value={form.hours} onChange={e => update('hours', e.target.value)} aria-invalid={!!errors.hours}/>{errors.hours && <span className="fieldError">{errors.hours}</span>}</label>
      </div><p className="muted">Profile information is private to your account. Fields without task metadata do not affect compatibility scores.</p>
      {error && <p className="msg error" role="alert">{error}</p>}{message && <p className="msg success" role="status">{message}</p>}
      <button className="btn primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile'}</button>
    </form></section></>;
}
