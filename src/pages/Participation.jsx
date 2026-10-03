import React, { useEffect, useState } from 'react';
import { api } from '../api';

export default function Participation({ onError }) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [busy, setBusy] = useState(null);
  const load = () => api('/me/participation').then(setData).catch(e => { setError(e.message); if (e.status === 401) onError(e); });
  useEffect(() => { load(); }, []);
  const change = async (id, action) => {
    setBusy(id); setError('');
    try { await api(`/tasks/${id}/participation`, { method: 'POST', body: { action } }); await load(); }
    catch (e) { setError(e.message); if (e.status === 401) onError(e); }
    finally { setBusy(null); }
  };
  return <><section className="pageHead"><div><span className="eyebrow">YOUR CONTRIBUTIONS</span><h1>Participation</h1><p>Manage your claimed tasks and review your contribution history.</p></div></section><section className="pageBody discovery">
    {error && <p className="msg error" role="alert">{error}</p>}
    {!data ? <p role="status">Loading participation…</p> : <><h2>Active claims</h2>{data.active.length === 0 && <p className="panel">No active claims. Claim an available issue from Discover.</p>}
      {data.active.map(t => <article className="panel taskCard" key={t.id}><h3>{t.title}</h3><p>{t.metadata.location || t.repository}</p><div className="taskActions"><button className="btn primary" disabled={busy === t.id} onClick={() => change(t.id, 'completed')}>Mark complete</button><button className="btn secondary" disabled={busy === t.id} onClick={() => change(t.id, 'released')}>Release task</button></div></article>)}
      <h2 className="sectionTitle">Participation history</h2>{data.events.length === 0 && <p className="muted">Your claims, releases, and completions will appear here.</p>}
      <ol className="historyList">{data.events.map(e => <li className="panel" key={e.id}><strong>{e.title}</strong><span className="tags"><span>{e.action}</span></span><time>{new Date(e.occurred_at * 1000).toLocaleString()}</time></li>)}</ol></>}
  </section></>;
}
