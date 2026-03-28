"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProperties, type PropertySummary } from "@/lib/api";
import PropertyCard from "@/components/PropertyCard";
import { Home, TrendingUp, AlertTriangle, Plus } from "lucide-react";

export default function DashboardPage() {
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getProperties(page)
      .then((data) => { setProperties(data.results); setCount(data.count); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(count / 20));
  const avgScore = properties.length > 0
    ? properties.filter((p) => p.investment_score !== null).reduce((a, p) => a + (p.investment_score ?? 0), 0) / Math.max(1, properties.filter((p) => p.investment_score !== null).length)
    : null;
  const totalFlags = properties.reduce((a, p) => a + (p.red_flags?.length ?? 0), 0);

  return (
    <div className="animate-fade-in">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Объекты</h1>
          <p className="mt-1 text-sm text-slate-500">{count} объектов проанализировано</p>
        </div>
        <Link href="/" className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-blue px-5 py-2.5 text-sm font-semibold text-surface transition-all hover:shadow-glow cursor-pointer">
          <Plus className="h-4 w-4" /> Новый анализ
        </Link>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        <div className="glass rounded-2xl p-5 flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neon-cyan/10 text-neon-cyan"><Home className="h-5 w-5" /></div>
          <div><p className="text-xs text-slate-500">Всего проанализировано</p><p className="text-2xl font-bold text-white">{count}</p></div>
        </div>
        <div className="glass rounded-2xl p-5 flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neon-purple/10 text-neon-purple"><TrendingUp className="h-5 w-5" /></div>
          <div><p className="text-xs text-slate-500">Средний инв. рейтинг</p><p className="text-2xl font-bold text-white">{avgScore !== null ? avgScore.toFixed(1) : "—"}</p></div>
        </div>
        <div className="glass rounded-2xl p-5 flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neon-pink/10 text-neon-pink"><AlertTriangle className="h-5 w-5" /></div>
          <div><p className="text-xs text-slate-500">Красные флаги</p><p className="text-2xl font-bold text-white">{totalFlags}</p></div>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-72 animate-pulse rounded-2xl bg-surface-100" />)}
        </div>
      ) : error ? (
        <div className="glass rounded-2xl p-6 text-neon-pink">{error}</div>
      ) : properties.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
          <Home className="mb-4 h-12 w-12 text-slate-600" />
          <p className="text-lg font-medium text-slate-400">Объектов пока нет.</p>
          <Link href="/" className="mt-4 text-neon-cyan hover:underline cursor-pointer">Проанализируйте первый объект</Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((p) => <PropertyCard key={p.id} property={p} />)}
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="glass rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white disabled:opacity-40 transition cursor-pointer">Назад</button>
          <span className="text-sm text-slate-500">{page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)} className="glass rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white disabled:opacity-40 transition cursor-pointer">Вперёд</button>
        </div>
      )}
    </div>
  );
}
