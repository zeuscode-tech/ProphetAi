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

export default function RedFlagCard({ flag }: Props) {
  const s = SEV[flag.severity] ?? SEV.Low;
  const Icon = ICONS[flag.category] ?? AlertTriangle;
  return (
    <div className={`glass rounded-xl border ${s.border} p-4`}>
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-4 w-4 text-slate-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-200">{flag.category}</span>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${s.badge}`}>{flag.severity}</span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{flag.description}</p>
        </div>
      </div>
    </div>
  );
}
