import type { RedFlag } from "@/lib/api";

interface Props {
  flag: RedFlag;
}

const SEVERITY_STYLES: Record<string, { badge: string; border: string; bg: string }> = {
  High: {
    badge: "bg-red-900/60 text-red-300",
    border: "border-red-800",
    bg: "bg-red-950/30",
  },
  Medium: {
    badge: "bg-amber-900/60 text-amber-300",
    border: "border-amber-800",
    bg: "bg-amber-950/20",
  },
  Low: {
    badge: "bg-blue-900/50 text-blue-300",
    border: "border-blue-900",
    bg: "bg-blue-950/20",
  },
};

const CATEGORY_ICONS: Record<string, string> = {
  Structural: "🏗️",
  "Water Damage": "💧",
  Electrical: "⚡",
  Cosmetic: "🎨",
  Legal: "⚖️",
  Pricing: "💲",
  Other: "⚠️",
};

export default function RedFlagCard({ flag }: Props) {
  const styles = SEVERITY_STYLES[flag.severity] ?? SEVERITY_STYLES.Low;
  const icon = CATEGORY_ICONS[flag.category] ?? "⚠️";

  return (
    <div
      className={`rounded-xl border ${styles.border} ${styles.bg} p-4`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-200">
              {flag.category}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold ${styles.badge}`}
            >
              {flag.severity}
            </span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">
            {flag.description}
          </p>
        </div>
      </div>
    </div>
  );
}
