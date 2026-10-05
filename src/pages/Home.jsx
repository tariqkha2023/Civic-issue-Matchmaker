import React, { useEffect, useMemo, useState } from "react";
import SearchBar from "../components/SearchBar";
import Filters from "../components/Filters";
import IssueCard from "../components/IssueCard";
import { DEFAULT_FILTERS } from "../options";

export default function Home() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [joined, setJoined] = useState(new Set());

  const update = (key, value) =>
    setFilters((f) => ({ ...f, [key]: value }));

  useEffect(() => {
    fetch("http://127.0.0.1:8000/tasks")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load tasks");
        }

        return response.json();
      })
      .then((tasks) => {
        const mappedIssues = tasks.map((task) => ({
          id: task.id,
          title: task.title,

          topic: task.source === "github" ? "GitHub" : "GitLab",

          org: task.repository.includes("/")
            ? task.repository.split("/")[0]
            : task.repository,

          repo: task.repository,

          difficulty: "Beginner",
          effort: "Unknown",
          claims: 0,
          days: 0,
          score: 0,

          desc: task.description || "No description provided.",

          skills: task.labels || [],

          url: task.url,

          status:
            task.status === "open" || task.status === "opened"
              ? "Open"
              : task.status.charAt(0).toUpperCase() +
                task.status.slice(1),
        }));

        setIssues(mappedIssues);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Could not load tasks from the backend.");
        setLoading(false);
      });
  }, []);

  const terms = useMemo(() => {
    return filters.query
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
  }, [filters.query]);

  const filteredIssues = useMemo(() => {
    const query = filters.query.toLowerCase().trim();

    if (!query) {
      return issues;
    }

    return issues.filter((issue) => {
      const searchableText = [
        issue.title,
        issue.desc,
        issue.repo,
        issue.org,
        ...issue.skills,
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(query);
    });
  }, [issues, filters.query]);

  const toggleJoin = (id) => {
    setJoined((current) => {
      const next = new Set(current);

      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }

      return next;
    });
  };

  return (
    <main className="container">
      <SearchBar
        value={filters.query}
        onChange={(v) => update("query", v)}
      />

      <Filters
        filters={filters}
        update={update}
        clearAll={() => setFilters(DEFAULT_FILTERS)}
      />

      {loading && <p>Loading tasks...</p>}

      {error && <p>{error}</p>}

      {!loading && !error && filteredIssues.length === 0 && (
        <p>No tasks found.</p>
      )}

      {!loading &&
        !error &&
        filteredIssues.map((issue) => (
          <IssueCard
            key={issue.id}
            issue={issue}
            terms={terms}
            joined={joined.has(issue.id)}
            onToggleJoin={() => toggleJoin(issue.id)}
          />
        ))}
    </main>
  );
}