/**
 * pages/AboutPage.jsx  –  About SevaSetu project.
 */
import { Github, Globe, BookOpen, Cpu } from "lucide-react";
import useStore from "../store/useStore";

const WORKFLOW_STEPS = [
  { icon: "🔍", en: "Problem Identification",  hi: "समस्या की पहचान",   desc_hi: "ग्रामीण क्षेत्रों में डिजिटल पहुंच की बाधाएं" },
  { icon: "📋", en: "Requirement Analysis",    hi: "आवश्यकता विश्लेषण", desc_hi: "भाषा, आवाज़ और योजना मार्गदर्शन की जरूरत" },
  { icon: "📦", en: "Data Collection",          hi: "डेटा संग्रह",        desc_hi: "10 सरकारी योजनाओं का बहुभाषी डेटासेट" },
  { icon: "🔧", en: "Data Preprocessing",       hi: "डेटा प्रोसेसिंग",    desc_hi: "चंक्स में विभाजन, 3 भाषाओं में एम्बेडिंग" },
  { icon: "🗄️", en: "Knowledge Base",           hi: "नॉलेज बेस",          desc_hi: "FAISS वेक्टर इंडेक्स (90 चंक्स)" },
  { icon: "🏗️", en: "System Architecture",      hi: "सिस्टम आर्किटेक्चर", desc_hi: "FastAPI + React + PostgreSQL + FAISS" },
  { icon: "🤖", en: "RAG Pipeline",             hi: "RAG पाइपलाइन",      desc_hi: "क्वेरी → एम्बेडिंग → रिट्रीवल → जेनरेशन" },
  { icon: "🎙️", en: "Voice Processing",         hi: "वॉयस प्रोसेसिंग",    desc_hi: "gTTS + SpeechRecognition हिंदी सपोर्ट" },
  { icon: "💬", en: "Dual Interaction",          hi: "दोहरा इंटरफेस",      desc_hi: "शुरुआती + विस्तृत मोड" },
  { icon: "🏋️", en: "Model Fine-Tuning",        hi: "मॉडल फाइन-ट्यूनिंग", desc_hi: "Flan-T5 पर सरकारी Q&A डेटा से ट्रेनिंग" },
  { icon: "🚀", en: "Backend Deployment",        hi: "बैकएंड डिप्लॉयमेंट",  desc_hi: "Docker + FastAPI + uvicorn" },
  { icon: "✅", en: "Testing & Evaluation",      hi: "परीक्षण और मूल्यांकन", desc_hi: "pytest यूनिट टेस्ट + API इंटीग्रेशन टेस्ट" },
];

const TECH_STACK = [
  { category: "Frontend", items: ["React 18", "Tailwind CSS", "Zustand", "Framer Motion", "Vite"] },
  { category: "Backend",  items: ["FastAPI", "SQLAlchemy", "Pydantic v2", "Python-Jose", "bcrypt"] },
  { category: "AI / NLP", items: ["SentenceTransformers", "FAISS", "Flan-T5", "langdetect", "HuggingFace"] },
  { category: "Voice",    items: ["gTTS", "SpeechRecognition", "Google STT", "MP3 Audio Streaming"] },
  { category: "Database", items: ["PostgreSQL 16", "SQLAlchemy ORM", "Alembic Migrations", "Redis Cache"] },
  { category: "DevOps",   items: ["Docker", "Docker Compose", "Nginx (prod)", "GitHub Actions"] },
];

export default function AboutPage() {
  const { language } = useStore();
  const isHindi = language !== "english";

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">

      {/* Header */}
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full
                        bg-saffron/10 border border-saffron/20 text-saffron text-sm font-medium mb-6">
          🇮🇳 B.Tech Final Year Project / Hackathon
        </div>
        <h1 className="font-display text-4xl font-bold text-charcoal dark:text-white mb-4">
          {isHindi ? "SevaSetu के बारे में" : "About SevaSetu"}
        </h1>
        <p className="text-lg text-charcoal/60 dark:text-white/60 max-w-2xl mx-auto">
          {isHindi
            ? "एक AI-संचालित चैटबॉट जो ग्रामीण नागरिकों को हिंदी और भोजपुरी में सरकारी योजनाओं की जानकारी देता है।"
            : "An AI-powered chatbot helping rural citizens access government schemes in Hindi, Bhojpuri and English."}
        </p>
      </div>

      {/* Problem & Solution */}
      <div className="grid md:grid-cols-2 gap-6 mb-16">
        <div className="bg-red-50 dark:bg-red-950/20 rounded-2xl p-6 border border-red-100 dark:border-red-900/30">
          <h2 className="font-bold text-lg text-red-600 mb-4">❌ {isHindi ? "समस्या" : "The Problem"}</h2>
          <ul className="space-y-2 text-sm text-charcoal/70 dark:text-white/70">
            {(isHindi ? [
              "केवल अंग्रेज़ी में सरकारी पोर्टल",
              "जटिल फॉर्म और प्रक्रियाएं",
              "कम डिजिटल साक्षरता",
              "क्षेत्रीय भाषा का अभाव",
              "नज़दीकी सेवा केंद्र दूर",
            ] : [
              "English-only government portals",
              "Complex forms and procedures",
              "Low digital literacy in rural areas",
              "No regional dialect support",
              "CSC centers far from villages",
            ]).map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span> {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-jade/5 dark:bg-jade/10 rounded-2xl p-6 border border-jade/20">
          <h2 className="font-bold text-lg text-jade mb-4">✅ {isHindi ? "समाधान" : "Our Solution"}</h2>
          <ul className="space-y-2 text-sm text-charcoal/70 dark:text-white/70">
            {(isHindi ? [
              "हिंदी, भोजपुरी, अंग्रेज़ी में चैटबॉट",
              "RAG पाइपलाइन से सटीक जानकारी",
              "वॉयस इनपुट + TTS आउटपुट",
              "शुरुआती और विस्तृत मोड",
              "JWT-सुरक्षित यूज़र अकाउंट",
            ] : [
              "Chatbot in Hindi, Bhojpuri & English",
              "RAG pipeline for accurate answers",
              "Voice input + TTS audio output",
              "Beginner & Advanced response modes",
              "JWT-secured user accounts",
            ]).map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-jade mt-0.5">•</span> {item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Workflow */}
      <div className="mb-16">
        <h2 className="font-display text-2xl font-bold text-charcoal dark:text-white text-center mb-8">
          {isHindi ? "विकास प्रक्रिया" : "Development Workflow"}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={i}
              className="bg-white dark:bg-charcoal rounded-xl p-4 border border-blue-50
                         dark:border-white/10 shadow-card text-center hover:-translate-y-1 transition-transform">
              <div className="text-2xl mb-2">{step.icon}</div>
              <div className="text-xs font-bold text-charcoal dark:text-white mb-1">
                {isHindi ? step.hi : step.en}
              </div>
              <div className="text-xs text-charcoal/50 dark:text-white/40 leading-tight">
                {step.desc_hi}
              </div>
              <div className="mt-2 w-6 h-6 rounded-full bg-ashoka/10 text-ashoka text-xs
                              font-bold flex items-center justify-center mx-auto">
                {i + 1}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="mb-16">
        <h2 className="font-display text-2xl font-bold text-charcoal dark:text-white text-center mb-8">
          {isHindi ? "तकनीकी स्टैक" : "Technology Stack"}
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {TECH_STACK.map(({ category, items }) => (
            <div key={category}
              className="bg-white dark:bg-charcoal rounded-2xl p-5 border border-blue-50
                         dark:border-white/10 shadow-card">
              <h3 className="font-bold text-charcoal dark:text-white mb-3 flex items-center gap-2">
                <Cpu size={16} className="text-saffron" /> {category}
              </h3>
              <div className="flex flex-wrap gap-2">
                {items.map((item) => (
                  <span key={item}
                    className="text-xs px-2 py-1 rounded-lg bg-ashoka/8 dark:bg-ashoka/20
                               text-ashoka dark:text-blue-300 font-medium">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Links */}
      <div className="flex flex-wrap justify-center gap-4">
        <a href="https://github.com" target="_blank" rel="noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-charcoal dark:bg-white/10
                     text-white font-medium hover:opacity-90 transition-all">
          <Github size={18} /> GitHub
        </a>
        <a href="http://localhost:8000/api/docs" target="_blank" rel="noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-ashoka text-white
                     font-medium hover:bg-ashoka-dark shadow-glow-blue transition-all">
          <Globe size={18} /> API Docs
        </a>
        <a href="https://www.india.gov.in" target="_blank" rel="noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-jade text-white
                     font-medium hover:opacity-90 transition-all">
          <BookOpen size={18} /> india.gov.in
        </a>
      </div>
    </div>
  );
}
