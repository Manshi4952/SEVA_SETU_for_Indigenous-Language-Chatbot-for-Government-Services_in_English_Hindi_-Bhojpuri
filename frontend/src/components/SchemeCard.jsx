/**
 * components/SchemeCard.jsx  –  Government scheme display card.
 */
import { ExternalLink, CheckCircle, IndianRupee, Users } from "lucide-react";
import useStore from "../store/useStore";
import { t } from "../utils/i18n";

const SCHEME_COLORS = {
  "Atal Pension":      ["#FF6B2B", "#FF8C55"],
  "PM Kisan":          ["#138808", "#1AAD0A"],
  "Ayushman":          ["#0A3D91", "#1254C0"],
  "Pradhan Mantri Awas": ["#7C3AED", "#9F67FF"],
  "Ujjwala":           ["#F59E0B", "#FCD34D"],
  "Mudra":             ["#059669", "#34D399"],
  "IGNOAPS":           ["#DC2626", "#F87171"],
  "PMJJBY":            ["#0891B2", "#22D3EE"],
  "PMSBY":             ["#7C3AED", "#C084FC"],
  "Sukanya":           ["#DB2777", "#F472B6"],
};

function getColor(name) {
  for (const [key, colors] of Object.entries(SCHEME_COLORS)) {
    if (name.includes(key)) return colors;
  }
  return ["#0A3D91", "#1254C0"];
}

export default function SchemeCard({ scheme }) {
  const { language } = useStore();
  const tx = (key) => t(key, language);
  const [colorA, colorB] = getColor(scheme.name);

  const desc = language === "hindi"    ? scheme.hindi_desc
             : language === "bhojpuri" ? scheme.bhojpuri_desc
             : scheme.english_desc;

  const elig = language === "hindi"    ? scheme.eligibility?.hindi
             : language === "bhojpuri" ? scheme.eligibility?.bhojpuri
             : scheme.eligibility?.english;

  const ben  = language === "hindi"    ? scheme.benefits?.hindi
             : language === "bhojpuri" ? scheme.benefits?.bhojpuri
             : scheme.benefits?.english;

  return (
    <div className="scheme-card rounded-2xl bg-white dark:bg-charcoal border border-blue-50
                    dark:border-white/10 overflow-hidden shadow-card">
      {/* Header gradient */}
      <div className="h-2 w-full" style={{
        background: `linear-gradient(90deg, ${colorA}, ${colorB})`,
      }} />

      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="font-display font-bold text-base text-charcoal dark:text-white leading-tight">
            {scheme.name}
          </h3>
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
               style={{ background: `linear-gradient(135deg, ${colorA}20, ${colorB}30)` }}>
            <IndianRupee size={18} style={{ color: colorA }} />
          </div>
        </div>

        {/* Description */}
        {desc && (
          <p className="text-sm text-charcoal/60 dark:text-white/60 leading-relaxed mb-4 line-clamp-2">
            {desc}
          </p>
        )}

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {scheme.age_limit && (
            <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full
                             bg-blue-50 dark:bg-white/10 text-ashoka dark:text-blue-300">
              <Users size={10} /> {scheme.age_limit}
            </span>
          )}
          {scheme.pension_range && scheme.pension_range !== "N/A" && (
            <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full
                             bg-jade/10 text-jade">
              <IndianRupee size={10} /> {scheme.pension_range.split(" ")[0]}
            </span>
          )}
        </div>

        {/* Eligibility */}
        {elig && (
          <div className="mb-4 p-3 rounded-xl bg-green-50 dark:bg-jade/10">
            <p className="text-xs font-semibold text-jade mb-1">
              ✅ {tx("eligibility")}
            </p>
            <p className="text-xs text-charcoal/70 dark:text-white/70 line-clamp-2">{elig}</p>
          </div>
        )}

        {/* Benefits */}
        {ben && (
          <div className="mb-4 p-3 rounded-xl"
               style={{ background: `${colorA}08`, border: `1px solid ${colorA}20` }}>
            <p className="text-xs font-semibold mb-1" style={{ color: colorA }}>
              🎁 {tx("benefits")}
            </p>
            <p className="text-xs text-charcoal/70 dark:text-white/70 line-clamp-2">{ben}</p>
          </div>
        )}

        {/* CTA */}
        <a href="https://www.india.gov.in" target="_blank" rel="noreferrer"
          className="flex items-center justify-center gap-2 w-full py-2 rounded-xl text-sm font-semibold
                     text-white transition-all hover:opacity-90 active:scale-95"
          style={{ background: `linear-gradient(90deg, ${colorA}, ${colorB})` }}>
          {tx("applyNow")}
          <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}
