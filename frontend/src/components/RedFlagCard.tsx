import { AlertTriangle, Droplets, Zap, Paintbrush, Scale, DollarSign, Construction } from "lucide-react";
import type { RedFlag } from "@/lib/api";

interface Props { flag: RedFlag; }

const SEV: Record<string, { badge: string; border: string }> = {
  High: { badge: "bg-neon-pink/15 text-neon-pink", border: "border-neon-pink/20" },
  Medium: { badge: "bg-amber-500/15 text-amber-400", border: "border-amber-500/20" },
  Low: { badge: "bg-neon-blue/15 text-neon-blue", border: "border-neon-blue/20" },
};
const ICONS: Record<string, typeof AlertTriangle> = {
  Structural: Construction, "Water Damage": Droplets, Electrical: Zap,
  Cosmetic: Paintbrush, Legal: Scale, Pricing: DollarSign,
};

const CATEGORY_RU: Record<string, string> = {
  Structural: "Конструктив", "Water Damage": "Протечка", Electrical: "Электрика",
  Cosmetic: "Косметика", Legal: "Юридический", Pricing: "Ценообразование",
};
const SEVERITY_RU: Record<string, string> = {
  High: "Высокий", Medium: "Средний", Low: "Низкий",
};

export default function RedFlagCard({ flag }: Props) {
  // Normalize severity to capitalized key ("high" → "High")
  const sevKey = flag.severity
    ? (flag.severity.charAt(0).toUpperCase() + flag.severity.slice(1).toLowerCase())
    : "Low";
  const s = SEV[sevKey] ?? SEV.Low;
  // Support both new schema (issue) and old schema (category)
  const title = flag.issue || (flag.category ? (CATEGORY_RU[flag.category] ?? flag.category) : "Риск");
  const Icon = flag.category ? (ICONS[flag.category] ?? AlertTriangle) : AlertTriangle;
  return (
    <div className={`glass rounded-xl border ${s.border} p-4`}>
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-4 w-4 text-slate-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-200">{title}</span>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s.badge}`}>{SEVERITY_RU[sevKey] ?? sevKey}</span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{flag.description}</p>
        </div>
      </div>
    </div>
  );
}
