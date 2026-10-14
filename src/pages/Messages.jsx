import React, { useEffect, useRef, useState } from 'react';
import { Send } from 'lucide-react';
import { api } from '../api';

const initials = name => name.split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();

export default function Messages({ onError, onChanged }) {
  const [people, setPeople] = useState(null), [active, setActive] = useState(null), [thread, setThread] = useState([]);
  const [text, setText] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const end = useRef(null);
  const fail = e => { setError(e.message); if (e.status === 401) onError(e); };
  const loadPeople = () => api('/messages/conversations').then(setPeople).catch(fail);
  const open = async id => {
    try { const d = await api('/messages/' + id); setActive(d.user); setThread(d.messages); onChanged(); loadPeople(); }
    catch (e) { fail(e); }
  };
  useEffect(() => { loadPeople(); }, []);
  useEffect(() => { end.current?.scrollIntoView?.({ block: 'end' }); }, [thread]);
  const send = async e => {
    e.preventDefault();
    if (!text.trim() || !active) return;
    setBusy(true); setError('');
    try { await api('/messages', { method: 'POST', body: { recipient_id: active.user_id, body: text } }); setText(''); await open(active.user_id); }
    catch (e) { fail(e); }
    finally { setBusy(false); }
  };
  return <><section className="pageHead"><div><span className="eyebrow">CIVIC ISSUE MATCHMAKER</span><h1>Messages</h1><p>Talk with maintainers, administrators, and people who write to you.</p></div></section>
    <section className="pageBody">
      {error && <p className="msg error" role="alert">{error}</p>}
      {!people ? <p role="status">Loading messages…</p> : people.length === 0 ? <p className="panel">No conversations yet.</p> :
        <div className="messagesLayout panel">
          <ul className="convoList" aria-label="Conversations">{people.map(p => <li key={p.user_id}>
            <button className={'convo' + (active?.user_id === p.user_id ? ' active' : '')} onClick={() => open(p.user_id)}>
              <span className="avatar small">{initials(p.name)}</span>
              <span className="convoText"><strong>{p.name}{p.staff && <span className="roleBadge">Staff</span>}</strong><small>{p.last || 'Start a conversation'}</small></span>
              {p.unread > 0 && <b className="count">{p.unread}</b>}
            </button></li>)}</ul>
          <div className="thread">
            {!active ? <p className="muted threadEmpty">Select a conversation to read and reply.</p> : <>
              <h3 className="threadHead">{active.name}</h3>
              <div className="bubbles" role="log" aria-live="polite">
                {thread.length === 0 && <p className="muted">No messages yet. Say hello below.</p>}
                {thread.map(m => <div key={m.id} className={'bubble' + (m.mine ? ' mine' : '')}><p>{m.body}</p><small>{new Date(m.created_at * 1000).toLocaleString()}</small></div>)}
                <div ref={end}/>
              </div>
              <form className="composer" onSubmit={send}>
                <input aria-label="Message" value={text} maxLength={2000} onChange={e => setText(e.target.value)} placeholder="Write a message…"/>
                <button className="btn primary" disabled={busy || !text.trim()}><Send size={16}/> Send</button>
              </form></>}
          </div>
        </div>}
    </section></>;
}
