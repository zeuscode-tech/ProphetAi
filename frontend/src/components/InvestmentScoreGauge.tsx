"use client";

interface Props { score: number | null | undefined; }

export default function InvestmentScoreGauge({ score }: Props) {
  const value = score ?? 0;
  const capped = Math.min(Math.max(value, 0), 100);
  const R = 52, cx = 64, cy = 64, sw = 8;
  const startAngle = 225, sweepAngle = 270;
  const endAngle = startAngle + (capped / 100) * sweepAngle;

  function polar(a: number) {
    const r = ((a - 90) * Math.PI) / 180;
    return { x: cx + R * Math.cos(r), y: cy + R * Math.sin(r) };
  }
  function arc(s: number, e: number) {
    const a = polar(s), b = polar(e);
    return `M ${a.x} ${a.y} A ${R} ${R} 0 ${e - s > 180 ? 1 : 0} 1 ${b.x} ${b.y}`;
  }

  // 4 investment zones
  const color = capped >= 75 ? "#06d6a0"   // green  — Рекомендуем
              : capped >= 50 ? "#fbbf24"    // yellow — Нейтрально
              : capped >= 25 ? "#f97316"    // orange — Зона риска
              : "#f72585";                  // red    — Осторожно
  const glow  = capped >= 75 ? "drop-shadow(0 0 6px rgba(6,214,160,0.5))"
              : capped >= 50 ? "drop-shadow(0 0 6px rgba(251,191,36,0.5))"
              : capped >= 25 ? "drop-shadow(0 0 6px rgba(249,115,22,0.5))"
              : "drop-shadow(0 0 6px rgba(247,37,133,0.5))";
  const label = capped >= 75 ? "Рекомендуем"
              : capped >= 50 ? "Нейтрально"
              : capped >= 25 ? "Зона риска"
              : "Осторожно";

  return (
    <div className="flex flex-col items-center">
      <svg width="128" height="100" viewBox="0 0 128 100">
        <path d={arc(startAngle, startAngle + sweepAngle)} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={sw} strokeLinecap="round" />
        {capped > 0 && <path d={arc(startAngle, endAngle)} fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" style={{ filter: glow }} />}
        <text x={cx} y={cx + 6} textAnchor="middle" fontSize="24" fontWeight="800" fill="#fff" fontFamily="Inter,sans-serif">{score != null ? Math.round(capped) : "\u2014"}</text>
        <text x={cx} y={cx + 22} textAnchor="middle" fontSize="9" fill="#64748b" fontFamily="Inter,sans-serif">/ 100</text>
      </svg>
      <p className="text-sm font-semibold" style={{ color }}>{label}</p>
    </div>
  );
}
