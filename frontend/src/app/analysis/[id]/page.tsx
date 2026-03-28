"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getProperty, type PropertyDetail } from "@/lib/api";
import MarketPosition from "@/components/MarketPosition";
import RedFlagCard from "@/components/RedFlagCard";
import PhotoInsightCard from "@/components/PhotoInsightCard";
import InvestmentScoreGauge from "@/components/InvestmentScoreGauge";
import {
  ArrowLeft, Bed, Bath, Maximize, Calendar, ExternalLink,
  TrendingUp, Percent, AlertTriangle, ChevronLeft, ChevronRight,
  X, Images, Phone, MapPin,
} from "lucide-react";

function fmt(n: number | null | undefined, opts?: Intl.NumberFormatOptions) {
  if (n == null) return "\u2014";
  return new Intl.NumberFormat("en-US", opts).format(n);
}
function fmtUSD(n: number | null | undefined) {
  return fmt(n, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

const STATUS: Record<string, string> = {
  completed: "bg-neon-cyan/10 text-neon-cyan",
  processing: "bg-neon-blue/10 text-neon-blue",
  failed: "bg-neon-pink/10 text-neon-pink",
  pending: "bg-surface-200 text-slate-400",
};

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;
    getProperty(Number(id))
      .then(setProperty)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const photos: string[] = [];
  if (property) {
    property.photos?.forEach((p) => { if (p.url) photos.push(p.url); });
    property.photo_insights?.forEach((p) => { if (p.photo_url && !photos.includes(p.photo_url)) photos.push(p.photo_url); });
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <svg className="h-8 w-8 animate-spin text-neon-cyan" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
          </svg>
          <p className="text-sm">Загружаю анализ...</p>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return <div className="glass rounded-2xl p-6 text-neon-pink">{error ?? "Объект не найден."}</div>;
  }

  // delta > 0 → listing is ABOVE market (overprice, bad for buyer → red)
  // delta < 0 → listing is BELOW market (good deal → cyan)
  const delta = property.price_delta_pct;
  const isOverpriced = delta !== null && delta > 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Lightbox */}
      {lightbox !== null && photos.length > 0 && (
        <div className="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center" onClick={() => setLightbox(null)}>
          <button className="absolute top-5 right-5 text-slate-500 hover:text-white cursor-pointer" onClick={() => setLightbox(null)}><X className="h-6 w-6" /></button>
          <button className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white cursor-pointer"
            onClick={(e) => { e.stopPropagation(); setLightbox((i) => (i! > 0 ? i! - 1 : photos.length - 1)); }}>
            <ChevronLeft className="h-8 w-8" />
          </button>
          <button className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white cursor-pointer"
            onClick={(e) => { e.stopPropagation(); setLightbox((i) => (i! < photos.length - 1 ? i! + 1 : 0)); }}>
            <ChevronRight className="h-8 w-8" />
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photos[lightbox]} alt="" className="max-h-[85vh] max-w-[92vw] rounded-xl object-contain" onClick={(e) => e.stopPropagation()} />
          <p className="absolute bottom-5 text-sm text-slate-600">{lightbox + 1} / {photos.length}</p>
        </div>
      )}

      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-neon-cyan transition cursor-pointer">
        <ArrowLeft className="h-4 w-4" /> Назад
      </button>

      {/* Photo Gallery */}
      {photos.length > 0 && (
        <div className="grid gap-2 rounded-2xl overflow-hidden" style={{
          gridTemplateColumns: photos.length === 1 ? "1fr" : "3fr 1fr",
          gridTemplateRows: photos.length <= 2 ? "320px" : "160px 160px",
        }}>
          <div className={`relative overflow-hidden cursor-pointer group ${photos.length > 2 ? "row-span-2" : ""}`} onClick={() => setLightbox(0)}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={photos[0]} alt="" className="h-full w-full object-cover group-hover:scale-[1.03] transition-transform duration-700" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
            <div className="absolute bottom-3 left-3 flex items-center gap-1.5 bg-black/50 backdrop-blur-sm rounded-full px-3 py-1.5 text-xs text-white font-medium">
              <Images className="h-3.5 w-3.5" /> {photos.length} фото
            </div>
          </div>
          {photos.slice(1, photos.length > 2 ? 3 : 2).map((url, i) => (
            <div key={i} className="relative overflow-hidden cursor-pointer group" onClick={() => setLightbox(i + 1)}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="" className="h-full w-full object-cover group-hover:scale-[1.03] transition-transform duration-700" />
              {i === (photos.length > 2 ? 1 : 0) && photos.length > 3 && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center backdrop-blur-sm">
                  <span className="text-white font-semibold">+{photos.length - 3} ещё</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="glass rounded-2xl p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{property.address || "Адрес недоступен"}</h1>
            <p className="mt-0.5 text-slate-400">{[property.city, property.state, property.zip_code].filter(Boolean).join(", ")}</p>
            <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-400">
              {property.bedrooms != null && <span className="flex items-center gap-1.5"><Bed className="h-4 w-4 text-slate-500" />{property.bedrooms} спальня</span>}
              {property.bathrooms != null && <span className="flex items-center gap-1.5"><Bath className="h-4 w-4 text-slate-500" />{property.bathrooms} ванных</span>}
              {property.square_feet != null && <span className="flex items-center gap-1.5"><Maximize className="h-4 w-4 text-slate-500" />{fmt(property.square_feet)} м²</span>}
              {property.year_built != null && <span className="flex items-center gap-1.5"><Calendar className="h-4 w-4 text-slate-500" />Построен {property.year_built}</span>}
            </div>
          </div>
          <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium capitalize ${STATUS[property.status] ?? STATUS.pending}`}>{property.status}</span>
        </div>

        <div className="mt-6 grid gap-3 sm:gap-4 grid-cols-1 sm:grid-cols-3 border-t border-glass-border pt-6">
          <div>
            <p className="text-xs text-slate-500">Цена объявления</p>
            <p className="mt-1 text-2xl font-bold text-white">{fmtUSD(property.listing_price)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Оценочная стоимость</p>
            <p className="mt-1 text-2xl font-bold text-neon-cyan">{fmtUSD(property.ai_estimated_price)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Переплата от рынка</p>
            <p className={`mt-1 text-2xl font-bold ${delta == null ? "text-slate-500" : isOverpriced ? "text-neon-pink" : "text-neon-cyan"}`}>
              {delta == null ? "—" : `${isOverpriced ? "+" : ""}${delta.toFixed(1)}%`}
            </p>
            {delta != null && (
              <p className="text-xs text-slate-500">
                {isOverpriced ? "Выше рыночной оценки" : "Ниже рыночной оценки"}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
        <div className="col-span-2 sm:col-span-1 glass rounded-2xl p-5 flex flex-col items-center justify-center">
          <p className="mb-3 text-xs text-slate-500">Инв. рейтинг</p>
          <InvestmentScoreGauge score={property.investment_score} />
        </div>
        {[
          { icon: Percent, label: "Арендная доходность", value: typeof property.rental_yield_pct === "number" ? `${property.rental_yield_pct.toFixed(1)}%` : "—", sub: "Расчётная валовая годовая", color: "text-neon-cyan" },
          { icon: TrendingUp, label: "Прирост стоимости", value: typeof property.appreciation_trend_pct === "number" ? `${property.appreciation_trend_pct.toFixed(1)}%` : "—", sub: "Среднее по району за 12 мес.", color: "text-neon-purple" },
          { icon: AlertTriangle, label: "Красные флаги", value: String(property.red_flags?.length ?? 0), sub: "Выявлено проблем", color: "text-neon-pink" },
        ].map((m) => (
          <div key={m.label} className="glass rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-1"><m.icon className={`h-4 w-4 ${m.color}`} /><p className="text-xs text-slate-500">{m.label}</p></div>
            <p className="mt-1 text-2xl font-bold text-white">{m.value}</p>
            <p className="mt-1 text-xs text-slate-500">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Market Position */}
      {property.comparable_sales && property.comparable_sales.length > 0 && (
        <div className="glass rounded-2xl p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">Позиция на рынке</h2>
          <MarketPosition property={property} comparables={property.comparable_sales} />
        </div>
      )}

      {/* Red Flags */}
      {property.red_flags && property.red_flags.length > 0 && (
        <div>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
            <AlertTriangle className="h-5 w-5 text-neon-pink" /> Красные флаги ({property.red_flags.length})
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {property.red_flags.map((flag, i) => <RedFlagCard key={i} flag={flag} />)}
          </div>
        </div>
      )}

      {/* Photo Analysis */}
      {property.photo_insights && property.photo_insights.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-white">Анализ фотографий</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {property.photo_insights.map((insight, i) => (
              <PhotoInsightCard key={i} insight={insight} onPhotoClick={() => {
                const idx = photos.indexOf(insight.photo_url);
                if (idx !== -1) setLightbox(idx);
              }} />
            ))}
          </div>
        </div>
      )}

      {/* Listing Params */}
      {property.listing_params && Object.keys(property.listing_params).length > 0 && (
        <div className="glass rounded-2xl p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">Характеристики объявления</h2>
          <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(property.listing_params).map(([k, v]) => (
              <div key={k} className="flex justify-between gap-2 border-b border-glass-border py-1.5 text-sm">
                <span className="text-slate-500 shrink-0">{k}</span>
                <span className="text-slate-200 text-right">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phone + Map */}
      {(property.phone_number || (property.map_lat && property.map_lng)) && (
        <div className="grid gap-4 sm:grid-cols-2">
          {property.phone_number && (
            <div className="glass rounded-2xl p-5 flex flex-col gap-3">
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Phone className="h-4 w-4 text-neon-cyan" /> Контакт продавца
              </div>
              <div className="flex flex-wrap gap-2">
                <a
                  href={`tel:${property.phone_number}`}
                  className="flex items-center gap-1.5 rounded-lg bg-neon-cyan/10 px-4 py-2 text-neon-cyan text-sm font-medium hover:bg-neon-cyan/20 transition cursor-pointer"
                >
                  <Phone className="h-3.5 w-3.5" /> {property.phone_number}
                </a>
                <a
                  href={`https://wa.me/${property.phone_number.replace(/\D/g, "")}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-lg bg-green-500/10 px-4 py-2 text-green-400 text-sm font-medium hover:bg-green-500/20 transition cursor-pointer"
                >
                  WhatsApp
                </a>
              </div>
            </div>
          )}
          {property.map_lat && property.map_lng && (
            <div className="glass rounded-2xl overflow-hidden">
              <a
                href={`https://www.google.com/maps?q=${property.map_lat},${property.map_lng}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block cursor-pointer"
              >
                <iframe
                  src={`https://www.openstreetmap.org/export/embed.html?bbox=${property.map_lng - 0.005},${property.map_lat - 0.005},${property.map_lng + 0.005},${property.map_lat + 0.005}&layer=mapnik&marker=${property.map_lat},${property.map_lng}`}
                  className="h-40 w-full pointer-events-none"
                  title="Карта"
                />
                <div className="flex items-center gap-1.5 px-4 py-2 text-xs text-slate-500">
                  <MapPin className="h-3 w-3" /> Открыть в Google Maps
                </div>
              </a>
            </div>
          )}
        </div>
      )}

      {/* Source */}
      <div className="glass rounded-2xl p-4 text-sm text-slate-500">
        <span className="text-slate-400">Источник: </span>
        <a href={property.listing_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-neon-cyan hover:underline break-all cursor-pointer">
          {property.listing_url} <ExternalLink className="h-3 w-3 shrink-0" />
        </a>
      </div>
    </div>
  );
}
