const QUICK = ["Python", "Accessibility (WCAG)", "React", "GIS", "Data Analysis"];

export default function Hero({ query, setQuery, onSearch }) {
  const submit = (e) => { e.preventDefault(); onSearch(query); };
  return (
    <section className="hero">
      <div className="panel">
        <form className="search" onSubmit={submit} role="search">
          <input
            aria-label="Search tech issues"
            placeholder="Search open civic-tech issues (e.g. Python, accessibility, GIS)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
        <div className="quick">
          Try:
          {QUICK.map((s) => (
            <button key={s} onClick={() => { setQuery(s); onSearch(s); }}>{s}</button>
          ))}
        </div>
      </div>
    </section>
  );
}
