import React, { useEffect, useState } from 'react';
import { api } from '../api';

function RoleEditor({ account, repositories, onSave, busy }) {
  const [roles, setRoles] = useState(account.roles.filter(r => r !== 'volunteer'));
  const [assigned, setAssigned] = useState(account.maintained_repositories);
  const toggle = (list, value) => list.includes(value) ? list.filter(x => x !== value) : [...list, value];
  return <article className="panel adminAccount"><h3>{account.profile.name}</h3><p className="muted">{account.email}</p><fieldset><legend>Account roles</legend><span className="muted">Volunteer access is included for every account.</span>{['maintainer', 'administrator'].map(role => <label className="checkLabel" key={role}><input type="checkbox" checked={roles.includes(role)} onChange={() => setRoles(toggle(roles, role))}/>{role === 'maintainer' ? 'Maintainer' : 'Administrator'}</label>)}</fieldset>
    {roles.includes('maintainer') && <fieldset><legend>Assigned repositories</legend>{repositories.map(r => <label className="checkLabel" key={r.id}><input type="checkbox" checked={assigned.includes(r.id)} onChange={() => setAssigned(toggle(assigned, r.id))}/>{r.path}</label>)}</fieldset>}
    <button className="btn secondary" disabled={busy} onClick={() => onSave(account.id, { roles, repository_ids: roles.includes('maintainer') ? assigned : [] })}>Save roles</button></article>;
}

export default function Admin({ user, onUserChanged, onError }) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [message, setMessage] = useState(''), [busy, setBusy] = useState(false);
  const load = async () => { const [users, repos, audit] = await Promise.all([api('/admin/users'), api('/admin/repositories'), api('/admin/audit')]); setData({ users, repos, audit }); };
  useEffect(() => { load().catch(e => { setError(e.message); if (e.status === 401) onError(e); }); }, []);
  const run = async action => { setBusy(true); setError(''); setMessage(''); try { await action(); await load(); setMessage('Changes saved.'); } catch (e) { setError(e.message); if (e.status === 401) onError(e); } finally { setBusy(false); } };
  const saveRoles = (id, body) => run(async () => { const updated = await api(`/admin/users/${id}/roles`, { method: 'PUT', body }); if (id === user.id) onUserChanged(updated); });
  return <><section className="pageHead"><div><span className="eyebrow">ADMINISTRATOR WORKSPACE</span><h1>Administration</h1><p>Manage account permissions and oversee civic repository sources.</p></div></section><section className="pageBody discovery">
    {error && <p className="msg error" role="alert">{error}</p>}{message && <p className="msg success" role="status">{message}</p>}
    {!data ? <p role="status">Loading administration…</p> : <><h2>Users and roles</h2><div className="adminGrid">{data.users.map(u => <RoleEditor key={u.id + u.roles.join() + u.maintained_repositories.join()} account={u} repositories={data.repos} busy={busy} onSave={saveRoles}/>)}</div>
      <h2 className="sectionTitle">Repository sources</h2><p className="muted">Disabling a source removes its issues from discovery and prevents new claims. Existing participation history remains available.</p>{data.repos.map(r => <article className="panel taskCard" key={r.id}><h3>{r.path}</h3><p>{r.source} · {r.enabled ? 'Enabled' : 'Disabled'}</p>{r.error && <p className="msg error">{r.error}</p>}<button className="btn secondary" disabled={busy} onClick={() => run(() => api(`/admin/repositories/${r.id}`, { method: 'PUT', body: { enabled: !r.enabled } }))}>{r.enabled ? 'Disable source' : 'Enable source'}</button></article>)}
      <h2 className="sectionTitle">Recent audit activity</h2>{!data.audit.length && <p className="muted">Role changes, metadata corrections, and source changes appear here.</p>}<ol className="historyList">{data.audit.map(e => <li className="panel" key={e.id}><strong>{e.action}</strong><span>{e.target} · Account #{e.actor_id}</span><time>{new Date(e.occurred_at * 1000).toLocaleString()}</time></li>)}</ol></>}
  </section></>;
}
