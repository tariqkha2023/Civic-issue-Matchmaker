import React, { useState } from "react";

export default function Profile({ profile, setProfile }) {
  const [saved, setSaved] = useState(false);
  const update = (k, v) => { setSaved(false); setProfile(p => ({ ...p, [k]: v })); };
  return (
    <>
      <section className="pageHead">
        <div>
          <span className="eyebrow"></span>
          <h1></h1>
          <p></p>
        </div>
      </section>
      <section className="pageBody">
        <div className="twoCols">
          <div className="panel form">
            <h3>Volunteer profile</h3>
            <label>Display name<input value={profile.name} onChange={e => update("name", e.target.value)} /></label>
            <label>Experience level
              <select value={profile.level} onChange={e => update("level", e.target.value)}>
                <option>Beginner</option><option>Intermediate</option><option>Advanced</option>
              </select>
            </label>
            <label>Weekly availability<input type="number" value={profile.hours} onChange={e => update("hours", e.target.value)} /></label>
            <label>Interests<input value={profile.interests} onChange={e => update("interests", e.target.value)} /></label>
            <label>Skills<input value={profile.skills} onChange={e => update("skills", e.target.value)} /></label>
            {saved && <div className="msg success">Profile saved.</div>}
            <button className="btn primary" onClick={() => setSaved(true)}>Save profile</button>
          </div>
          <div className="panel">
            <h3>Match profile</h3>
            <div className="bigStat">82%</div>
            <p>Complete availability and repository preferences to improve recommendation explanations.</p>
            <hr />
            <h4></h4>
           
          </div>
        </div>
      </section>
    </>
  );
}
