"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from "recharts";
import type { PropertyDetail, ComparableSale } from "@/lib/api";

interface Props { property: PropertyDetail; comparables: ComparableSale[]; }

function fmtUSD(v: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(v);
}

interface TEntry { payload: { address: string; sale_price: number; days_ago?: number }; }
interface TProps { active?: boolean; payload?: TEntry[]; }

function Tip({ active, payload }: TProps) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="glass rounded-lg p-3 text-xs shadow-xl border border-glass-border-light">
      <p className="font-semibold text-white max-w-[180px] truncate">{d.address}</p>
      <p className="text-neon-cyan font-semibold">{fmtUSD(d.sale_price)}</p>
      {d.days_ago && <p className="mt-0.5 text-slate-500">{d.days_ago} days ago</p>}
    </div>
  );
}

export default function PriceChart({ property, comparables }: Props) {
  const est = property.ai_estimated_price ? Number(property.ai_estimated_price) : null;
  const list = property.listing_price ? Number(property.listing_price) : null;
  const data = comparables.map((c) => ({ address: c.address, sale_price: c.sale_price, days_ago: c.days_ago }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
          <XAxis dataKey="address" tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v: string) => v.split(" ").slice(0, 2).join(" ")} />
          <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`} />
          <Tooltip content={<Tip />} cursor={{ fill: "rgba(255,255,255,0.02)" }} />
          {est && <ReferenceLine y={est} stroke="#06d6a0" strokeDasharray="4 3" label={{ value: "Estimate", fill: "#06d6a0", fontSize: 10, position: "insideTopRight" }} />}
          {list && <ReferenceLine y={list} stroke="#7b61ff" strokeDasharray="4 3" label={{ value: "Listing", fill: "#7b61ff", fontSize: 10, position: "insideTopLeft" }} />}
          <Bar dataKey="sale_price" radius={[6, 6, 0, 0]} maxBarSize={50}>
            {data.map((_, i) => <Cell key={i} fill="rgba(76,201,240,0.4)" />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5"><span className="inline-block h-0.5 w-5 border-t-2 border-dashed border-neon-cyan" />Estimate</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-0.5 w-5 border-t-2 border-dashed border-neon-purple" />Listing</span>
        <span className="flex items-center gap-1.5"><span className="inline-block h-2 w-4 rounded-sm bg-neon-blue/40" />Comparable</span>
      </div>
    </div>
  );
}
