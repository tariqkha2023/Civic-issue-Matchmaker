import React, { useState } from "react";
import PasswordInput from "../components/PasswordInput";

export default function Register({ go }) {
  const [f, setF] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);
  const set = k => v => setF(s => ({ ...s, [k]: v }));

  const submit = e => {
    e.preventDefault();
    setOk(false);
    if (f.name.trim().length < 2) return setError("Enter your full name.");
    if (!/^\S+@\S+\.\S+$/.test(f.email)) return setError("Enter a valid email address.");
    if (f.password.length < 6) return setError("Password must be at least 6 characters.");
    if (f.password !== f.confirm) return setError("Passwords do not match.");
    setError("");
    setOk(true); // TODO: replace with real API call
  };

  return (
    <main className="authWrap">
      <form className="authCard" onSubmit={submit} noValidate>
        <h1>Create your account</h1>
        <p className="sub">Join and get matched with civic technology tasks.</p>
        <label>Full name
          <input value={f.name} onChange={e => set("name")(e.target.value)} placeholder="Your name" autoComplete="name" />
        </label>
        <label>Email
          <input type="email" value={f.email} onChange={e => set("email")(e.target.value)} placeholder="you@example.com" autoComplete="email" />
        </label>
        <label>Password
          <PasswordInput value={f.password} onChange={set("password")} placeholder="At least 6 characters" autoComplete="new-password" />
        </label>
        <label>Confirm password
          <PasswordInput value={f.confirm} onChange={set("confirm")} placeholder="Repeat password" autoComplete="new-password" />
        </label>
        {error && <div className="msg error">{error}</div>}
        {ok && <div className="msg success">Registration form is valid. Connect it to your backend to create the account.</div>}
        <button type="submit" className="btn primary full">Register</button>
        <p className="switch">Already have an account? <button type="button" onClick={() => go("login")}>Login</button></p>
      </form>
    </main>
  );
}
