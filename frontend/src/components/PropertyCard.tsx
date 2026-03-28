import Link from "next/link";
import { Bed, Bath, Maximize, AlertTriangle, ArrowUpRight } from "lucide-react";
import type { PropertySummary } from "@/lib/api";

interface Props {
  property: PropertySummary;
}

function fmtUSD(n: number | null | undefined) {
  if (n == null) return "\u2014";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

const STATUS: Record<string, string> = {
  completed: "bg-neon-cyan/10 text-neon-cyan",
  processing: "bg-neon-blue/10 text-neon-blue animate-pulse",
  failed: "bg-neon-pink/10 text-neon-pink",
  pending: "bg-surface-200 text-slate-400",
};

export default function PropertyCard({ property }: Props) {
  const delta = property.price_delta_pct;
  const photo = property.photo_insights?.[0]?.photo_url;

  return (
    <Link href={`/analysis/${property.id}`} className="group block glass-hover rounded-2xl overflow-hidden cursor-pointer">
      {/* Photo */}
      <div className="relative h-44 bg-surface-100 overflow-hidden">
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photo} alt={property.address} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500" onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        ) : (
          <div className="h-full w-full flex items-center justify-center text-slate-700 text-3xl font-bold">
            {property.address?.[0] ?? "?"}
          </div>
        )}
        <span className={`absolute top-3 right-3 rounded-full px-2.5 py-0.5 text-[10px] font-semibold capitalize backdrop-blur-sm ${STATUS[property.status] ?? STATUS.pending}`}>
          {property.status}
        </span>
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent px-4 pb-3 pt-8">
          <p className="text-white text-lg font-bold">{fmtUSD(property.listing_price)}</p>
        </div>
      </div>

      {/* Info */}
      <div className="p-4">
        <p className="text-sm font-semibold text-white truncate">{property.address || "Address pending..."}</p>
        <p className="text-xs text-slate-500 truncate mt-0.5">{[property.city, property.state].filter(Boolean).join(", ")}</p>

        <div className="mt-2.5 flex gap-4 text-xs text-slate-500">
          {property.bedrooms != null && <span className="flex items-center gap-1"><Bed className="h-3.5 w-3.5" />{property.bedrooms}</span>}
          {property.bathrooms != null && <span className="flex items-center gap-1"><Bath className="h-3.5 w-3.5" />{property.bathrooms}</span>}
          {property.square_feet != null && <span className="flex items-center gap-1"><Maximize className="h-3.5 w-3.5" />{property.square_feet.toLocaleString()}</span>}
        </div>

        <div className="mt-3 pt-3 border-t border-glass-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Est.</span>
            <span className="text-xs font-semibold text-neon-cyan">{fmtUSD(property.ai_estimated_price)}</span>
            {delta != null && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${delta >= 0 ? "bg-neon-cyan/10 text-neon-cyan" : "bg-neon-pink/10 text-neon-pink"}`}>
                {delta >= 0 ? "+" : ""}{delta.toFixed(1)}%
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {property.red_flags && property.red_flags.length > 0 && (
              <span className="flex items-center gap-1 text-[10px] text-amber-400">
                <AlertTriangle className="h-3 w-3" />{property.red_flags.length}
              </span>
            )}
            <span className="text-neon-cyan opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowUpRight className="h-3.5 w-3.5" />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
