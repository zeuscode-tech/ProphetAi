"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { PropertyDetail, ComparableSale } from "@/lib/api";

interface Props {
  property: PropertyDetail;
  comparables: ComparableSale[];
}

function fmtUSD(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

interface TooltipEntry {
  payload: {
    address: string;
    sale_price: number;
    days_ago?: number;
  };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipEntry[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-xs shadow-xl">
      <p className="mb-1 font-semibold text-slate-200 max-w-[180px] truncate">
        {d.address}
      </p>
      <p className="text-brand-400">{fmtUSD(d.sale_price)}</p>
      {d.days_ago && (
        <p className="mt-0.5 text-slate-500">{d.days_ago} days ago</p>
      )}
    </div>
  );
}

export default function PriceChart({ property, comparables }: Props) {
  const aiEstimate = property.ai_estimated_price
    ? Number(property.ai_estimated_price)
    : null;
  const listingPrice = property.listing_price
    ? Number(property.listing_price)
    : null;

  const data = comparables.map((c) => ({
    address: c.address,
    sale_price: c.sale_price,
    days_ago: c.days_ago,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 10, left: 10, bottom: 0 }}
        >
          <XAxis
            dataKey="address"
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: string) => v.split(" ").slice(0, 2).join(" ")}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />

          {/* AI estimate reference line */}
          {aiEstimate && (
            <ReferenceLine
              y={aiEstimate}
              stroke="#38bdf8"
              strokeDasharray="4 3"
              label={{ value: "AI Est.", fill: "#38bdf8", fontSize: 10, position: "insideTopRight" }}
            />
          )}

          {/* Listing price reference line */}
          {listingPrice && (
            <ReferenceLine
              y={listingPrice}
              stroke="#6366f1"
              strokeDasharray="4 3"
              label={{ value: "Listing", fill: "#6366f1", fontSize: 10, position: "insideTopLeft" }}
            />
          )}

          <Bar dataKey="sale_price" radius={[4, 4, 0, 0]} maxBarSize={60}>
            {data.map((_, idx) => (
              <Cell key={idx} fill="#0369a1" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-5 border-t-2 border-dashed border-brand-400" />
          AI Estimate: {aiEstimate ? fmtUSD(aiEstimate) : "—"}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-5 border-t-2 border-dashed border-accent" />
          Listing: {listingPrice ? fmtUSD(listingPrice) : "—"}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-4 rounded-sm bg-brand-700" />
          Comparable sale
        </span>
      </div>
    </div>
  );
}
