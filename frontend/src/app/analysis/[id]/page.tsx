"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getProperty, type PropertyDetail } from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import RedFlagCard from "@/components/RedFlagCard";
import PhotoInsightCard from "@/components/PhotoInsightCard";
import InvestmentScoreGauge from "@/components/InvestmentScoreGauge";

function fmt(n: number | null | undefined, opts?: Intl.NumberFormatOptions) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", opts).format(n);
}

function fmtUSD(n: number | null | undefined) {
  return fmt(n, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getProperty(Number(id))
      .then(setProperty)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-slate-400">
          <svg className="h-10 w-10 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          <p className="text-sm">Loading analysis…</p>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="rounded-xl border border-red-800 bg-red-950/30 p-6 text-red-400">
        {error ?? "Property not found."}
      </div>
    );
  }

  const delta = property.price_delta_pct;
  const deltaPositive = delta !== null && delta > 0;

  return (
    <div className="space-y-8">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
      >
        ← Back to dashboard
      </button>

      {/* Property header */}
      <div className="gradient-border rounded-2xl bg-slate-900/60 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-50">
              {property.address || "Address unavailable"}
            </h1>
            <p className="mt-0.5 text-slate-400">
              {[property.city, property.state, property.zip_code].filter(Boolean).join(", ")}
            </p>
            <div className="mt-3 flex flex-wrap gap-3 text-sm text-slate-300">
              {property.bedrooms != null && <span>🛏 {property.bedrooms} beds</span>}
              {property.bathrooms != null && <span>🚿 {property.bathrooms} baths</span>}
              {property.square_feet != null && (
                <span>📐 {fmt(property.square_feet)} sqft</span>
              )}
              {property.year_built != null && <span>🗓 Built {property.year_built}</span>}
            </div>
          </div>

          {/* Status badge */}
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wider ${
              property.status === "completed"
                ? "bg-green-900/40 text-green-400"
                : property.status === "processing"
                ? "bg-yellow-900/40 text-yellow-400"
                : property.status === "failed"
                ? "bg-red-900/40 text-red-400"
                : "bg-slate-800 text-slate-400"
            }`}
          >
            {property.status}
          </span>
        </div>

        {/* Price row */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500">Listing Price</p>
            <p className="mt-1 text-2xl font-bold text-slate-100">
              {fmtUSD(property.listing_price)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500">AI Estimate</p>
            <p className="mt-1 text-2xl font-bold text-brand-400">
              {fmtUSD(property.ai_estimated_price)}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500">Price Delta</p>
            <p
              className={`mt-1 text-2xl font-bold ${
                delta == null
                  ? "text-slate-400"
                  : deltaPositive
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              {delta == null
                ? "—"
                : `${deltaPositive ? "+" : ""}${delta.toFixed(1)}%`}
            </p>
            <p className="text-xs text-slate-500">
              {delta == null
                ? ""
                : deltaPositive
                ? "Undervalued vs listing"
                : "Overvalued vs listing"}
            </p>
          </div>
        </div>
      </div>

      {/* Investment Score + Metrics row */}
      <div className="grid gap-4 sm:grid-cols-4">
        <div className="sm:col-span-1 gradient-border rounded-2xl bg-slate-900/60 p-5 flex flex-col items-center justify-center">
          <p className="mb-3 text-xs uppercase tracking-widest text-slate-500">Investment Score</p>
          <InvestmentScoreGauge score={property.investment_score} />
        </div>
        {[
          {
            label: "Rental Yield",
            value: typeof property.rental_yield_pct === 'number' ? `${property.rental_yield_pct.toFixed(1)}%` : "-",
            sub: "Estimated gross annual yield",
          },
          {
            label: "Appreciation Trend",
            value: typeof property.appreciation_trend_pct === 'number' ? `${property.appreciation_trend_pct.toFixed(1)}%` : "-",
            sub: "12-month area average",
          },
          {
            label: "Red Flags",
            value: property.red_flags?.length ?? 0,
            sub: "Issues detected by AI",
          },
        ].map((m) => (
          <div key={m.label} className="gradient-border rounded-2xl bg-slate-900/60 p-5">
            <p className="text-xs uppercase tracking-widest text-slate-500">{m.label}</p>
            <p className="mt-1 text-3xl font-bold text-slate-100">{m.value}</p>
            <p className="mt-1 text-xs text-slate-500">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Price chart */}
      {property.comparable_sales && property.comparable_sales.length > 0 && (
        <div className="gradient-border rounded-2xl bg-slate-900/60 p-6">
          <h2 className="mb-4 text-lg font-semibold text-slate-100">
            Comparable Sales
          </h2>
          <PriceChart
            property={property}
            comparables={property.comparable_sales}
          />
        </div>
      )}

      {/* Red flags */}
      {property.red_flags && property.red_flags.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-slate-100">
            ⚠️ Red Flags ({property.red_flags.length})
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {property.red_flags.map((flag, i) => (
              <RedFlagCard key={i} flag={flag} />
            ))}
          </div>
        </div>
      )}

      {/* Photo insights */}
      {property.photo_insights && property.photo_insights.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-slate-100">
            🖼️ Photo Insights
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {property.photo_insights.map((insight, i) => (
              <PhotoInsightCard key={i} insight={insight} />
            ))}
          </div>
        </div>
      )}

      {/* Listing URL */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-500">
        <span className="font-medium text-slate-400">Source URL: </span>
        <a
          href={property.listing_url}
          target="_blank"
          rel="noopener noreferrer"
          className="break-all text-brand-400 hover:underline"
        >
          {property.listing_url}
        </a>
      </div>
    </div>
  );
}
