import { norm } from "../utils";

export default function IssueCard({ issue, terms, joined, onToggleJoin }) {
  return (
    <article className="card">
      <div>
        <h3><a href={issue.url} target="_blank" rel="noreferrer">{issue.title}</a></h3>
        <div className="meta">
          <span>{issue.topic}</span>
          <span>{issue.org}</span>
          <span>{issue.effort}</span>
          <span>{issue.claims} {issue.claims === 1 ? "volunteer" : "volunteers"} working on this</span>
          <span>Posted {issue.days} {issue.days === 1 ? "day" : "days"} ago</span>
        </div>
        <p>{issue.desc}</p>
        <div className="skills">
          {issue.skills.map((s) => (
            <span key={s} className={terms.some((t) => norm(s).includes(t)) ? "hit" : ""}>{s}</span>
          ))}
        </div>
      </div>
      <div className="side">
        <div className="score">{issue.score}%<small>match</small></div>
        <span className={`urg ${issue.difficulty}`}>{issue.difficulty}</span>
        <span className={`status ${issue.status.toLowerCase()}`}>{issue.status}</span>
        <button className={`btn ${joined ? "" : "pri"}`} onClick={onToggleJoin} disabled={issue.status === "Claimed" && !joined}>
          {joined ? "Claimed ✓" : issue.status === "Claimed" ? "Already claimed" : "Claim task"}
        </button>
      </div>
    </article>
  );
}
