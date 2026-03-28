import { Wrench } from "lucide-react";
import type { PhotoInsight } from "@/lib/api";

interface Props { insight: PhotoInsight; onPhotoClick?: () => void; }

export default function PhotoInsightCard({ insight, onPhotoClick }: Props) {
  const score = insight.condition_score ?? 5;
  const color = score >= 7 ? "bg-neon-cyan" : score >= 4 ? "bg-neon-blue" : "bg-neon-pink";

  return (
    <div className="glass overflow-hidden rounded-2xl">
      {insight.photo_url && (
        <div className="relative h-44 overflow-hidden cursor-pointer group" onClick={onPhotoClick}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={insight.photo_url} alt={insight.room_type} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
          <div className="absolute inset-0 bg-gradient-to-t from-surface/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      )}
      <div className="p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-white">{insight.room_type || "Room"}</span>
          <span className="text-xs text-slate-400">{score.toFixed(1)}/10</span>
        </div>
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-200">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${(score / 10) * 100}%` }} />
        </div>
        {insight.observations && insight.observations.length > 0 && (
          <ul className="mt-3 space-y-1">
            {insight.observations.map((obs, i) => (
              <li key={i} className="flex gap-1.5 text-xs text-slate-400"><span className="shrink-0 text-neon-cyan">&bull;</span>{obs}</li>
            ))}
          </ul>
        )}
        {insight.renovation_needed && (
          <div className="mt-3 flex items-center gap-2 rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-400">
            <Wrench className="h-3.5 w-3.5 shrink-0" />
            Renovation needed{insight.estimated_reno_cost_usd != null && (
              <span className="font-semibold ml-0.5">~{new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(insight.estimated_reno_cost_usd)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
