"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { analyseProperty } from "@/lib/api";

const LOADING_STEPS = [
  "Сбор данных из объявления…",
  "Извлечение характеристик объекта…",
  "Запуск модели оценки XGBoost…",
  "Gemini анализирует фото интерьера…",
  "Поиск красных флагов через AI-Vision…",
  "Расчёт инвестиционного рейтинга…",
  "Генерация сопоставимых продаж…",
  "Формирование отчёта…",
];

export default function LandingPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (loading) {
      setLoadingStep(0);
      intervalRef.current = setInterval(() => {
        setLoadingStep((prev) =>
          prev < LOADING_STEPS.length - 1 ? prev + 1 : prev
        );
      }, 3000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await analyseProperty(url.trim());
      router.push(`/analysis/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Произошла непредвиденная ошибка.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      {/* Hero */}
      <div className="mb-10 space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-brand-800 bg-brand-950/40 px-4 py-1.5 text-sm text-brand-300">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500" />
          </span>
          AI-анализ на базе Gemini & XGBoost
        </div>

        <h1 className="text-5xl font-extrabold tracking-tight text-slate-50 sm:text-6xl">
          Узнайте реальную{" "}
          <span className="bg-gradient-to-r from-brand-400 to-accent bg-clip-text text-transparent">
            стоимость недвижимости
          </span>
        </h1>

        <p className="mx-auto max-w-2xl text-lg text-slate-400">
          Вставьте ссылку на объявление. ProphetAI соберёт данные, запустит
          AI-анализ фотографий и вернёт мгновенную оценку рыночной стоимости
          с выявлением рисков — за секунды.
        </p>
      </div>

      {/* URL input form */}
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-2xl flex-col gap-3 sm:flex-row"
      >
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.house.kg/details/..."
          required
          className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3.5 text-slate-100 placeholder-slate-500 outline-none ring-0 transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl bg-brand-600 px-6 py-3.5 font-semibold text-white shadow-lg shadow-brand-900/40 transition hover:bg-brand-500 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Анализ…
            </span>
          ) : (
            "Анализировать →"
          )}
        </button>
      </form>

      {/* Step-by-step loading indicator */}
      {loading && (
        <div className="mt-6 w-full max-w-2xl">
          <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm text-brand-400">
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span className="font-medium">{LOADING_STEPS[loadingStep]}</span>
            </div>
            <div className="space-y-1.5">
              {LOADING_STEPS.map((step, i) => (
                <div key={step} className="flex items-center gap-2 text-xs">
                  {i < loadingStep ? (
                    <span className="text-green-400">✓</span>
                  ) : i === loadingStep ? (
                    <span className="animate-pulse text-brand-400">▶</span>
                  ) : (
                    <span className="text-slate-600">○</span>
                  )}
                  <span className={i <= loadingStep ? "text-slate-300" : "text-slate-600"}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-brand-500 transition-all duration-1000"
                style={{ width: `${((loadingStep + 1) / LOADING_STEPS.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {error && (
        <p className="mt-4 rounded-lg border border-red-800 bg-red-950/40 px-4 py-2 text-sm text-red-400">
          {error}
        </p>
      )}

      {/* Feature cards */}
      <div className="mt-20 grid gap-6 sm:grid-cols-3">
        {[
          {
            icon: "💰",
            title: "Умная оценка стоимости",
            desc: "Модель XGBoost оценивает рыночную стоимость с доверительным интервалом ±12%.",
          },
          {
            icon: "📊",
            title: "Инвестиционный рейтинг",
            desc: "Комплексная оценка 0–100 с доходностью аренды, трендом роста цен и аналогами.",
          },
          {
            icon: "🖼️",
            title: "AI-анализ фотографий",
            desc: "Gemini Vision определяет риски, состояние комнат и стоимость ремонта.",
          },
        ].map((f) => (
          <div
            key={f.title}
            className="gradient-border rounded-2xl bg-slate-900/60 p-6 text-left backdrop-blur-sm"
          >
            <div className="mb-3 text-3xl">{f.icon}</div>
            <h3 className="mb-1 font-semibold text-slate-100">{f.title}</h3>
            <p className="text-sm text-slate-400">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
