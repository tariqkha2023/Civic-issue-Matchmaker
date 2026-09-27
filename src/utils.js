import { DIFFICULTY_RANK } from "./data";

export const norm = (s) => s.toLowerCase().trim();
export const toTerms = (q) => norm(q).split(/[\s,]+/).filter(Boolean);
const haystack = (i) => norm([i.title, i.desc, i.topic, i.org, i.skills.join(" ")].join(" "));

export function matchScore(issue, terms) {
  if (!terms.length) return 60 + DIFFICULTY_RANK[issue.difficulty] * 5;
  const hits = terms.filter((t) => haystack(issue).includes(t)).length;
  return Math.round(40 + (60 * hits) / terms.length);
}

export function filterIssues(issues, { terms, topics, skills, difficulty, effort, status, sort }) {
  const list = issues
    .filter((i) => {
      if (topics.length && !topics.includes(i.topic)) return false;
      if (skills.length && !skills.some((s) => i.skills.includes(s))) return false;
      if (difficulty !== "Any" && i.difficulty !== difficulty) return false;
      if (effort !== "Any" && i.effort !== effort) return false;
      if (status !== "Any" && i.status !== status) return false;
      if (terms.length && !terms.some((t) => haystack(i).includes(t))) return false;
      return true;
    })
    .map((i) => ({ ...i, score: matchScore(i, terms) }));

  if (sort === "match") list.sort((a, b) => b.score - a.score || DIFFICULTY_RANK[a.difficulty] - DIFFICULTY_RANK[b.difficulty]);
  if (sort === "newest") list.sort((a, b) => a.days - b.days);
  if (sort === "claims") list.sort((a, b) => a.claims - b.claims);
  return list;
}
