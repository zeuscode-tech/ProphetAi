import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProphetAI \u2014 Smart Property Analytics",
  description: "Instant property valuations and condition reports from any listing URL.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface text-slate-200 antialiased">
        <nav className="fixed top-0 left-0 right-0 z-50">
          <div className="mx-4 mt-4">
            <div className="glass mx-auto flex max-w-6xl items-center justify-between rounded-2xl px-6 py-3">
              <a href="/" className="flex items-center gap-2.5 cursor-pointer">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-neon-cyan to-neon-blue">
                  <span className="text-sm font-black text-surface">P</span>
                </div>
                <span className="text-lg font-bold text-white">
                  Prophet<span className="text-gradient">AI</span>
                </span>
              </a>
              <div className="flex items-center gap-1 text-sm">
                <a href="/dashboard" className="rounded-xl px-4 py-2 text-slate-400 transition-colors hover:text-white cursor-pointer">Dashboard</a>
                <a href="/" className="rounded-xl bg-gradient-to-r from-neon-cyan to-neon-blue px-5 py-2 font-semibold text-surface transition-all hover:shadow-glow cursor-pointer">New Analysis</a>
              </div>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-6xl px-6 pt-28 pb-8">{children}</main>
        <footer className="border-t border-glass-border py-6 text-center text-xs text-slate-600">
          &copy; {new Date().getFullYear()} ProphetAI &middot; Built by ZeusCode Tech
        </footer>
      </body>
    </html>
  );
}
