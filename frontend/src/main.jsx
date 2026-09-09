import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { authHeaders, request } from "./api";
import AppShell from "./components/AppShell";
import AuthPage from "./pages/AuthPage";
import CreatePage from "./pages/CreatePage";
import DashboardPage from "./pages/DashboardPage";
import ExplorePage from "./pages/ExplorePage";
import PeoplePage from "./pages/PeoplePage";
import ProfilePage from "./pages/ProfilePage";
import SchedulePage from "./pages/SchedulePage";

function App() {
  const [token, setToken] = useState(localStorage.getItem("mashbot_token"));
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [page, setPage] = useState("dashboard");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const fail = (text) => { setError(text); setMessage(""); };
  const notify = (text) => { setMessage(text); setError(""); };
  const headers = token ? authHeaders(token) : {};

  async function loadData() {
    if (!token) return;
    try {
      const profile = await request("/users/me", { headers });
      const [items, people] = await Promise.all([request("/campaigns", { headers }), profile.role === "admin" ? request("/users", { headers }) : Promise.resolve([])]);
      setUser(profile); setCampaigns(items); setUsers(people);
    } catch (err) {
      fail(err.message); localStorage.removeItem("mashbot_token"); setToken(null); setUser(null);
    }
  }
  useEffect(() => { loadData(); }, [token]);
  useEffect(() => { if (message || error) { const timer = setTimeout(() => { setMessage(""); setError(""); }, 5000); return () => clearTimeout(timer); } }, [message, error]);
  function login(value) { localStorage.setItem("mashbot_token", value); setToken(value); }
  function logout() { localStorage.removeItem("mashbot_token"); setToken(null); setUser(null); }
  if (!token || !user) return <AuthPage onLogin={login} />;
  const refresh = () => loadData();
  let content;
  if (page === "dashboard") content = <DashboardPage token={token} onError={fail} onNavigate={setPage} />;
  if (page === "create") content = <CreatePage token={token} user={user} campaigns={campaigns} refresh={refresh} onMessage={notify} onError={fail} />;
  if (page === "schedule") content = <SchedulePage token={token} user={user} campaigns={campaigns} refresh={refresh} onMessage={notify} onError={fail} />;
  if (page === "explore") content = <ExplorePage token={token} onMessage={notify} onError={fail} />;
  if (page === "profile") content = <ProfilePage token={token} user={user} onMessage={notify} onError={fail} />;
  if (page === "people") content = <PeoplePage token={token} users={users} setUsers={setUsers} onMessage={notify} onError={fail} />;
  return <AppShell user={user} page={page} setPage={setPage} onSignOut={logout}><div className="toast-area">{message && <p className="success banner">{message}</p>}{error && <p className="error banner">{error}</p>}</div>{content}</AppShell>;
}

createRoot(document.getElementById("root")).render(<App />);

