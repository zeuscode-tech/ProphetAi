import type { PhotoInsight } from "@/lib/api";

interface Props {
  insight: PhotoInsight;
}

function ConditionBar({ score }: { score: number }) {
  const pct = (score / 10) * 100;
  const color =
    score >= 7 ? "bg-green-500" : score >= 4 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
      <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function PhotoInsightCard({ insight }: Props) {
  const hasReno = insight.renovation_needed;

  return (
    <div className="gradient-border rounded-2xl bg-slate-900/60 overflow-hidden">
      {/* Photo thumbnail */}
      {insight.photo_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={insight.photo_url}
          alt={insight.room_type}
          className="h-40 w-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      )}

      <div className="p-4">
        {/* Room type + condition score */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-slate-200">
            {insight.room_type || "Unknown Room"}
          </span>
          <span className="text-xs text-slate-400">
            {insight.condition_score?.toFixed(1)} / 10
          </span>
        </div>
        <ConditionBar score={insight.condition_score ?? 5} />

        {/* Observations */}
        {insight.observations && insight.observations.length > 0 && (
          <ul className="mt-3 space-y-1">
            {insight.observations.map((obs, i) => (
              <li key={i} className="flex gap-1.5 text-xs text-slate-400">
                <span className="shrink-0 text-brand-400">•</span>
                {obs}
              </li>
            ))}
          </ul>
        )}

        {/* Renovation flag */}
        {hasReno && (
          <div className="mt-3 rounded-lg border border-amber-800 bg-amber-950/30 px-3 py-2 text-xs text-amber-400">
            🔨 Renovation needed
            {insight.estimated_reno_cost_usd != null && (
              <span className="ml-1 font-semibold">
                ~{new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(insight.estimated_reno_cost_usd)}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
