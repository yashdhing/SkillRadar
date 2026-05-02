import Link from "next/link";
import type { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Generate" },
  { href: "/library", label: "Library" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-frame">
      <header className="app-header">
        <div>
          <p className="eyebrow">SkillRadar</p>
          <h1 className="app-title">Personal study radar for backend growth.</h1>
        </div>

        <nav className="top-nav" aria-label="Primary">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      {children}
    </div>
  );
}

