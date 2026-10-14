import React, { useEffect, useState } from 'react';
import { Bell, Check } from 'lucide-react';
import { api } from '../api';

function ago(ts) {
  const s = Math.max(0, Date.now() / 1000 - ts);
  if (s < 60) return 'Just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} hours ago`;
  if (s < 172800) return 'Yesterday';
  return new Date(ts * 1000).toLocaleDateString();
}

export default function Notifications({ onError, onChanged }) {
  const [items, setItems] = useState(null), [error, setError] = useState('');
  const fail = e => { setError(e.message); if (e.status === 401) onError(e); };
  const load = () => api('/me/notifications').then(setItems).catch(fail);
  useEffect(() => { load(); }, []);
  const markAll = async () => {
    try { await api('/me/notifications/read', { method: 'POST' }); setItems(l => l.map(n => ({ ...n, read: true }))); onChanged(); }
    catch (e) { fail(e); }
  };
  const markOne = async n => {
    if (n.read) return;
    try { await api(`/me/notifications/${n.id}/read`, { method: 'PUT' }); setItems(l => l.map(x => x.id === n.id ? { ...x, read: true } : x)); onChanged(); }
    catch (e) { fail(e); }
  };
  const unread = items ? items.filter(n => !n.read).length : 0;
  return <><section className="pageHead"><div><span className="eyebrow">CIVIC ISSUE MATCHMAKER</span><h1>Notifications</h1><p>New matches, task events, and account updates.</p></div>
    <button className="btn ghost" disabled={!unread} onClick={markAll}><Check size={16}/> Mark all read</button></section>
    <section className="pageBody">
      {error && <p className="msg error" role="alert">{error}</p>}
      {!items ? <p role="status">Loading notifications…</p> : items.length === 0 ? <p className="panel">You have no notifications yet.</p> :
        <div className="panel list">{items.map(n => <div key={n.id} className={'notification' + (n.read ? '' : ' unread')} onClick={() => markOne(n)}>
          <Bell size={19}/><div><strong>{n.title}</strong><p>{n.body}</p><small>{ago(n.created_at)}</small></div></div>)}</div>}
    </section></>;
}
