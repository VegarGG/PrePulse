import Link from "next/link";
import { Shield } from "lucide-react";

const NAV_LINKS = [
  { href: "/", label: "Run" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/history", label: "History" },
  { href: "/about", label: "About" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto max-w-7xl px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Shield className="h-5 w-5" />
            <span>PrePulse</span>
          </Link>
          <nav className="flex items-center gap-6 text-sm text-muted-foreground">
            {NAV_LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="hover:text-foreground transition-colors">
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="flex-1 mx-auto max-w-7xl w-full px-6 py-8">{children}</main>
      <footer className="border-t text-xs text-muted-foreground">
        <div className="mx-auto max-w-7xl px-6 h-10 flex items-center justify-between">
          <span>PrePulse Prototype v0.2.0</span>
          <span>NYU Tandon · MG-9781</span>
        </div>
      </footer>
    </div>
  );
}
