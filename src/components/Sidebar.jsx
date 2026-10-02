import React from "react";
import { Wrench, Settings } from "lucide-react";
import civicLogo from "../assets/civic-logo.png";

const tools = [
  ["maintainer", "Maintainer", Wrench],
  ["admin", "Administration", Settings],
];

export default function Sidebar({ page, go }) {
  return (
    <aside className="sidebar">
      <button
        className="sideBrand"
        onClick={() => go("home")}
        aria-label="Civic Issue Matchmaker home"
      >
        <img
          src={civicLogo}
          alt="Civic Issue Matchmaker"
          className="sidebarLogo"
        />
      </button>

      <div className="eyebrow sideLabel">ROLE TOOLS</div>

      {tools.map(([id, label, Icon]) => (
        <button
          key={id}
          className={"navItem" + (page === id ? " active" : "")}
          onClick={() => go(id)}
          title={label}
          aria-label={label}
        >
          <Icon size={18} />
          <span>{label}</span>
        </button>
      ))}
    </aside>
  );
}
