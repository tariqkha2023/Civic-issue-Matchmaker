import React from "react";
import { Search } from "lucide-react";

export default function SearchBar({ value, onChange }) {
  return (
    <div className="searchBar">
      <Search size={18} />
      <input
        aria-label="Search tasks"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Search tasks, skills, or repositories"
      />
    </div>
  );
}
