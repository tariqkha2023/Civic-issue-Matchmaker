import React, { useState } from "react";
import PasswordInput from "../components/PasswordInput";

export default function Login({ go }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);

  const submit = e => {
    e.preventDefault();
    setOk(false);
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Enter a valid email address.");
    if (password.length < 6) return setError("Password must be at least 6 characters.");
    setError("");
    setOk(true); // TODO: replace with real API call
  };

  return (
    <main className="authWrap">
      <form className="authCard" onSubmit={submit} noValidate>
        <h1>Welcome back</h1>
        <p className="sub">Log in to find civic tasks that fit you.</p>
        <label>Email
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
        </label>
        <label>Password
          <PasswordInput value={password} onChange={setPassword} placeholder="Your password" autoComplete="current-password" />
        </label>
        {error && <div className="msg error">{error}</div>}
        {ok && <div className="msg success">Login form is valid. Connect it to your backend to sign in.</div>}
        <button type="submit" className="btn primary full">Login</button>
        <p className="switch">New here? <button type="button" onClick={() => go("register")}>Create an account</button></p>
      </form>
    </main>
  );
}
