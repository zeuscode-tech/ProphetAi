import Link from "next/link";

export default function AnalysisFallbackPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="glass rounded-2xl p-6 text-center">
        <h1 className="text-xl font-bold text-white">Analysis page</h1>
        <p className="mt-2 text-slate-400">
          Для открытия анализа нужен ID объекта.
        </p>
        <Link
          href="/"
          className="mt-4 inline-block rounded-lg bg-cyan-500 px-4 py-2 text-white"
        >
          Вернуться на главную
        </Link>
      </div>
    </div>
  );
}