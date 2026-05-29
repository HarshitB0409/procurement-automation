import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Procurement Automation",
  description: "AI-powered procurement request and approval system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-4">
            <span className="text-lg font-semibold text-slate-800">
              Procurement Automation
            </span>
            <a href="/" className="text-sm text-slate-600 hover:text-slate-900">
              New Request
            </a>
            <a
              href="/approver"
              className="text-sm text-slate-600 hover:text-slate-900"
            >
              Approver Dashboard
            </a>
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
