import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProphetAI — AI-аналитика недвижимости",
  description:
    "Вставьте ссылку на объявление и получите мгновенную AI-оценку стоимости и выявление рисков.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        {/* Top navigation bar */}
        <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <a href="/" className="flex items-center gap-2">
              <span className="text-2xl font-bold tracking-tight text-brand-400">
                Prophet<span className="text-accent">AI</span>
              </span>
              <span className="rounded bg-accent/20 px-1.5 py-0.5 text-xs font-semibold text-accent-light">
                BETA
              </span>
            </a>
            <div className="flex items-center gap-6 text-sm font-medium text-slate-400">
              <a href="/dashboard" className="hover:text-slate-100 transition-colors">
                Панель
              </a>
              <a
                href="/"
                className="rounded-lg bg-brand-600 px-4 py-1.5 text-white hover:bg-brand-500 transition-colors"
              >
                + Новый анализ
              </a>
            </div>
          </div>
        </nav>

        <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>

        <footer className="mt-16 border-t border-slate-800 py-6 text-center text-xs text-slate-600">
          © {new Date().getFullYear()} ProphetAI · Создано ZeusCode Tech ·{" "}
          <span className="text-slate-500">На базе Gemini & XGBoost</span>
        </footer>
      </body>
    </html>
  );
}
