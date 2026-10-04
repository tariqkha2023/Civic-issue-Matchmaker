import React, { useState, useEffect } from "react";
import { Bell } from "lucide-react";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RoleLogin from "./pages/RoleLogin";
import RoleHome from "./pages/RoleHome";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import { notificationsSeed, profileSeed } from "./data";

const routes = ["home", "login", "register", "maintainer", "admin", "notifications", "profile"];
const fromHash = () => {
  const h = window.location.hash.replace("#/", "");
  return routes.includes(h) ? h : "home";
};

export default function App() {
  const [page, setPage] = useState(fromHash());
  // Kept in memory only, so a page refresh asks for the username and password again.
  const [access, setAccess] = useState({ maintainer: false, admin: false });

  const [notifications, setNotifications] = useState(notificationsSeed);
  const [profile, setProfile] = useState(profileSeed);
  const unread = notifications.filter(n => !n.read).length;

  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = p => { window.location.hash = "#/" + p; };
  const setRoleAccess = (role, value) => setAccess(a => ({ ...a, [role]: value }));

  const initials = profile.name.split(" ").filter(Boolean).map(w => w[0]).join("").slice(0, 2).toUpperCase() || "?";

  const isRole = page === "maintainer" || page === "admin";

  return (
    <div className="app">
      <Sidebar page={page} go={go} notificationCount={unread} />
      <div className="workspace">
        <header className="topbar">
          <div className="authBtns">
            <button className={"btn ghost" + (page === "login" ? " active" : "")} onClick={() => go("login")}>Login</button>
            <button className={"btn primary" + (page === "register" ? " active" : "")} onClick={() => go("register")}>Register</button>
          </div>
          <button className={"iconBtn" + (page === "notifications" ? " active" : "")} aria-label="Notifications" title="Notifications" onClick={() => go("notifications")}>
            <Bell size={20} />{unread ? <span className="dot" /> : null}
          </button>
          <button className="avatar small" aria-label="My profile" title="My profile" onClick={() => go("profile")}>{initials}</button>
        </header>
        {page === "home" && <Home />}
        {page === "login" && <Login go={go} />}
        {page === "register" && <Register go={go} />}
        {page === "notifications" && <Notifications notifications={notifications} setNotifications={setNotifications} />}
        {page === "profile" && <Profile profile={profile} setProfile={setProfile} />}
        {isRole && (access[page]
          ? <RoleHome role={page} onSignOut={() => setRoleAccess(page, false)} />
          : <RoleLogin key={page} role={page} onSuccess={r => setRoleAccess(r, true)} />)}
      </div>
    </div>
  );
}
