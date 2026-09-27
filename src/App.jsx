import { useMemo, useState } from "react";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Filters from "./components/Filters";
import IssueCard from "./components/IssueCard";
import { ISSUES } from "./data";
import { filterIssues, toTerms } from "./utils";

export default function App() {
  // Search box text (live) vs. applied search (after pressing Search)
  const [query, setQuery] = useState("");
  const [applied, setApplied] = useState("");

  const [topics, setTopics] = useState([]);
  const [skills, setSkills] = useState([]);
  const [difficulty, setDifficulty] = useState("Any");
  const [effort, setEffort] = useState("Any");
  const [status, setStatus] = useState("Any");
  const [sort, setSort] = useState("match");
  const [joined, setJoined] = useState({});

  const toggle = (list, setList, v) =>
    setList(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);

  const terms = toTerms(applied);
  const results = useMemo(
    () => filterIssues(ISSUES, { terms, topics, skills, difficulty, effort, status, sort }),
    [applied, topics, skills, difficulty, effort, status, sort]
  );

  const reset = () => {
    setQuery(""); setApplied("");
    setTopics([]); setSkills([]); setDifficulty("Any"); setEffort("Any"); setStatus("Any"); setSort("match");
  };

  const hasActive = applied || topics.length || skills.length || difficulty !== "Any" || effort !== "Any" || status !== "Any";

  return (
    <>
      <Header />
      <Hero query={query} setQuery={setQuery} onSearch={(q) => setApplied(q)} />
      <main>
        <Filters
          topics={topics} skills={skills} difficulty={difficulty} effort={effort} status={status}
          onToggleTopic={(t) => toggle(topics, setTopics, t)}
          onToggleSkill={(s) => toggle(skills, setSkills, s)}
          setDifficulty={setDifficulty} setEffort={setEffort} setStatus={setStatus}
          onReset={reset}
        />

        <section aria-live="polite">
          <div className="top">
            <h2>{results.length} {results.length === 1 ? "issue" : "issues"} found</h2>
            <select aria-label="Sort by" value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="match">Best match</option>
              <option value="newest">Newest</option>
              <option value="claims">Fewest volunteers</option>
            </select>
          </div>

          {hasActive && (
            <div className="tags">
              {applied && <button className="tag" onClick={() => { setQuery(""); setApplied(""); }}>“{applied}” ✕</button>}
              {topics.map((t) => <button key={t} className="tag" onClick={() => toggle(topics, setTopics, t)}>{t} ✕</button>)}
              {skills.map((s) => <button key={s} className="tag" onClick={() => toggle(skills, setSkills, s)}>{s} ✕</button>)}
              {difficulty !== "Any" && <button className="tag" onClick={() => setDifficulty("Any")}>{difficulty} ✕</button>}
              {effort !== "Any" && <button className="tag" onClick={() => setEffort("Any")}>{effort} ✕</button>}
              {status !== "Any" && <button className="tag" onClick={() => setStatus("Any")}>{status} ✕</button>}
            </div>
          )}

          {results.length === 0 ? (
            <div className="empty">
              <h3>No issues match these filters</h3>
              <p>Remove a filter or try a broader skill such as “Python” or “accessibility”.</p>
              <button className="btn pri" onClick={reset}>Clear all filters</button>
            </div>
          ) : (
            results.map((i) => (
              <IssueCard
                key={i.id} issue={i} terms={terms} joined={!!joined[i.id]}
                onToggleJoin={() => setJoined({ ...joined, [i.id]: !joined[i.id] })}
              />
            ))
          )}
        </section>
      </main>
    </>
  );
}
