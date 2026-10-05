import React, { useState, useEffect } from "react";
import { Landmark } from "lucide-react";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";

const routes = ["home", "login", "register"];
const fromHash = () => {
  const h = window.location.hash.replace("#/", "");
  return routes.includes(h) ? h : "home";
};

export default function App() {
  const [page, setPage] = useState(fromHash());

  useEffect(() => {
    const onHash = () => setPage(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = p => { window.location.hash = "#/" + p; };

  return (
    <div className="page">
      <header className="brand">
        <button className="brandLink" onClick={() => go("home")}>
          <span className="brandIcon"><Landmark size={20} /></span>
          <span>Civic Issue Matchmaker</span>
        </button>
        <div className="authBtns">
          <button className={"btn ghost" + (page === "login" ? " active" : "")} onClick={() => go("login")}>Login</button>
          <button className={"btn primary" + (page === "register" ? " active" : "")} onClick={() => go("register")}>Register</button>
        </div>
      </header>
      {page === "home" && <Home />}
      {page === "login" && <Login go={go} />}
      {page === "register" && <Register go={go} />}
    </div>
  );
}
