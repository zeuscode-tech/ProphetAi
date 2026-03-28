import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProphetAI — Умная аналитика недвижимости",
  description: "Мгновенная оценка стоимости недвижимости и отчёт о состоянии по любой ссылке на объявление.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-surface text-slate-200 antialiased">
        <nav className="fixed top-0 left-0 right-0 z-50">
          <div className="mx-2 mt-3 sm:mx-4 sm:mt-4">
            <div className="glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-3 py-2.5 sm:px-6 sm:py-3">
              <a href="/" className="flex items-center gap-2 cursor-pointer">
                <div className="flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-lg bg-gradient-to-br from-neon-cyan to-neon-blue shrink-0">
                  <span className="text-xs sm:text-sm font-black text-surface">P</span>
                </div>
                <span className="text-base sm:text-lg font-bold text-white">
                  Prophet<span className="text-gradient">AI</span>
                </span>
              </a>
              <div className="flex items-center gap-1 text-xs sm:text-sm">
                <a href="/dashboard" className="rounded-xl px-3 py-2 sm:px-4 text-slate-400 transition-colors hover:text-white cursor-pointer">
                  <span className="hidden sm:inline">Дашборд</span>
                  <span className="sm:hidden">Борд</span>
                </a>
                <a href="/" className="rounded-xl bg-gradient-to-r from-neon-cyan to-neon-blue px-3 py-1.5 sm:px-5 sm:py-2 font-semibold text-surface transition-all hover:shadow-glow cursor-pointer whitespace-nowrap">
                  <span className="hidden sm:inline">Новый анализ</span>
                  <span className="sm:hidden">Анализ</span>
                </a>
              </div>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-4 sm:px-6 pt-24 sm:pt-28 pb-8">{children}</main>
        <footer className="border-t border-glass-border py-6 text-center text-xs text-slate-600">
          &copy; {new Date().getFullYear()} ProphetAI &middot; Создано ZeusCode Tech
        </footer>
      </body>
    </html>
  );
}
