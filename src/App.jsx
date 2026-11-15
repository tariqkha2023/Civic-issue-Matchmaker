
import React, { useEffect, useState } from 'react';
import {
  Bookmark, Compass, UserRound, LogOut, FolderOpen,
  History, Shield, Wrench, Bell, MessageSquare,
  Info, Users
} from 'lucide-react';

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

// PUBLIC PAGE: ABOUT THIS PROJECT
function AboutProject() {
  return (
    <>
      <section className="pageHead">
        <div>
          <span className="eyebrow">PROJECT INFORMATION</span>
          <h1>About This Project</h1>
          <p>Small contributions. Meaningful civic impact.</p>
        </div>
      </section>

      <section className="pageBody">
        <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
          <h2>What Is Civic Issue Matchmaker?</h2>
          <p>
            Civic Issue Matchmaker is a Senior Design project
            developed at Florida Atlantic University.
            It connects volunteers with open-source civic
            technology projects based on their technical
            skills, interests, and experience.
          </p>
          <p>
            The application makes it easier for contributors
            to discover meaningful GitHub issues and
            participate in projects that benefit communities.
          </p>
        </div>

        <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
          <h2>Project Objectives</h2>
          <ul>
            <li>Connect volunteers with civic technology projects.</li>
            <li>Recommend GitHub issues based on technical skills.</li>
            <li>Make open-source contribution opportunities easier to find.</li>
            <li>Support collaboration between contributors and maintainers.</li>
            <li>Provide tools for project and user management.</li>
          </ul>
        </div>

        <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
          <h2>How the Application Works</h2>
          <ol>
            <li>Users register and create a contributor profile.</li>
            <li>They provide their technical skills and interests.</li>
            <li>The application searches civic-tech GitHub issues.</li>
            <li>Matching features recommend suitable opportunities.</li>
            <li>Users can save issues and track contributions.</li>
            <li>Maintainers review metadata and administrators manage access.</li>
          </ol>
        </div>

        <div className="panel" style={{ padding: 24, marginBottom: 20 }}>
          <h2>Main Features</h2>
          <ul>
            <li>Registration and login</li>
            <li>GitHub issue search and filtering</li>
            <li>AI-assisted matching and recommendations</li>
            <li>Saved issues and contribution tracking</li>
            <li>Notifications and messaging</li>
            <li>Maintainer metadata review</li>
            <li>Administrator user and role management</li>
          </ul>
        </div>

        <div className="panel" style={{ padding: 24 }}>
          <h2>Technology Used</h2>
          <p><strong>Frontend:</strong> React, JavaScript, Vite, HTML, CSS</p>
          <p><strong>Backend:</strong> Python, FastAPI</p>
          <p><strong>Database:</strong> SQLite for local development</p>
          <p><strong>External Integration:</strong> GitHub API</p>
          <p><strong>Matching:</strong> AI-assisted issue enrichment</p>
          <p><strong>Version Control:</strong> Git and GitHub</p>
        </div>
      </section>
    </>
  );
}

// PUBLIC PAGE: OUR TEAM
function ProjectTeam() {
  const members = [
    {
      name: 'Tariq Khan',
      role: 'Frontend Development',
      tasks: [
        'React frontend and interface development',
        'Login and registration interfaces',
        'Issue search and filtering',
        'Notifications and messaging interfaces',
        'Maintainer and Administrator workspaces',
        'Frontend API integration and testing'
      ]
    },
    {
      name: 'Michael Anstett',
      role: 'Backend, Database and Project Planning',
      tasks: [
        'Database and backend development',
        'Repository and project planning',
        'Deployment and hosting planning',
        'Project documentation and presentation materials'
      ]
    },
    {
      name: 'Davian Brooks',
      role: 'Requirements, Integration and Testing',
      tasks: [
        'Software requirements and design documentation',
        'Project planning and task coordination',
        'Matching and interface design',
        'API integration and application testing'
      ]
    },
    {
      name: 'David Landivar',
      role: 'Backend Infrastructure and Security',
      tasks: [
        'Backend infrastructure',
        'Authentication and role-based access',
        'Security and privacy',
        'Performance and quality assurance',
        'Technical documentation'
      ]
    },
    {
      name: 'Andre Walia',
      role: 'GitHub Integration and Data Architecture',
      tasks: [
        'GitHub API and repository integration',
        'Issue synchronization',
        'Metadata normalization and validation',
        'Deduplication and incremental updates',
        'Data monitoring'
      ]
    }
  ];

  return (
    <>
      <section className="pageHead">
        <div>
          <span className="eyebrow">FAU SENIOR DESIGN | TEAM 26</span>
          <h1>Our Team & Contributions</h1>
          <p>
            Meet the developers behind Civic Issue Matchmaker.
          </p>
        </div>
      </section>

      <section className="pageBody">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 20
          }}
        >
          {members.map(member => (
            <article
              className="panel"
              key={member.name}
              style={{ padding: 24 }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  marginBottom: 16
                }}
              >
                <div className="avatar" aria-hidden="true">
                  {member.name
                    .split(' ')
                    .map(part => part[0])
                    .slice(0, 2)
                    .join('')
                    .toUpperCase()}
                </div>

                <div>
                  <h2 style={{ fontSize: 19, margin: 0 }}>
                    {member.name}
                  </h2>
                  <p className="muted" style={{ marginTop: 5 }}>
                    {member.role}
                  </p>
                </div>
              </div>

              <h3 style={{ fontSize: 15 }}>Contributions</h3>
              <ul>
                {member.tasks.map(task => (
                  <li key={task}>{task}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

// PAGE ROUTING
function route() {
  const value = window.location.hash.slice(2);

  const allowedPages = [
    'home', 'repository', 'saved', 'profile',
    'login', 'register', 'participation',
    'maintainer', 'admin', 'notifications',
    'messages', 'account', 'about', 'team'
  ];

  return allowedPages.includes(value) ? value : 'home';
}

// MAIN APPLICATION
export default function App() {
  const [page, setPage] = useState(route);
  const [selectedProject, setSelectedProject] = useState('');
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState('');

  const [unread, setUnread] = useState({
    notifications: 0,
    messages: 0
  });

  const go = p => {
    window.location.hash = '#/' + p;
  };

  useEffect(() => {
    const change = () => setPage(route());

    window.addEventListener('hashchange', change);

    api('/me')
      .then(setUser)
      .catch(e => {
        if (e.status !== 401) setError(e.message);
      })
      .finally(() => setReady(true));

    return () => {
      window.removeEventListener('hashchange', change);
    };
  }, []);

  const refreshUnread = () =>
    api('/me/unread')
      .then(setUnread)
      .catch(() => {});

  useEffect(() => {
    if (!user) {
      setUnread({ notifications: 0, messages: 0 });
      return;
    }

    refreshUnread();

    const timer = setInterval(refreshUnread, 30000);

    return () => clearInterval(timer);
  }, [user?.id, page]);

  const onError = e => {
    if (e.status === 401) {
      setUser(null);
      go('login');
    }

    setError(e.message);
  };

  const logout = async () => {
    try {
      await api('/sessions', { method: 'DELETE' });
      setUser(null);
      setError('');
      go('login');
    } catch (e) {
      onError(e);
    }
  };

  const administrator = user?.roles.includes('administrator');

  const maintainer =
    administrator || user?.roles.includes('maintainer');

  // EXISTING ROLE-BASED NAVIGATION
  const nav = [
    ['home', Compass, 'Discover'],
    ['repository', FolderOpen, 'Projects'],
    ['saved', Bookmark, 'Saved issues'],
    ['participation', History, 'My contributions'],
    ['notifications', Bell, 'Notifications'],
    ['messages', MessageSquare, 'Messages'],
    ['profile', UserRound, 'My profile'],
    ['account', Shield, 'Account settings'],

    ...(maintainer
      ? [['maintainer', Wrench, 'Review metadata']]
      : []),

    ...(administrator
      ? [['admin', Shield, 'Administration']]
      : [])
  ];

  // PUBLIC NAVIGATION FOR ALL VISITORS
  const projectNav = [
    ['about', Info, 'About This Project'],
    ['team', Users, 'Our Team & Contributions']
  ];

  const badge = {
    notifications: unread.notifications,
    messages: unread.messages
  };

  const initial = user
    ? user.profile.name
        .split(/\s+/)
        .map(w => w[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : '';

  return (
    <div className="app">
      <a className="skipLink" href="#main">
        Skip to content
      </a>

      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        <button
          className="sideBrand"
          aria-label="Civic Issue Matchmaker home"
          onClick={() => go('home')}
        >
          <img
            className="sidebarLogo"
            src={logo}
            alt="Civic Issue Matchmaker"
          />
        </button>

        <div className="sideLabel eyebrow">
          {administrator
            ? 'ADMINISTRATOR WORKSPACE'
            : maintainer
            ? 'CURATOR WORKSPACE'
            : user
            ? 'CONTRIBUTOR WORKSPACE'
            : 'CIVIC ISSUE MATCHMAKER'}
        </div>

        {nav.map(([key, Icon, label]) => (
          <button
            key={key}
            className={
              'navItem' + (page === key ? ' active' : '')
            }
            aria-label={label}
            aria-current={page === key ? 'page' : undefined}
            onClick={() => go(key)}
          >
            <Icon size={20} />
            <span>{label}</span>

            {badge[key] > 0 && (
              <b
                className="count"
                aria-label={`${badge[key]} unread`}
              >
                {badge[key]}
              </b>
            )}
          </button>
        ))}

        {/* DIVIDER AND PUBLIC PROJECT LINKS */}
        <div
          style={{
            borderTop: '1px solid rgba(255,255,255,0.25)',
            margin: '18px 12px 12px',
            paddingTop: 14
          }}
        >
          <p
            className="eyebrow"
            style={{
              color: '#a9c5c4',
              fontSize: 11,
              fontWeight: 'bold',
              letterSpacing: 1,
              marginBottom: 12
            }}
          >
            PROJECT INFORMATION
          </p>
        </div>

        {projectNav.map(([key, Icon, label]) => (
          <button
            key={key}
            className={
              'navItem' + (page === key ? ' active' : '')
            }
            aria-label={label}
            aria-current={page === key ? 'page' : undefined}
            onClick={() => go(key)}
          >
            <Icon size={20} />
            <span>{label}</span>
          </button>
        ))}

        <p className="sidebarNote">
          Small contributions.
          <br />
          Meaningful civic impact.
        </p>
      </aside>

      {/* MAIN WORKSPACE */}
      <div className="workspace">
        <header className="topbar">
          {user ? (
            <>
              <button
                className={
                  'iconBtn' +
                  (page === 'notifications' ? ' active' : '')
                }
                aria-label={
                  unread.notifications
                    ? `Open notifications, ${unread.notifications} unread`
                    : 'Open notifications'
                }
                onClick={() => go('notifications')}
              >
                <Bell size={20} />
                {unread.notifications > 0 && (
                  <span className="dot" />
                )}
              </button>

              <button
                className="avatar small"
                aria-label="Open my profile"
                onClick={() => go('profile')}
              >
                {initial}
              </button>

              <span className="accountName">
                {user.profile.name}{' '}
                <span className="roleBadge">
                  {administrator
                    ? 'Administrator'
                    : maintainer
                    ? 'Curator'
                    : 'Contributor'}
                </span>
              </span>

              <button
                className="btn ghost"
                onClick={logout}
              >
                <LogOut size={16} />
                Sign out
              </button>
            </>
          ) : (
            <>
              <button
                className="btn ghost"
                onClick={() => go('login')}
              >
                Login
              </button>

              <button
                className="btn primary"
                onClick={() => go('register')}
              >
                Register
              </button>
            </>
          )}
        </header>

        <main id="main" tabIndex="-1">
          {error && (
            <div
              role="alert"
              className="msg error globalError"
            >
              {error}
              <button
                className="textButton"
                onClick={() => setError('')}
              >
                Dismiss
              </button>
            </div>
          )}

          {!ready ? (
            <p className="container" role="status">
              Connecting to your workspace…
            </p>

          // PUBLIC PROJECT PAGES: NO LOGIN REQUIRED
          ) : page === 'about' ? (
            <AboutProject />

          ) : page === 'team' ? (
            <ProjectTeam />

          // LOGIN AND REGISTRATION
          ) : page === 'login' || page === 'register' ? (
            <Auth
              key={page}
              register={page === 'register'}
              go={go}
              onSuccess={u => {
                setUser(u);
                setError('');
                go('home');
              }}
            />

          // VISITOR WELCOME PAGE
          ) : !user ? (
            <section className="container welcome">
              <span className="eyebrow">
                CIVIC ISSUE MATCHMAKER
              </span>

              <h1>Find your next civic-tech contribution.</h1>

              <p>
                Match your technical skills and civic interests
                with real GitHub issues. Explore public-interest
                projects, understand recommendations, and track
                your contributions.
              </p>

              <button
                className="btn primary"
                onClick={() => go('register')}
              >
                Create your contributor profile
              </button>

              <p>
                Already a member?{' '}
                <button
                  className="textButton"
                  onClick={() => go('login')}
                >
                  Sign in
                </button>
              </p>
            </section>

          // EXISTING AUTHENTICATED PAGES
          ) : page === 'repository' ? (
            <Projects
              onError={onError}
              onOpen={path => {
                setSelectedProject(path);
                go('home');
              }}
            />

          ) : page === 'account' ? (
            <Account
              onError={onError}
              onDeleted={() => {
                setUser(null);
                go('login');
              }}
            />

          ) : page === 'notifications' ? (
            <Notifications
              onError={onError}
              onChanged={refreshUnread}
            />

          ) : page === 'messages' ? (
            <Messages
              onError={onError}
              onChanged={refreshUnread}
            />

          ) : page === 'participation' ? (
            <Participation onError={onError} />

          ) : page === 'maintainer' ? (
            maintainer ? (
              <Maintainer onError={onError} />
            ) : (
              <section className="container">
                <h1>Access restricted</h1>
                <p>Maintainer access is required.</p>
              </section>
            )

          ) : page === 'admin' ? (
            administrator ? (
              <Admin
                user={user}
                onUserChanged={setUser}
                onError={onError}
              />
            ) : (
              <section className="container">
                <h1>Access restricted</h1>
                <p>Administrator access is required.</p>
              </section>
            )

          ) : page === 'profile' ? (
            <Profile
              user={user}
              onSaved={setUser}
              onError={onError}
            />

          ) : (
            <Home
              selectedProject={selectedProject}
              key={page + user.id + selectedProject}
              savedOnly={page === 'saved'}
              repositoryOnly={page === 'repository'}
              user={user}
              go={go}
              onError={onError}
            />
          )}
        </main>
      </div>
    </div>
  );
}
