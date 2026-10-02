import React, { useState } from "react";
import { Lock } from "lucide-react";
import PasswordInput from "../components/PasswordInput";
import { ROLES } from "../roles";

export default function RoleLogin({ role, onSuccess }) {
  const cfg = ROLES[role];
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = e => {
    e.preventDefault();
    // TODO: replace with a real API call
    const ok = username.trim().toLowerCase() === cfg.username && password === cfg.password;
    if (!ok) return setError("Incorrect username or password.");
    setError("");
    onSuccess(role);
  };

  return (
    <main className="authWrap">
      <form className="authCard" onSubmit={submit} noValidate>
        <span className="lockIcon"><Lock size={20} /></span>
        <h1>{cfg.label} access</h1>
        <p className="sub">Enter your {cfg.label.toLowerCase()} username and password to continue.</p>
        <label>Username
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" autoComplete="username" autoFocus />
        </label>
        <label>Password
          <PasswordInput value={password} onChange={setPassword} placeholder="Password" autoComplete="current-password" />
        </label>
        {error && <div className="msg error">{error}</div>}
        <button type="submit" className="btn primary full">Sign in</button>
      </form>
    </main>
  );
}
