import React, { useEffect, useState } from 'react';
import { Bookmark, Compass, UserRound, LogOut, FolderOpen, History, Shield, Wrench } from 'lucide-react';
import logo from './assets/civic-logo.png';
import { api } from './api';
import Home from './pages/Home';
import Profile from './pages/Profile';
import Auth from './pages/Auth';
import Participation from './pages/Participation';
import Maintainer from './pages/Maintainer';
import Admin from './pages/Admin';

function route() {
  const value = window.location.hash.slice(2);
  return ['home', 'repository', 'saved', 'profile', 'login', 'register', 'participation', 'maintainer', 'admin'].includes(value) ? value : 'home';
}
export default function App() {
  const [page, setPage] = useState(route);
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');
  const go = p => { window.location.hash = '#/' + p; };
  useEffect(() => {
    const change = () => setPage(route());
    window.addEventListener('hashchange', change);
    api('/me').then(setUser).catch(e => { if (e.status !== 401) setError(e.message); }).finally(() => setReady(true));
    return () => window.removeEventListener('hashchange', change);
  }, []);
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
  const nav = [["home", Compass, "Discover"], ["repository", FolderOpen, "Repository"], ["saved", Bookmark, "Saved tasks"], ["participation", History, "Participation"], ["profile", UserRound, "My profile"], ...(maintainer ? [["maintainer", Wrench, "Manage issues"]] : []), ...(administrator ? [["admin", Shield, "Administration"]] : [])];
  return <div className="app">
    <a className="skipLink" href="#main">Skip to content</a>
    <aside className="sidebar">
      <button className="sideBrand" aria-label="Civic Issue Matchmaker home" onClick={() => go('home')}><img className="sidebarLogo" src={logo} alt="Civic Issue Matchmaker" /></button>
      <div className="sideLabel eyebrow">{administrator ? 'ADMINISTRATOR WORKSPACE' : maintainer ? 'MAINTAINER WORKSPACE' : 'VOLUNTEER WORKSPACE'}</div>
      {nav.map(([key, Icon, label]) =>
        <button key={key} className={'navItem' + (page === key ? ' active' : '')} aria-label={label} aria-current={page === key ? 'page' : undefined} onClick={() => go(key)}><Icon size={20}/><span>{label}</span></button>)}
      <p className="sidebarNote">Small contributions.<br/>Meaningful civic impact.</p>
    </aside>
    <div className="workspace">
      <header className="topbar">
        {user ? <><span className="accountName">{user.profile.name} <span className="roleBadge">{administrator ? 'Administrator' : maintainer ? 'Maintainer' : 'Volunteer'}</span></span><button className="btn ghost" onClick={logout}><LogOut size={16}/> Sign out</button></> : <><button className="btn ghost" onClick={() => go('login')}>Login</button><button className="btn primary" onClick={() => go('register')}>Register</button></>}
      </header>
      <main id="main" tabIndex="-1">
        {error && <div role="alert" className="msg error globalError">{error}<button className="textButton" onClick={() => setError('')}>Dismiss</button></div>}
        {!ready ? <p className="container" role="status">Connecting to your workspace…</p> :
          page === 'login' || page === 'register' ? <Auth key={page} register={page === 'register'} go={go} onSuccess={u => { setUser(u); setError(''); go('home'); }}/>
          : !user ? <section className="container welcome"><span className="eyebrow">CIVIC ISSUE MATCHMAKER</span><h1>Find a task that fits you.</h1><p>Connect your skills and interests with community projects and local volunteer opportunities. Get transparent recommendations and keep a personal list of tasks to explore.</p><button className="btn primary" onClick={() => go('register')}>Create your volunteer profile</button><p>Already a member? <button className="textButton" onClick={() => go('login')}>Sign in</button></p></section>
          : page === 'participation' ? <Participation onError={onError}/>
          : page === 'maintainer' ? (maintainer ? <Maintainer onError={onError}/> : <section className="container"><h1>Access restricted</h1><p>Maintainer access is required.</p></section>)
          : page === 'admin' ? (administrator ? <Admin user={user} onUserChanged={setUser} onError={onError}/> : <section className="container"><h1>Access restricted</h1><p>Administrator access is required.</p></section>)
          : page === 'profile' ? <Profile user={user} onSaved={setUser} onError={onError}/>
          : <Home key={page + user.id} savedOnly={page === 'saved'} repositoryOnly={page === 'repository'} user={user} go={go} onError={onError}/>}
      </main>
    </div>
  </div>;
}
