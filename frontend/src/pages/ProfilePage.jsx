import { useState } from "react";
import { authHeaders, request } from "../api";

export default function ProfilePage({ token, user, onMessage, onError }) {
  const [name, setName] = useState(user.name);
  const [password, setPassword] = useState("");
  async function save(event) { event.preventDefault(); try { await request("/users/me", { method: "PATCH", headers: authHeaders(token), body: JSON.stringify({ name, ...(password ? { password } : {}) }) }); setPassword(""); onMessage("Profile updated."); } catch (err) { onError(err.message); } }
  return <div className="page-stack narrow-page"><section className="split-heading"><div><p className="eyebrow orange">YOUR IDENTITY</p><h2>Profile settings</h2><p className="muted">Keep your workspace identity and access details current.</p></div><div className="profile-large-avatar">{user.name.slice(0, 1).toUpperCase()}</div></section><section className="panel form-panel"><div className="profile-meta"><span className="role-badge">{user.role}</span><span className="muted">{user.email}</span></div><form onSubmit={save}><label>Display name<input value={name} onChange={(event) => setName(event.target.value)} required /></label><label>New password<input type="password" minLength="8" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Leave blank to keep your password" /></label><button>Save profile</button></form></section></div>;
}

