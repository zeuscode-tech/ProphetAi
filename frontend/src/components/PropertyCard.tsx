import Link from "next/link";
import type { PropertySummary } from "@/lib/api";

interface Props {
  property: PropertySummary;
}

function fmtUSD(n: number | null | undefined) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

const STATUS_COLORS: Record<string, string> = {
  completed: "bg-green-900/40 text-green-400",
  processing: "bg-yellow-900/40 text-yellow-400 animate-pulse",
  failed: "bg-red-900/40 text-red-400",
  pending: "bg-slate-800 text-slate-400",
};

export default function PropertyCard({ property }: Props) {
  const delta = property.price_delta_pct;

  return (
    <Link
      href={`/analysis/${property.id}`}
      className="gradient-border block rounded-2xl bg-slate-900/60 p-5 transition hover:bg-slate-800/60 hover:shadow-lg hover:shadow-brand-900/20"
    >
      {/* Address & status */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-semibold text-slate-100">
            {property.address || "Address pending…"}
          </p>
          <p className="mt-0.5 truncate text-xs text-slate-500">
            {[property.city, property.state].filter(Boolean).join(", ")}
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wider ${
            STATUS_COLORS[property.status] ?? STATUS_COLORS.pending
          }`}
        >
          {property.status}
        </span>
      </div>

      {/* Beds / baths / sqft */}
      <div className="mt-3 flex gap-3 text-xs text-slate-400">
        {property.bedrooms != null && <span>🛏 {property.bedrooms}</span>}
        {property.bathrooms != null && <span>🚿 {property.bathrooms}</span>}
        {property.square_feet != null && (
          <span>📐 {property.square_feet.toLocaleString()} sqft</span>
        )}
      </div>

      {/* Price row */}
      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-xs text-slate-500">Listing</p>
          <p className="text-sm font-semibold text-slate-200">
            {fmtUSD(property.listing_price)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">AI Estimate</p>
          <p className="text-sm font-semibold text-brand-400">
            {fmtUSD(property.ai_estimated_price)}
          </p>
        </div>
        {delta != null && (
          <span
            className={`rounded-md px-2 py-0.5 text-xs font-bold ${
              delta >= 0
                ? "bg-green-900/40 text-green-400"
                : "bg-red-900/40 text-red-400"
            }`}
          >
            {delta >= 0 ? "+" : ""}
            {delta.toFixed(1)}%
          </span>
        )}
      </div>

      {/* Investment score bar */}
      {property.investment_score != null && (
        <div className="mt-4">
          <div className="mb-1 flex justify-between text-xs text-slate-500">
            <span>Investment Score</span>
            <span className="font-semibold text-slate-300">
              {property.investment_score.toFixed(0)} / 100
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-accent"
              style={{ width: `${Math.min(property.investment_score, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Red flags count */}
      {property.red_flags && property.red_flags.length > 0 && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-amber-500">
          <span>⚠️</span>
          <span>
            {property.red_flags.length} red flag
            {property.red_flags.length !== 1 ? "s" : ""} detected
          </span>
        </div>
      )}
    </Link>
  );
}
