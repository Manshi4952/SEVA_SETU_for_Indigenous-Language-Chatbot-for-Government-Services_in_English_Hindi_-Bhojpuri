/**
 * pages/AdminPage.jsx  –  Admin dashboard: stats, users, logs.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, MessageSquare, BookOpen, BarChart2, RefreshCw, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import api from "../utils/api";

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-white dark:bg-charcoal rounded-2xl p-6 shadow-card border border-blue-50 dark:border-white/10">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-charcoal/50 dark:text-white/50 font-medium">{label}</span>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
             style={{ background: `${color}15` }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
      <div className="font-display text-3xl font-bold text-charcoal dark:text-white">{value}</div>
    </div>
  );
}

export default function AdminPage() {
  const { user, isAuthenticated, language } = useStore();
  const navigate = useNavigate();
  const [stats, setStats]   = useState(null);
  const [users, setUsers]   = useState([]);
  const [logs,  setLogs]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("stats");

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "admin") {
      navigate("/");
      return;
    }
    loadAll();
  }, [isAuthenticated]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, logsRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/users"),
        api.get("/admin/logs"),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setLogs(logsRes.data);
    } catch {
      toast.error("Failed to load admin data");
    } finally {
      setLoading(false);
    }
  };

  const toggleUser = async (uid) => {
    try {
      const { data } = await api.patch(`/admin/users/${uid}/toggle-active`);
      toast.success(`User ${data.is_active ? "enabled" : "disabled"}`);
      loadAll();
    } catch {
      toast.error("Action failed");
    }
  };

  if (loading) return (
    <div className="flex justify-center py-32">
      <Loader2 size={40} className="animate-spin text-ashoka" />
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl font-bold text-charcoal dark:text-white">
            Admin Dashboard
          </h1>
          <p className="text-charcoal/50 dark:text-white/50 text-sm mt-1">SevaSetu Control Panel</p>
        </div>
        <button onClick={loadAll}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-ashoka/10 text-ashoka
                     hover:bg-ashoka/20 text-sm font-medium transition-all">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Users}        label="Total Users"         value={stats.total_users}         color="#0A3D91" />
          <StatCard icon={MessageSquare} label="Conversations"      value={stats.total_conversations} color="#FF6B2B" />
          <StatCard icon={BarChart2}    label="Messages Sent"       value={stats.total_messages}      color="#138808" />
          <StatCard icon={BookOpen}     label="Active Schemes"      value={stats.total_schemes}       color="#7C3AED" />
        </div>
      )}

      {/* Language distribution */}
      {stats && (
        <div className="bg-white dark:bg-charcoal rounded-2xl p-6 shadow-card border border-blue-50
                        dark:border-white/10 mb-8">
          <h2 className="font-bold text-charcoal dark:text-white mb-4">Language Distribution</h2>
          <div className="flex gap-4 flex-wrap">
            {Object.entries(stats.language_distribution).map(([lang, count]) => (
              <div key={lang} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full"
                     style={{ background: lang === "hindi" ? "#FF6B2B" : lang === "bhojpuri" ? "#138808" : "#0A3D91" }} />
                <span className="text-sm text-charcoal/70 dark:text-white/70 capitalize">{lang}:</span>
                <span className="text-sm font-bold text-charcoal dark:text-white">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-blue-50 dark:border-white/10">
        {["Users", "Logs"].map((t) => (
          <button key={t} onClick={() => setTab(t.toLowerCase())}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-all ${
              tab === t.toLowerCase()
                ? "border-ashoka text-ashoka"
                : "border-transparent text-charcoal/50 dark:text-white/50"
            }`}>
            {t}
          </button>
        ))}
      </div>

      {/* Users table */}
      {tab === "users" && (
        <div className="bg-white dark:bg-charcoal rounded-2xl shadow-card border border-blue-50
                        dark:border-white/10 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-blue-50 dark:bg-white/5">
              <tr>
                {["ID", "Name", "Email", "Language", "Role", "Status", "Action"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-charcoal/60 dark:text-white/60 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-50 dark:divide-white/5">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-blue-50/50 dark:hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3 text-charcoal/50 dark:text-white/50">{u.id}</td>
                  <td className="px-4 py-3 font-medium text-charcoal dark:text-white">{u.full_name || "—"}</td>
                  <td className="px-4 py-3 text-charcoal/70 dark:text-white/70">{u.email}</td>
                  <td className="px-4 py-3 capitalize">{u.preferred_lang}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      u.role === "admin" ? "bg-saffron/10 text-saffron" : "bg-blue-50 dark:bg-white/10 text-ashoka"
                    }`}>{u.role}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      u.is_active ? "bg-jade/10 text-jade" : "bg-red-50 text-red-500"
                    }`}>{u.is_active ? "Active" : "Disabled"}</span>
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => toggleUser(u.id)}
                      className="text-xs px-3 py-1 rounded-lg bg-charcoal/5 dark:bg-white/10
                                 hover:bg-charcoal/10 text-charcoal/70 dark:text-white/70 transition-all">
                      Toggle
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Logs table */}
      {tab === "logs" && (
        <div className="bg-white dark:bg-charcoal rounded-2xl shadow-card border border-blue-50
                        dark:border-white/10 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-blue-50 dark:bg-white/5">
              <tr>
                {["ID", "Admin", "Action", "Details", "Time"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-charcoal/60 dark:text-white/60 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-50 dark:divide-white/5">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-blue-50/50 dark:hover:bg-white/5 transition-colors">
                  <td className="px-4 py-3 text-charcoal/50 dark:text-white/50">{l.id}</td>
                  <td className="px-4 py-3 text-charcoal/70 dark:text-white/70">{l.admin_id}</td>
                  <td className="px-4 py-3 font-medium text-charcoal dark:text-white">{l.action}</td>
                  <td className="px-4 py-3 text-charcoal/50 dark:text-white/50 font-mono text-xs">
                    {JSON.stringify(l.details)}
                  </td>
                  <td className="px-4 py-3 text-charcoal/50 dark:text-white/50">
                    {new Date(l.created_at).toLocaleString("en-IN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
