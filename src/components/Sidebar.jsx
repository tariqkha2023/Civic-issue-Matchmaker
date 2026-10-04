import React from "react";
import { Bell, UserRound, Wrench, Settings } from "lucide-react";
import civicLogo from "../assets/civic-logo.png";

const workspace = [
  ["notifications", "Notifications", Bell],
  ["profile", "My profile", UserRound],
];

const tools = [
  ["maintainer", "Maintainer", Wrench],
  ["admin", "Administration", Settings],
];

export default function Sidebar({ page, go, notificationCount = 0 }) {
  const item = ([id, label, Icon]) => (
    <button
      key={id}
      className={"navItem" + (page === id ? " active" : "")}
      onClick={() => go(id)}
      title={label}
      aria-label={label}
    >
      <Icon size={18} />
      <span>{label}</span>
      {id === "notifications" && notificationCount > 0 ? <b className="count">{notificationCount}</b> : null}
    </button>
  );

  return (
    <aside className="sidebar">
      <button
        className="sideBrand"
        onClick={() => go("home")}
        aria-label="Civic Issue Matchmaker home"
      >
        <img src={civicLogo} alt="Civic Issue Matchmaker" className="sidebarLogo" />
      </button>

      <div className="eyebrow sideLabel">VOLUNTEER WORKSPACE</div>
      {workspace.map(item)}

      <div className="eyebrow sideLabel tools">ROLE TOOLS</div>
      {tools.map(item)}
    </aside>
  );
}
