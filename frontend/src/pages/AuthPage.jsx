import { useState } from "react";
import { request } from "../api";

export default function AuthPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault(); setError(""); setMessage("");
    const form = new FormData(event.currentTarget);
    try {
      if (mode === "register") {
        await request("/auth/register", { method: "POST", body: JSON.stringify({ email: form.get("email"), name: form.get("name"), password: form.get("password") }) });
        setMode("login"); setMessage("Account created. Sign in to continue."); return;
      }
      const body = new URLSearchParams({ username: form.get("email"), password: form.get("password") });
      const data = await request("/auth/login", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body });
      onLogin(data.access_token);
    } catch (err) { setError(err.message); }
  }
  return <main className="auth"><section className="hero"><p className="eyebrow">MASHBOT / CAMPAIGN CONTROL</p><h1>Turn campaign ideas into approved moments.</h1><p>A focused workspace for creating, reviewing, scheduling, and exploring social campaigns.</p><div className="hero-note"><span>01</span><span>Create with clarity</span><span>02</span><span>Approve with confidence</span></div></section><section className="auth-card"><p className="eyebrow">{mode === "login" ? "WELCOME BACK" : "JOIN THE WORKSPACE"}</p><h2>{mode === "login" ? "Sign in" : "Create account"}</h2><form onSubmit={submit}>{mode === "register" && <input name="name" placeholder="Name" required />}<input name="email" type="email" placeholder="Email" required /><input name="password" type="password" minLength="8" placeholder="Password (8+ characters)" required /><button>{mode === "login" ? "Sign in" : "Register"}</button></form>{mode === "login" ? <p className="switch">New here? <button className="link-button" onClick={() => setMode("register")}>Create an account</button></p> : <p className="switch">Already registered? <button className="link-button" onClick={() => setMode("login")}>Sign in</button></p>}{message && <p className="success">{message}</p>}{error && <p className="error">{error}</p>}</section></main>;
}

