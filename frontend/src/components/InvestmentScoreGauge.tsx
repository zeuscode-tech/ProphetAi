"use client";

interface Props {
  score: number | null | undefined;
}

export default function InvestmentScoreGauge({ score }: Props) {
  const value = score ?? 0;
  const capped = Math.min(Math.max(value, 0), 100);

  // SVG arc parameters
  const R = 52;
  const cx = 64;
  const cy = 64;
  const strokeWidth = 10;
  // Arc from 225° to 315° (270° sweep)
  const startAngle = 225;
  const sweepAngle = 270;
  const endAngle = startAngle + (capped / 100) * sweepAngle;

  function polarToCartesian(angle: number) {
    const rad = ((angle - 90) * Math.PI) / 180;
    return {
      x: cx + R * Math.cos(rad),
      y: cy + R * Math.sin(rad),
    };
  }

  function describeArc(start: number, end: number) {
    const s = polarToCartesian(start);
    const e = polarToCartesian(end);
    const large = end - start > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${R} ${R} 0 ${large} 1 ${e.x} ${e.y}`;
  }

  const trackPath = describeArc(startAngle, startAngle + sweepAngle);
  const fillPath = capped > 0 ? describeArc(startAngle, endAngle) : "";

  const fillColor =
    capped >= 70 ? "#22c55e" : capped >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width="128" height="100" viewBox="0 0 128 100">
        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#1e293b"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Fill */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={fillColor}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
        )}
        {/* Score text */}
        <text
          x={cx}
          y={cy + 6}
          textAnchor="middle"
          fontSize="22"
          fontWeight="bold"
          fill="#f1f5f9"
          fontFamily="Inter, sans-serif"
        >
          {score != null ? Math.round(capped) : "—"}
        </text>
        <text
          x={cx}
          y={cy + 22}
          textAnchor="middle"
          fontSize="9"
          fill="#64748b"
          fontFamily="Inter, sans-serif"
        >
          / 100
        </text>
      </svg>
      <p
        className="text-sm font-semibold"
        style={{ color: fillColor }}
      >
        {capped >= 70 ? "Покупать" : capped >= 40 ? "Нейтрально" : "Осторожно"}
      </p>
    </div>
  );
}
