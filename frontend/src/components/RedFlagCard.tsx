import type { RedFlag } from "@/lib/api";

interface Props {
  flag: RedFlag;
}

const SEVERITY_STYLES: Record<string, { badge: string; border: string; bg: string }> = {
  high: {
    badge: "bg-red-900/60 text-red-300",
    border: "border-red-800",
    bg: "bg-red-950/30",
  },
  medium: {
    badge: "bg-amber-900/60 text-amber-300",
    border: "border-amber-800",
    bg: "bg-amber-950/20",
  },
  low: {
    badge: "bg-blue-900/50 text-blue-300",
    border: "border-blue-900",
    bg: "bg-blue-950/20",
  },
};

const CATEGORY_ICONS: Record<string, string> = {
  "Конструкция": "🏗️",
  "Влага / протечки": "💧",
  "Электрика": "⚡",
  "Косметика": "🎨",
  "Документы": "⚖️",
  "Цена": "💲",
  "Завышена цена": "💲",
};

function detectCategory(text: string): string {
  const lower = text.toLowerCase();
  if (lower.includes("overpric") || lower.includes("price") || lower.includes("цен")) return "Цена";
  if (lower.includes("structur") || lower.includes("foundation") || lower.includes("crack") || lower.includes("конструк") || lower.includes("фундамент") || lower.includes("трещин")) return "Конструкция";
  if (lower.includes("water") || lower.includes("leak") || lower.includes("mold") || lower.includes("влаг") || lower.includes("протеч") || lower.includes("плесен")) return "Влага / протечки";
  if (lower.includes("electr") || lower.includes("wiring") || lower.includes("электр") || lower.includes("провод")) return "Электрика";
  if (lower.includes("cosmetic") || lower.includes("paint") || lower.includes("interior") || lower.includes("косметич") || lower.includes("краск") || lower.includes("интерьер")) return "Косметика";
  if (lower.includes("legal") || lower.includes("permit") || lower.includes("document") || lower.includes("документ") || lower.includes("разрешен")) return "Документы";
  // Instead of "Other", derive a short summary from the issue text
  return summarizeIssue(text);
}

function summarizeIssue(text: string): string {
  // Take first meaningful words (up to ~30 chars) as category label
  const cleaned = text.replace(/[.!?,;:]+$/, "").trim();
  if (cleaned.length <= 30) return cleaned;
  const truncated = cleaned.slice(0, 30).replace(/\s+\S*$/, "");
  return truncated + "…";
}

export default function RedFlagCard({ flag }: Props) {
  const severity = (flag.severity || "medium").toLowerCase();
  const styles = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.medium;
  const issueText = flag.issue || flag.description || "";
  const category = flag.category || detectCategory(issueText);
  const icon = CATEGORY_ICONS[category] ?? "⚠️";

  return (
    <div
      className={`rounded-xl border ${styles.border} ${styles.bg} p-4`}
    >
      <div className="flex items-start gap-3">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-slate-200">
              {category}
            </span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${styles.badge}`}
            >
              {severity}
            </span>
          </div>
          <p className="mt-1.5 text-xs leading-relaxed text-slate-400">
            {issueText}
          </p>
        </div>
      </div>
    </div>
  );
}
