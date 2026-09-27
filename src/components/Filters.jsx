import { TOPICS, SKILLS, DIFFICULTIES, EFFORTS } from "../data";

export default function Filters({
  topics, skills, difficulty, effort, status,
  onToggleTopic, onToggleSkill, setDifficulty, setEffort, setStatus, onReset,
}) {
  return (
    <aside aria-label="Filters">
      <h2>Filters <button className="link" onClick={onReset}>Clear all</button></h2>

      <fieldset>
        <legend>Topic</legend>
        {TOPICS.map((t) => (
          <label className="chk" key={t}>
            <input type="checkbox" checked={topics.includes(t)} onChange={() => onToggleTopic(t)} />{t}
          </label>
        ))}
      </fieldset>

      <fieldset>
        <legend>Required skill</legend>
        {SKILLS.map((s) => (
          <label className="chk" key={s}>
            <input type="checkbox" checked={skills.includes(s)} onChange={() => onToggleSkill(s)} />{s}
          </label>
        ))}
      </fieldset>

      <fieldset>
        <legend><label htmlFor="difficulty">Difficulty</label></legend>
        <select id="difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
          {["Any", ...DIFFICULTIES].map((d) => <option key={d}>{d}</option>)}
        </select>
      </fieldset>

      <fieldset>
        <legend><label htmlFor="effort">Estimated effort</label></legend>
        <select id="effort" value={effort} onChange={(e) => setEffort(e.target.value)}>
          {["Any", ...EFFORTS].map((ef) => <option key={ef}>{ef}</option>)}
        </select>
      </fieldset>

      <fieldset>
        <legend><label htmlFor="status">Status</label></legend>
        <select id="status" value={status} onChange={(e) => setStatus(e.target.value)}>
          {["Any", "Open", "Claimed"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </fieldset>
    </aside>
  );
}
