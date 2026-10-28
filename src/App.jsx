import React, { useEffect, useState } from 'react';
import { Bookmark, Compass, UserRound, LogOut, FolderOpen, History, Shield, Wrench, Bell, MessageSquare } from 'lucide-react';
import logo from './assets/civic-logo.png';
import { api } from './api';
import Home from './pages/Home';
import Projects from './pages/Projects';
import Account from './pages/Account';
import Profile from './pages/Profile';
import Auth from './pages/Auth';
import Participation from './pages/Participation';
import Maintainer from './pages/Maintainer';
import Admin from './pages/Admin';
import Notifications from './pages/Notifications';
import Messages from './pages/Messages';

function route() {
  const value = window.location.hash.slice(2);
  return ['home', 'repository', 'saved', 'profile', 'login', 'register', 'participation', 'maintainer', 'admin', 'notifications', 'messages', 'account'].includes(value) ? value : 'home';
}
export default function App() {
  const [page, setPage] = useState(route);
  const [selectedProject, setSelectedProject] = useState('');
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const [unread, setUnread] = useState({ notifications: 0, messages: 0 });
  const go = p => { window.location.hash = '#/' + p; };
  useEffect(() => {
    const change = () => setPage(route());
    window.addEventListener('hashchange', change);
    api('/me').then(setUser).catch(e => { if (e.status !== 401) setError(e.message); }).finally(() => setReady(true));
    return () => window.removeEventListener('hashchange', change);
  }, []);
  const refreshUnread = () => api('/me/unread').then(setUnread).catch(() => {});
  useEffect(() => {
    if (!user) { setUnread({ notifications: 0, messages: 0 }); return; }
    refreshUnread();
    const t = setInterval(refreshUnread, 30000);
    return () => clearInterval(t);
  }, [user?.id, page]);
  const onError = e => {
    if (e.status === 401) { setUser(null); go('login'); }
    setError(e.message);
  };
  const logout = async () => {
    try { await api('/sessions', { method: 'DELETE' }); setUser(null); setError(''); go('login'); }
    catch (e) { onError(e); }
  };
  const administrator = user?.roles.includes('administrator');
  const maintainer = administrator || user?.roles.includes('maintainer');
  const nav = [["home", Compass, "Discover"], ["repository", FolderOpen, "Projects"], ["saved", Bookmark, "Saved issues"], ["participation", History, "My contributions"], ["notifications", Bell, "Notifications"], ["messages", MessageSquare, "Messages"], ["profile", UserRound, "My profile"], ["account", Shield, "Account settings"], ...(maintainer ? [["maintainer", Wrench, "Review metadata"]] : []), ...(administrator ? [["admin", Shield, "Administration"]] : [])];
  const badge = { notifications: unread.notifications, messages: unread.messages };
  const initial = user ? user.profile.name.split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase() : '';
  return <div className="app">
    <a className="skipLink" href="#main">Skip to content</a>
    <aside className="sidebar">
      <button className="sideBrand" aria-label="Civic Issue Matchmaker home" onClick={() => go('home')}><img className="sidebarLogo" src={logo} alt="Civic Issue Matchmaker" /></button>
      <div className="sideLabel eyebrow">{administrator ? 'ADMINISTRATOR WORKSPACE' : maintainer ? 'CURATOR WORKSPACE' : 'CONTRIBUTOR WORKSPACE'}</div>
      {nav.map(([key, Icon, label]) =>
        <button key={key} className={'navItem' + (page === key ? ' active' : '')} aria-label={label} aria-current={page === key ? 'page' : undefined} onClick={() => go(key)}><Icon size={20}/><span>{label}</span>{badge[key] > 0 && <b className="count" aria-label={`${badge[key]} unread`}>{badge[key]}</b>}</button>)}
      <p className="sidebarNote">Small contributions.<br/>Meaningful civic impact.</p>
    </aside>
    <div className="workspace">
      <header className="topbar">
        {user ? <><button className={'iconBtn' + (page === 'notifications' ? ' active' : '')} aria-label={unread.notifications ? `Open notifications, ${unread.notifications} unread` : 'Open notifications'} onClick={() => go('notifications')}><Bell size={20}/>{unread.notifications > 0 && <span className="dot"/>}</button><button className="avatar small" aria-label="Open my profile" onClick={() => go('profile')}>{initial}</button><span className="accountName">{user.profile.name} <span className="roleBadge">{administrator ? 'Administrator' : maintainer ? 'Curator' : 'Contributor'}</span></span><button className="btn ghost" onClick={logout}><LogOut size={16}/> Sign out</button></> : <><button className="btn ghost" onClick={() => go('login')}>Login</button><button className="btn primary" onClick={() => go('register')}>Register</button></>}
      </header>
      <main id="main" tabIndex="-1">
        {error && <div role="alert" className="msg error globalError">{error}<button className="textButton" onClick={() => setError('')}>Dismiss</button></div>}
        {!ready ? <p className="container" role="status">Connecting to your workspace…</p> :
          page === 'login' || page === 'register' ? <Auth key={page} register={page === 'register'} go={go} onSuccess={u => { setUser(u); setError(''); go('home'); }}/>
          : !user ? <section className="container welcome"><span className="eyebrow">CIVIC ISSUE MATCHMAKER</span><h1>Find your next civic-tech contribution.</h1><p>Match your technical skills and civic interests with real GitHub issues. Explore public-interest projects, understand recommendations, and track your contributions.</p><button className="btn primary" onClick={() => go('register')}>Create your contributor profile</button><p>Already a member? <button className="textButton" onClick={() => go('login')}>Sign in</button></p></section>
          : page === 'repository' ? <Projects onError={onError} onOpen={path=>{setSelectedProject(path);go('home');}}/>
          : page === 'account' ? <Account onError={onError} onDeleted={()=>{setUser(null);go('login');}}/>
          : page === 'notifications' ? <Notifications onError={onError} onChanged={refreshUnread}/>
          : page === 'messages' ? <Messages onError={onError} onChanged={refreshUnread}/>
          : page === 'participation' ? <Participation onError={onError}/>
          : page === 'maintainer' ? (maintainer ? <Maintainer onError={onError}/> : <section className="container"><h1>Access restricted</h1><p>Maintainer access is required.</p></section>)
          : page === 'admin' ? (administrator ? <Admin user={user} onUserChanged={setUser} onError={onError}/> : <section className="container"><h1>Access restricted</h1><p>Administrator access is required.</p></section>)
          : page === 'profile' ? <Profile user={user} onSaved={setUser} onError={onError}/>
          : <Home selectedProject={selectedProject} key={page + user.id + selectedProject} savedOnly={page === 'saved'} repositoryOnly={page === 'repository'} user={user} go={go} onError={onError}/>}
      </main>
    </div>
  </div>;
}
