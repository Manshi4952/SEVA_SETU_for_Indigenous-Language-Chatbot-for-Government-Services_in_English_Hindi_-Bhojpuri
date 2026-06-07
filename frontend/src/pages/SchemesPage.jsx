/**
 * pages/SchemesPage.jsx  –  Browse and search all government schemes.
 */
import { useEffect, useState } from "react";
import { Search, Loader2 } from "lucide-react";
import useStore from "../store/useStore";
import SchemeCard from "../components/SchemeCard";
import { t } from "../utils/i18n";

export default function SchemesPage() {
  const { schemes, loadSchemes, language } = useStore();
  const [query, setQuery]   = useState("");
  const [loading, setLoading] = useState(false);
  const tx = (k) => t(k, language);

  useEffect(() => {
    setLoading(true);
    loadSchemes().finally(() => setLoading(false));
  }, []);

  const filtered = schemes.filter((s) =>
    s.name.toLowerCase().includes(query.toLowerCase()) ||
    (s.hindi_desc || "").includes(query) ||
    (s.english_desc || "").toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="font-display text-4xl font-bold text-charcoal dark:text-white mb-3">
          {language === "hindi" ? "सरकारी योजनाएं" : "Government Schemes"}
        </h1>
        <p className="text-charcoal/60 dark:text-white/60">
          {language === "hindi"
            ? "सभी केंद्रीय सरकारी योजनाओं की जानकारी एक जगह"
            : "All central government schemes in one place"}
        </p>
      </div>

      {/* Search bar */}
      <div className="relative max-w-xl mx-auto mb-10">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-charcoal/40" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={tx("schemeSearch")}
          className="w-full pl-11 pr-4 py-3 rounded-2xl border border-blue-100 dark:border-white/20
                     bg-white dark:bg-charcoal text-charcoal dark:text-white shadow-card
                     focus:outline-none focus:ring-2 focus:ring-ashoka/30 transition-all"
        />
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={32} className="animate-spin text-ashoka" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-charcoal/50 dark:text-white/50">
          <div className="text-5xl mb-4">🔍</div>
          <p>{language === "hindi" ? "कोई योजना नहीं मिली" : "No schemes found"}</p>
        </div>
      ) : (
        <>
          <p className="text-sm text-charcoal/50 dark:text-white/50 mb-6 text-center">
            {filtered.length} {language === "hindi" ? "योजनाएं मिलीं" : "schemes found"}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((scheme) => (
              <SchemeCard key={scheme.id} scheme={scheme} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
