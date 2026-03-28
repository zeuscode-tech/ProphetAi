"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProperties, type PropertySummary } from "@/lib/api";
import PropertyCard from "@/components/PropertyCard";

export default function DashboardPage() {
  const [properties, setProperties] = useState<PropertySummary[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getProperties(page)
      .then((data) => {
        setProperties(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(count / 20));

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Панель объектов</h1>
          <p className="mt-1 text-sm text-slate-400">
            {count} объект{count !== 1 ? "ов" : ""} проанализировано
          </p>
        </div>
        <Link
          href="/"
          className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors"
        >
          + Новый анализ
        </Link>
      </div>

      {/* Summary stats */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {[
          { label: "Всего проанализ.", value: count },
          {
            label: "Средн. рейтинг",
            value:
              properties.length > 0
                ? (
                    properties
                      .filter((p) => p.investment_score !== null)
                      .reduce((acc, p) => acc + (p.investment_score ?? 0), 0) /
                    Math.max(
                      1,
                      properties.filter((p) => p.investment_score !== null).length,
                    )
                  ).toFixed(1)
                : "—",
          },
          {
            label: "Красных флагов",
            value: properties.reduce((acc, p) => acc + (p.red_flags?.length ?? 0), 0),
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="gradient-border rounded-2xl bg-slate-900/60 p-5"
          >
            <p className="text-xs font-medium uppercase tracking-widest text-slate-500">
              {stat.label}
            </p>
            <p className="mt-1 text-3xl font-bold text-slate-100">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Property grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-56 animate-pulse rounded-2xl bg-slate-800"
            />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-800 bg-red-950/30 p-6 text-red-400">
          {error}
        </div>
      ) : properties.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-slate-500">
          <span className="text-5xl mb-4">🏠</span>
          <p className="text-lg font-medium">Объекты ещё не анализировались.</p>
          <Link href="/" className="mt-4 text-brand-400 hover:underline">
            Анализировать первое объявление →
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {properties.map((p) => (
            <PropertyCard key={p.id} property={p} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-400 hover:border-slate-500 disabled:opacity-40"
          >
            ← Назад
          </button>
          <span className="text-sm text-slate-500">
            Страница {page} из {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-400 hover:border-slate-500 disabled:opacity-40"
          >
            Далее →
          </button>
        </div>
      )}
    </div>
  );
}
