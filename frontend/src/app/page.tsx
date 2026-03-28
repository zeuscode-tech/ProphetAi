"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { analyseProperty } from "@/lib/api";
import { Search, TrendingUp, Shield, BarChart3, ArrowRight, Sparkles } from "lucide-react";

export default function LandingPage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyseProperty(url.trim());
      router.push(`/analysis/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Что-то пошло не так.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[75vh]">
      <div className="orb top-0 -left-40 h-80 w-80 bg-neon-cyan/20" />
      <div className="orb top-20 -right-40 h-96 w-96 bg-neon-purple/20" style={{ animationDelay: "2s" }} />
      <div className="orb bottom-0 left-1/3 h-64 w-64 bg-neon-blue/15" style={{ animationDelay: "4s" }} />

      <div className="animate-fade-in mb-6">
        <div className="glass inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm text-slate-400">
          <Sparkles className="h-3.5 w-3.5 text-neon-cyan" />
          Аналитика недвижимости на базе ИИ
        </div>
      </div>

      <div className="animate-slide-up mb-10 max-w-3xl text-center">
        <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-7xl leading-[1.1]">
          Узнайте реальную{" "}
          <span className="text-gradient">стоимость объекта</span>
        </h1>
        <p className="mt-6 text-lg text-slate-400 leading-relaxed max-w-xl mx-auto">
          Вставьте ссылку на любое объявление. Получите мгновенную оценку стоимости,
          инвестиционный рейтинг и ИИ-анализ фотографий с выявлением проблем.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="animate-slide-up relative z-10 flex w-full max-w-2xl flex-col gap-3 sm:flex-row" style={{ animationDelay: "0.1s" }}>
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Вставьте ссылку на объявление (zillow.com, redfin.com...)"
            required
            className="w-full rounded-xl border border-glass-border-light bg-surface-50 py-4 pl-11 pr-4 text-white placeholder-slate-500 outline-none transition-all focus:border-neon-cyan/50 focus:shadow-glow focus:bg-surface-100"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="group flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-blue px-7 py-4 font-semibold text-surface shadow-glow transition-all hover:shadow-glow-lg disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {loading ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Анализирую...
            </>
          ) : (
            <>Анализировать <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" /></>
          )}
        </button>
      </form>

      {error && (
        <p className="mt-4 glass rounded-xl border-neon-pink/30 px-4 py-3 text-sm text-neon-pink animate-fade-in">{error}</p>
      )}

      <div className="mt-12 sm:mt-20 grid w-full gap-4 sm:gap-5 grid-cols-1 sm:grid-cols-3">
        {[
          { icon: TrendingUp, title: "Рыночная стоимость", desc: "ИИ определяет справедливую рыночную цену с доверительными интервалами на основе данных о сопоставимых продажах.", color: "text-neon-cyan", glow: "group-hover:shadow-glow" },
          { icon: BarChart3, title: "Инвест. рейтинг", desc: "Оценка 0–100 с учётом арендной доходности, тенденций роста стоимости и сравнений по району.", color: "text-neon-purple", glow: "group-hover:shadow-glow-purple" },
          { icon: Shield, title: "Отчёт о состоянии", desc: "Анализ фотографий выявляет конструктивные дефекты, следы протечек и оценивает стоимость ремонта.", color: "text-neon-blue", glow: "group-hover:shadow-glow-blue" },
        ].map((f, i) => (
          <div key={f.title} className={`group glass-hover rounded-2xl p-5 sm:p-6 ${f.glow} animate-slide-up cursor-default`} style={{ animationDelay: `${0.2 + i * 0.1}s` }}>
            <div className={`mb-4 ${f.color}`}><f.icon className="h-6 w-6" /></div>
            <h3 className="mb-2 text-lg font-semibold text-white">{f.title}</h3>
            <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
