import React, { useState } from 'react';
import PasswordInput from '../components/PasswordInput';
import { api } from '../api';

export default function Auth({ register, go, onSuccess }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [errors, setErrors] = useState({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const change = (key, value) => { setForm(f => ({ ...f, [key]: value })); setErrors(e => ({ ...e, [key]: '' })); };
  const submit = async e => {
    e.preventDefault();
    const next = {};
    if (register && form.name.trim().length < 2) next.name = 'Enter your name (at least 2 characters).';
    if (!/^\S+@\S+\.\S+$/.test(form.email)) next.email = 'Enter a valid email address.';
    if (form.password.length < 10 || form.password.length > 128) next.password = 'Use 10–128 characters.';
    if (register && form.password !== form.confirm) next.confirm = 'Passwords do not match.';
    setErrors(next); setError('');
    if (Object.keys(next).length) { change('password', ''); change('confirm', ''); setErrors(next); return; }
    setBusy(true);
    try {
      const body = { email: form.email, password: form.password, ...(register ? { name: form.name.trim() } : {}) };
      onSuccess(await api(register ? '/accounts' : '/sessions', { method: 'POST', body }));
    } catch (e) { setError(e.message); setForm(f => ({ ...f, password: '', confirm: '' })); }
    finally { setBusy(false); }
  };
  const fieldError = key => errors[key] && <span id={key + '-error'} className="fieldError">{errors[key]}</span>;
  return <section className="authWrap"><form className="authCard" noValidate onSubmit={submit}>
    <h1>{register ? 'Create your account' : 'Welcome back'}</h1><p className="sub">Find civic tasks that fit your skills and time.</p>
    {register && <p className="privacyNotice">Your email and volunteer profile are stored to personalize recommendations. Your profile and saved list are private to your account. Never include sensitive personal information in profile fields.</p>}
    {register && <label htmlFor="name">Display name<input id="name" maxLength={100} value={form.name} onChange={e => change('name', e.target.value)} autoComplete="name" aria-invalid={!!errors.name} aria-describedby="name-error"/>{fieldError('name')}</label>}
    <label htmlFor="email">Email<input id="email" type="email" maxLength={254} value={form.email} onChange={e => change('email', e.target.value)} autoComplete="email" aria-invalid={!!errors.email} aria-describedby="email-error"/>{fieldError('email')}</label>
    <label htmlFor="password">Password<PasswordInput id="password" invalid={!!errors.password} describedBy="password-error" value={form.password} onChange={v => change('password', v)} autoComplete={register ? 'new-password' : 'current-password'}/>{fieldError('password')}</label>
    {register && <label htmlFor="confirm">Confirm password<PasswordInput id="confirm" invalid={!!errors.confirm} describedBy="confirm-error" value={form.confirm} onChange={v => change('confirm', v)} autoComplete="new-password"/>{fieldError('confirm')}</label>}
    {error && <div role="alert" className="msg error">{error}</div>}
    <button disabled={busy} className="btn primary full">{busy ? 'Please wait…' : register ? 'Register' : 'Login'}</button>
    <p className="switch">{register ? 'Already have an account? ' : 'New here? '}<button type="button" onClick={() => go(register ? 'login' : 'register')}>{register ? 'Login' : 'Create an account'}</button></p>
  </form></section>;
}
