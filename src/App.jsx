import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import RoleLogin from "./pages/RoleLogin";
import RoleHome from "./pages/RoleHome";

const routes = ["home", "login", "register", "maintainer", "admin"];
const fromHash = () => {
  const h = window.location.hash.replace("#/", "");
  return routes.includes(h) ? h : "home";
};

export default function App() {
  const [page, setPage] = useState(fromHash());
  // Kept in memory only, so a page refresh asks for the username and password again.
  const [access, setAccess] = useState({ maintainer: false, admin: false });

  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = p => { window.location.hash = "#/" + p; };
  const setRoleAccess = (role, value) => setAccess(a => ({ ...a, [role]: value }));

  const isRole = page === "maintainer" || page === "admin";

  return (
    <div className="app">
      <Sidebar page={page} go={go} />
      <div className="workspace">
        <header className="topbar">
          <div className="authBtns">
            <button className={"btn ghost" + (page === "login" ? " active" : "")} onClick={() => go("login")}>Login</button>
            <button className={"btn primary" + (page === "register" ? " active" : "")} onClick={() => go("register")}>Register</button>
          </div>
        </header>
        {page === "home" && <Home />}
        {page === "login" && <Login go={go} />}
        {page === "register" && <Register go={go} />}
        {isRole && (access[page]
          ? <RoleHome role={page} onSignOut={() => setRoleAccess(page, false)} />
          : <RoleLogin key={page} role={page} onSuccess={r => setRoleAccess(r, true)} />)}
      </div>
    </div>
  );
}
