import React from "react";
import { ROLES } from "../roles";

export default function RoleHome({ role, onSignOut }) {
  const cfg = ROLES[role];
  return (
    <main className="container">
      <section className="panel">
        <span className="eyebrow">CIVIC ISSUE MATCHMAKER</span>
        <h1>{cfg.title}</h1>
        <p className="sub">{cfg.subtitle}</p>
        <div className="msg success">Access granted. Your {cfg.label.toLowerCase()} tools will appear here.</div>
        <button className="btn primary" onClick={onSignOut}>Sign out</button>
      </section>
    </main>
  );
}
