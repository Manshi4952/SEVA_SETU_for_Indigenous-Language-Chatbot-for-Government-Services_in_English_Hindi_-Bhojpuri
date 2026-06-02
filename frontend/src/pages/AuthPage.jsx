/**
 * pages/AuthPage.jsx  –  Login and Register forms.
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Loader2, LogIn, UserPlus } from "lucide-react";
import toast from "react-hot-toast";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";

function InputField({ label, type = "text", value, onChange, placeholder, required }) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";

  return (
    <div>
      <label className="block text-sm font-medium text-charcoal/70 dark:text-white/70 mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          type={isPassword && show ? "text" : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className="w-full px-4 py-2.5 rounded-xl border border-blue-100 dark:border-white/20
                     bg-white dark:bg-charcoal text-charcoal dark:text-white text-sm
                     placeholder:text-charcoal/30 dark:placeholder:text-white/30
                     focus:outline-none focus:ring-2 focus:ring-ashoka/30 transition-all"
        />
        {isPassword && (
          <button type="button" onClick={() => setShow((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-charcoal/40 hover:text-ashoka transition-colors">
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Login ───────────────────────────────────────────────────────────────────
export function LoginPage() {
  const { login, language } = useStore();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const tx = (k) => t(k, language);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.email, form.password);
      toast.success(language === "hindi" ? "लॉगिन सफल!" : "Login successful!");
      navigate("/chat");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-hero-pattern">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-charcoal rounded-3xl shadow-card border border-blue-50
                        dark:border-white/10 overflow-hidden">
          {/* Top gradient */}
          <div className="h-2" style={{ background: "linear-gradient(90deg, #FF6B2B, #0A3D91, #138808)" }} />

          <div className="p-8">
            <div className="text-center mb-8">
              <div className="text-4xl mb-3">🏛️</div>
              <h1 className="font-display text-2xl font-bold text-charcoal dark:text-white">
                {language === "hindi" ? "SevaSetu में लॉगिन करें" : "Login to SevaSetu"}
              </h1>
              <p className="text-sm text-charcoal/50 dark:text-white/50 mt-1">
                {language === "hindi" ? "अपना खाता एक्सेस करें" : "Access your account"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <InputField label="Email" type="email" value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="you@example.com" required />
              <InputField label={language === "hindi" ? "पासवर्ड" : "Password"}
                type="password" value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="••••••••" required />

              <button type="submit" disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 bg-ashoka text-white
                           rounded-xl font-semibold hover:bg-ashoka-dark shadow-glow-blue
                           disabled:opacity-60 transition-all active:scale-95 mt-2">
                {loading ? <Loader2 size={18} className="animate-spin" /> : <LogIn size={18} />}
                {tx("login")}
              </button>
            </form>

            <p className="text-center text-sm text-charcoal/50 dark:text-white/50 mt-6">
              {language === "hindi" ? "खाता नहीं है?" : "Don't have an account?"}
              {" "}
              <Link to="/register" className="text-saffron font-medium hover:underline">
                {tx("register")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Register ─────────────────────────────────────────────────────────────────
export function RegisterPage() {
  const { register: registerUser, language } = useStore();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "", email: "", phone: "", password: "", preferred_lang: "hindi",
  });
  const [loading, setLoading] = useState(false);
  const tx = (k) => t(k, language);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await registerUser(form);
      toast.success(language === "hindi" ? "पंजीकरण सफल!" : "Registration successful!");
      navigate("/chat");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10 bg-hero-pattern">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-charcoal rounded-3xl shadow-card border border-blue-50
                        dark:border-white/10 overflow-hidden">
          <div className="h-2" style={{ background: "linear-gradient(90deg, #FF6B2B, #0A3D91, #138808)" }} />

          <div className="p-8">
            <div className="text-center mb-8">
              <div className="text-4xl mb-3">🌟</div>
              <h1 className="font-display text-2xl font-bold text-charcoal dark:text-white">
                {language === "hindi" ? "SevaSetu से जुड़ें" : "Join SevaSetu"}
              </h1>
              <p className="text-sm text-charcoal/50 dark:text-white/50 mt-1">
                {language === "hindi" ? "मुफ्त खाता बनाएं" : "Create your free account"}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <InputField label={language === "hindi" ? "पूरा नाम" : "Full Name"}
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                placeholder={language === "hindi" ? "अपना नाम लिखें" : "Your full name"} required />

              <InputField label="Email" type="email" value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="you@example.com" required />

              <InputField label={language === "hindi" ? "मोबाइल नंबर" : "Phone"}
                value={form.phone}
                onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                placeholder="+91 98765 43210" />

              <div>
                <label className="block text-sm font-medium text-charcoal/70 dark:text-white/70 mb-1.5">
                  {tx("selectLang")}
                </label>
                <select value={form.preferred_lang}
                  onChange={(e) => setForm((f) => ({ ...f, preferred_lang: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-xl border border-blue-100 dark:border-white/20
                             bg-white dark:bg-charcoal text-charcoal dark:text-white text-sm
                             focus:outline-none focus:ring-2 focus:ring-ashoka/30">
                  <option value="hindi">🇮🇳 हिंदी</option>
                  <option value="bhojpuri">🌾 भोजपुरी</option>
                  <option value="english">🔤 English</option>
                </select>
              </div>

              <InputField label={language === "hindi" ? "पासवर्ड" : "Password"}
                type="password" value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Min. 6 characters" required />

              <button type="submit" disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 bg-saffron text-white
                           rounded-xl font-semibold hover:bg-saffron-dark shadow-glow
                           disabled:opacity-60 transition-all active:scale-95">
                {loading ? <Loader2 size={18} className="animate-spin" /> : <UserPlus size={18} />}
                {tx("register")}
              </button>
            </form>

            <p className="text-center text-sm text-charcoal/50 dark:text-white/50 mt-6">
              {language === "hindi" ? "पहले से खाता है?" : "Already have an account?"}
              {" "}
              <Link to="/login" className="text-ashoka font-medium hover:underline">
                {tx("login")}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
