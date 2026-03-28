"use client";

import type { PropertyDetail, ComparableSale } from "@/lib/api";
import { MapPin, Ruler, Clock, Bed, DollarSign } from "lucide-react";

function fmtUSD(v: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

function fmtShort(v: number) {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
  return `$${(v / 1000).toFixed(0)}k`;
}

interface Props {
  property: PropertyDetail;
  comparables: ComparableSale[];
}

export default function MarketPosition({ property, comparables }: Props) {
  const est = property.ai_estimated_price ? Number(property.ai_estimated_price) : null;
  const list = property.listing_price ? Number(property.listing_price) : null;

  const allPrices = [
    ...comparables.map((c) => c.sale_price),
    ...(est ? [est] : []),
    ...(list ? [list] : []),
  ];
  if (allPrices.length === 0) return null;

  const minP = Math.min(...allPrices);
  const maxP = Math.max(...allPrices);
  const range = maxP - minP || 1;
  const pad = range * 0.12;
  const scaleMin = minP - pad;
  const scaleMax = maxP + pad;
  const scaleRange = scaleMax - scaleMin;

  const toLeft = (v: number) => Math.max(0, Math.min(100, ((v - scaleMin) / scaleRange) * 100));

  const avgComp = comparables.reduce((s, c) => s + c.sale_price, 0) / comparables.length;
  const propPpsf = list && property.square_feet ? list / property.square_feet : null;
  const compPpsf = comparables.filter((c) => c.square_feet > 0).map((c) => c.sale_price / c.square_feet);
  const avgPpsf = compPpsf.length > 0 ? compPpsf.reduce((s, v) => s + v, 0) / compPpsf.length : null;

  const sorted = [...comparables].sort((a, b) => a.days_ago - b.days_ago);
  const maxCompPrice = Math.max(...comparables.map((c) => c.sale_price));

  // Determine if property is a deal
  const dealDiff = est && list ? ((est - list) / list) * 100 : null;

  return (
    <div className="space-y-6">
      {/* Deal indicator */}
      {dealDiff !== null && (
        <div className={`flex items-center gap-3 rounded-xl p-3 text-sm font-medium ${
          dealDiff > 5 ? "bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/20" :
          dealDiff < -5 ? "bg-neon-pink/10 text-neon-pink border border-neon-pink/20" :
          "bg-neon-blue/10 text-neon-blue border border-neon-blue/20"
        }`}>
          <DollarSign className="h-4 w-4 shrink-0" />
          {dealDiff > 5 ? `Potential deal — estimated ${dealDiff.toFixed(1)}% above listing` :
           dealDiff < -5 ? `Overpriced — listed ${Math.abs(dealDiff).toFixed(1)}% above estimate` :
           "Fairly priced — within 5% of estimated value"}
        </div>
      )}

      {/* Price Position Scale */}
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-4">Price Position vs Comparables</p>
        <div className="relative pt-12 pb-2">
          {/* Scale track */}
          <div className="h-1.5 rounded-full bg-surface-200 relative">
            {/* Comp range highlight */}
            {comparables.length > 1 && (
              <div
                className="absolute h-full rounded-full bg-neon-blue/15"
                style={{
                  left: `${toLeft(Math.min(...comparables.map((c) => c.sale_price)))}%`,
                  width: `${toLeft(Math.max(...comparables.map((c) => c.sale_price))) - toLeft(Math.min(...comparables.map((c) => c.sale_price)))}%`,
                }}
              />
            )}
          </div>

          {/* Comp dots */}
          {comparables.map((c, i) => (
            <div key={i} className="absolute" style={{ left: `${toLeft(c.sale_price)}%`, top: "42px", transform: "translateX(-50%)" }}>
              <div className="w-2.5 h-2.5 rounded-full bg-slate-600 border-2 border-slate-500 hover:bg-neon-blue hover:border-neon-blue transition-colors cursor-default"
                   title={`${c.address}: ${fmtUSD(c.sale_price)}`} />
            </div>
          ))}

          {/* Listing marker */}
          {list && (
            <div className="absolute flex flex-col items-center" style={{ left: `${toLeft(list)}%`, top: "0", transform: "translateX(-50%)" }}>
              <span className="text-[10px] font-semibold text-neon-purple whitespace-nowrap px-1.5 py-0.5 rounded bg-neon-purple/10">
                Listing {fmtShort(list)}
              </span>
              <div className="w-px h-5 bg-neon-purple/50 mt-0.5" />
              <div className="w-3.5 h-3.5 rounded-full bg-neon-purple/20 border-2 border-neon-purple flex items-center justify-center mt-[-2px]">
                <div className="w-1.5 h-1.5 rounded-full bg-neon-purple" />
              </div>
            </div>
          )}

          {/* AI Estimate marker */}
          {est && (
            <div className="absolute flex flex-col items-center" style={{ left: `${toLeft(est)}%`, top: "0", transform: "translateX(-50%)" }}>
              <span className="text-[10px] font-semibold text-neon-cyan whitespace-nowrap px-1.5 py-0.5 rounded bg-neon-cyan/10">
                Estimate {fmtShort(est)}
              </span>
              <div className="w-px h-5 bg-neon-cyan/50 mt-0.5" />
              <div className="w-3.5 h-3.5 rounded-full bg-neon-cyan/20 border-2 border-neon-cyan flex items-center justify-center mt-[-2px]">
                <div className="w-1.5 h-1.5 rounded-full bg-neon-cyan" />
              </div>
            </div>
          )}

          {/* Scale labels */}
          <div className="flex justify-between mt-3 text-[10px] text-slate-600">
            <span>{fmtShort(scaleMin)}</span>
            <span>{fmtShort(scaleMax)}</span>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl bg-surface-200/40 border border-glass-border p-3 text-center">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Avg Comp</p>
          <p className="mt-1 text-sm font-bold text-white">{fmtUSD(avgComp)}</p>
        </div>
        <div className="rounded-xl bg-surface-200/40 border border-glass-border p-3 text-center">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">{propPpsf ? "Your $/sqft" : "Comps"}</p>
          <p className="mt-1 text-sm font-bold text-white">{propPpsf ? `$${propPpsf.toFixed(0)}` : String(comparables.length)}</p>
        </div>
        <div className="rounded-xl bg-surface-200/40 border border-glass-border p-3 text-center">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Area $/sqft</p>
          <p className="mt-1 text-sm font-bold text-white">{avgPpsf ? `$${avgPpsf.toFixed(0)}` : "—"}</p>
        </div>
      </div>

      {/* Comp Cards */}
      <div className="space-y-2">
        <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Recent Sales Nearby</p>
        {sorted.map((c, i) => {
          const ppsf = c.square_feet > 0 ? c.sale_price / c.square_feet : null;
          const barWidth = (c.sale_price / maxCompPrice) * 100;
          return (
            <div key={i} className="rounded-xl bg-surface-200/20 hover:bg-surface-200/40 border border-glass-border/50 p-3 transition-all duration-200 cursor-default">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 min-w-0">
                  <MapPin className="h-3.5 w-3.5 text-neon-blue shrink-0" />
                  <span className="text-sm font-medium text-slate-200 truncate">{c.address}</span>
                </div>
                <span className="text-sm font-bold text-white shrink-0 ml-3">{fmtUSD(c.sale_price)}</span>
              </div>
              <div className="h-1 rounded-full bg-surface-200 overflow-hidden mb-2">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-neon-blue/30 to-neon-cyan/40 transition-all duration-500"
                  style={{ width: `${barWidth}%` }}
                />
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-500">
                <span className="flex items-center gap-1"><Bed className="h-3 w-3" />{c.bedrooms} bed</span>
                <span className="flex items-center gap-1"><Ruler className="h-3 w-3" />{c.square_feet?.toLocaleString()} sqft</span>
                {ppsf && <span className="text-slate-400">${ppsf.toFixed(0)}/sqft</span>}
                <span className="flex items-center gap-1 ml-auto"><Clock className="h-3 w-3" />{c.days_ago}d ago</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-slate-500 pt-1">
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-full bg-neon-cyan border border-neon-cyan" />AI Estimate</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-full bg-neon-purple border border-neon-purple" />Listing</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-2.5 w-2.5 rounded-full bg-slate-600 border-2 border-slate-500" />Comp Sales</span>
      </div>
    </div>
  );
}
