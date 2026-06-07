/**
 * pages/HomePage.jsx  –  Landing page with hero, features, and scheme preview.
 */
import { Link } from "react-router-dom";
import { MessageCircle, Mic, Globe, Shield, ChevronRight, Star } from "lucide-react";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";

const FEATURES = [
  { icon: "🗣️", title: { hindi: "आपकी भाषा में", english: "In Your Language" },
    desc: { hindi: "हिंदी, भोजपुरी और अंग्रेज़ी में बात करें", english: "Chat in Hindi, Bhojpuri or English" } },
  { icon: "🎙️", title: { hindi: "वॉयस सपोर्ट", english: "Voice Enabled" },
    desc: { hindi: "बोलकर सवाल पूछें, जवाब भी सुनें", english: "Ask by voice, hear the answer back" } },
  { icon: "🏛️", title: { hindi: "सरकारी योजनाएं", english: "100+ Schemes" },
    desc: { hindi: "PM किसान, Ayushman, PMAY और बहुत कुछ", english: "PM Kisan, Ayushman, PMAY and more" } },
  { icon: "🔒", title: { hindi: "सुरक्षित", english: "Secure & Private" },
    desc: { hindi: "आपका डेटा पूरी तरह सुरक्षित है", english: "Your data is fully protected" } },
];

const SCHEMES_PREVIEW = [
  { name: "PM Kisan", name_hi: "PM किसान", emoji: "🌾", color: "#138808", amount: "₹6,000/साल" },
  { name: "Ayushman Bharat", name_hi: "आयुष्मान भारत", emoji: "🏥", color: "#0A3D91", amount: "₹5 लाख/साल" },
  { name: "PMAY Gramin", name_hi: "PM आवास योजना", emoji: "🏠", color: "#FF6B2B", amount: "₹1.20 लाख" },
  { name: "PMUY Ujjwala", name_hi: "उज्ज्वला योजना", emoji: "🔥", color: "#F59E0B", amount: "मुफ्त कनेक्शन" },
  { name: "Mudra Yojana", name_hi: "मुद्रा योजना", emoji: "💼", color: "#7C3AED", amount: "₹10 लाख तक" },
  { name: "Sukanya Samriddhi", name_hi: "सुकन्या समृद्धि", emoji: "👧", color: "#DB2777", amount: "8.2% ब्याज" },
];

export default function HomePage() {
  const { language } = useStore();
  const tx = (key) => t(key, language);
  const isHindi = language !== "english";

  return (
    <div className="min-h-screen bg-hero-pattern">
      {/* ── Hero ──────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 pt-16 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                        bg-saffron/10 border border-saffron/20 text-saffron text-sm font-medium mb-6">
          🇮🇳 Digital India Initiative
        </div>

        <h1 className="font-display text-5xl md:text-6xl font-bold text-charcoal dark:text-white
                       leading-tight mb-4 max-w-3xl mx-auto">
          {isHindi ? (
            <>
              <span className="text-saffron">सेवा</span>
              <span className="text-ashoka">सेतु</span>
              <br />
              <span className="text-3xl md:text-4xl text-charcoal/70 dark:text-white/70">
                आपकी अपनी, आपकी भाषा
              </span>
            </>
          ) : (
            <>
              <span className="text-saffron">Seva</span>
              <span className="text-ashoka">Setu</span>
              <br />
              <span className="text-3xl md:text-4xl text-charcoal/70 dark:text-white/70">
                Ask. Understand. Avail.
              </span>
            </>
          )}
        </h1>

        <p className="text-lg text-charcoal/60 dark:text-white/60 max-w-2xl mx-auto mb-10">
          {isHindi
            ? "सरकारी योजनाओं की जानकारी अपनी भाषा में पाएं — हिंदी, भोजपुरी या अंग्रेज़ी में। बस पूछें, हम बताएंगे।"
            : "Access government schemes in your language. Ask about PM Kisan, Ayushman Bharat, PMAY, and more."}
        </p>

        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/chat"
            className="flex items-center gap-2 px-8 py-3.5 bg-ashoka text-white rounded-2xl
                       font-semibold text-base shadow-glow-blue hover:bg-ashoka-dark transition-all
                       active:scale-95">
            <MessageCircle size={20} />
            {isHindi ? "चैट शुरू करें" : "Start Chatting"}
            <ChevronRight size={18} />
          </Link>
          <Link to="/schemes"
            className="flex items-center gap-2 px-8 py-3.5 bg-white dark:bg-charcoal text-ashoka
                       rounded-2xl font-semibold text-base border border-blue-100 dark:border-white/20
                       hover:shadow-card transition-all">
            🏛️ {isHindi ? "योजनाएं देखें" : "Browse Schemes"}
          </Link>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-center gap-8 mt-12 flex-wrap">
          {[
            { num: "10+",    label: isHindi ? "सरकारी योजनाएं" : "Gov Schemes" },
            { num: "3",      label: isHindi ? "भाषाएं"         : "Languages"    },
            { num: "100%",   label: isHindi ? "मुफ्त सेवा"     : "Free Service" },
            { num: "24/7",   label: isHindi ? "उपलब्ध"        : "Available"    },
          ].map(({ num, label }) => (
            <div key={label} className="text-center">
              <div className="font-display text-3xl font-bold text-saffron">{num}</div>
              <div className="text-sm text-charcoal/50 dark:text-white/50">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <h2 className="font-display text-3xl font-bold text-center text-charcoal dark:text-white mb-10">
          {isHindi ? "SevaSetu क्यों चुनें?" : "Why SevaSetu?"}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((f, i) => (
            <div key={i}
              className="bg-white dark:bg-charcoal rounded-2xl p-6 shadow-card
                         border border-blue-50 dark:border-white/10 hover:-translate-y-1
                         transition-transform scheme-card">
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="font-bold text-charcoal dark:text-white mb-2">
                {f.title[language] || f.title.english}
              </h3>
              <p className="text-sm text-charcoal/60 dark:text-white/60">
                {f.desc[language] || f.desc.english}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Popular Schemes Preview ───────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="flex items-center justify-between mb-8">
          <h2 className="font-display text-3xl font-bold text-charcoal dark:text-white">
            {isHindi ? "लोकप्रिय योजनाएं" : "Popular Schemes"}
          </h2>
          <Link to="/schemes"
            className="flex items-center gap-1 text-ashoka text-sm font-medium hover:underline">
            {tx("viewAll")} <ChevronRight size={16} />
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {SCHEMES_PREVIEW.map((s) => (
            <Link key={s.name} to="/chat"
              className="flex flex-col items-center gap-3 p-4 bg-white dark:bg-charcoal rounded-2xl
                         border border-blue-50 dark:border-white/10 shadow-card hover:-translate-y-1
                         transition-transform text-center scheme-card">
              <div className="text-3xl">{s.emoji}</div>
              <div>
                <p className="text-xs font-bold text-charcoal dark:text-white leading-tight">
                  {isHindi ? s.name_hi : s.name}
                </p>
                <p className="text-xs mt-1 font-medium" style={{ color: s.color }}>{s.amount}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── CTA Banner ───────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-4 py-12">
        <div className="rounded-3xl p-10 text-center text-white"
             style={{ background: "linear-gradient(135deg, #0A3D91, #138808)" }}>
          <h2 className="font-display text-3xl font-bold mb-3">
            {isHindi ? "आज ही शुरू करें" : "Get Started Today"}
          </h2>
          <p className="text-white/80 mb-6">
            {isHindi ? "रजिस्ट्रेशन करें और सभी सरकारी सेवाएं एक जगह पाएं।"
                     : "Register now and access all government schemes in one place."}
          </p>
          <Link to="/register"
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-ashoka rounded-xl
                       font-bold hover:shadow-lg transition-all active:scale-95">
            {tx("register")} <ChevronRight size={18} />
          </Link>
        </div>
      </section>
    </div>
  );
}
