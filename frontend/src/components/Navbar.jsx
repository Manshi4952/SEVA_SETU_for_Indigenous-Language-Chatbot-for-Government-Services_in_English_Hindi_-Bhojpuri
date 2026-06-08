/**
 * components/Navbar.jsx  –  Top navigation bar with tricolor accent.
 */
import { Link, useNavigate } from "react-router-dom";
import { Sun, Moon, MessageCircle, Home, BookOpen, Info, LogOut, Settings } from "lucide-react";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";
import clsx from "clsx";

const LANGUAGES = [
  { value: "hindi",    label: "हिंदी",    flag: "🇮🇳" },
  { value: "bhojpuri", label: "भोजपुरी",  flag: "🌾" },
  { value: "english",  label: "English",  flag: "🔤" },
];

export default function Navbar() {
  const { language, setLanguage, darkMode, toggleDark, isAuthenticated, logout, user } = useStore();
  const navigate = useNavigate();
  const tx = (key) => t(key, language);

  const handleLogout = () => { logout(); navigate("/"); };

  return (
    <nav className={clsx(
      "sticky top-0 z-50 glass border-b",
      darkMode ? "border-white/10" : "border-blue-100"
    )}>
      {/* Tricolor top stripe */}
      <div className="h-1 w-full"
           style={{ background: "linear-gradient(90deg, #FF6B2B 33.3%, #fff 33.3% 66.6%, #138808 66.6%)" }} />

      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-display font-bold text-xl text-ashoka">
          <span className="text-2xl">🏛️</span>
          <span className="hidden sm:block">
            <span className="text-saffron">सेवा</span>
            <span className="text-ashoka">सेतु</span>
          </span>
        </Link>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-1 ml-4">
          {[
            { to: "/",        icon: Home,          label: tx("home")    },
            { to: "/chat",    icon: MessageCircle, label: tx("chat")    },
            { to: "/schemes", icon: BookOpen,       label: tx("schemes") },
            { to: "/about",   icon: Info,           label: tx("about")  },
          ].map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                         text-charcoal/70 hover:text-ashoka hover:bg-ashoka/5 transition-all">
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </div>

        <div className="flex-1" />

        {/* Language selector */}
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="text-sm border border-blue-100 rounded-lg px-2 py-1 bg-white dark:bg-charcoal
                     text-charcoal dark:text-white focus:outline-none focus:ring-2 focus:ring-ashoka/30"
        >
          {LANGUAGES.map(({ value, label, flag }) => (
            <option key={value} value={value}>{flag} {label}</option>
          ))}
        </select>

        {/* Dark mode */}
        <button onClick={toggleDark}
          className="p-2 rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-all">
          {darkMode ? <Sun size={18} className="text-yellow-400" />
                    : <Moon size={18} className="text-ashoka" />}
        </button>

        {/* Auth buttons */}
        {isAuthenticated ? (
          <div className="flex items-center gap-2">
            {user?.role === "admin" && (
              <Link to="/admin"
                className="hidden sm:flex items-center gap-1 text-sm text-saffron hover:underline">
                <Settings size={14} /> Admin
              </Link>
            )}
            <button onClick={handleLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium
                         text-red-500 hover:bg-red-50 transition-all">
              <LogOut size={15} />
              <span className="hidden sm:block">{tx("logout")}</span>
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link to="/login"
              className="px-3 py-1.5 text-sm font-medium text-ashoka hover:text-ashoka-dark transition-all">
              {tx("login")}
            </Link>
            <Link to="/register"
              className="px-4 py-1.5 bg-saffron text-white rounded-lg text-sm font-medium
                         hover:bg-saffron-dark shadow-glow transition-all">
              {tx("register")}
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
