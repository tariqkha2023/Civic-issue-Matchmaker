import React from "react";
import { SlidersHorizontal } from "lucide-react";
import { TOPICS, DIFFICULTIES, SKILLS, REPOS, SORTS } from "../options";

function Select({ label, value, options, onChange }) {
  return (
    <label>
      {label}
      <select value={value} onChange={e => onChange(e.target.value)}>
        {options.map(o => <option key={o}>{o}</option>)}
      </select>
    </label>
  );
}

export default function Filters({ filters, update, clearAll }) {
  return (
    <section className="filters" aria-label="Filters">
      <div className="filterHead">
        <strong><SlidersHorizontal size={17} /> Filters</strong>
        <button onClick={clearAll}>Clear all</button>
      </div>
      <div className="filterGrid">
        <Select label="Topic" value={filters.topic} options={TOPICS} onChange={v => update("topic", v)} />
        <Select label="Difficulty" value={filters.difficulty} options={DIFFICULTIES} onChange={v => update("difficulty", v)} />
        <Select label="Required skill" value={filters.skill} options={SKILLS} onChange={v => update("skill", v)} />
        <Select label="Repository" value={filters.repo} options={REPOS} onChange={v => update("repo", v)} />
        <Select label="Sort by" value={filters.sort} options={SORTS} onChange={v => update("sort", v)} />
        <label>
          Maximum effort <b>{filters.effort} hours</b>
          <input type="range" min="2" max="20" value={filters.effort} onChange={e => update("effort", +e.target.value)} />
        </label>
      </div>
    </section>
  );
}
