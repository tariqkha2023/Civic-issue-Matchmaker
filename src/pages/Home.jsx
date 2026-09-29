import React, { useState } from "react";
import SearchBar from "../components/SearchBar";
import Filters from "../components/Filters";
import { DEFAULT_FILTERS } from "../options";

export default function Home() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const update = (key, value) => setFilters(f => ({ ...f, [key]: value }));
  return (
    <main className="container">
      <SearchBar value={filters.query} onChange={v => update("query", v)} />
      <Filters filters={filters} update={update} clearAll={() => setFilters(DEFAULT_FILTERS)} />
    </main>
  );
}
