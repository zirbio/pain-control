"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/analysis", label: "Analysis" },
  { href: "/history", label: "History" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-tertiary z-50 md:static md:border-t-0 md:border-b">
      <div className="max-w-6xl mx-auto flex items-center justify-center gap-8 px-6 py-3">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`font-body text-body transition-colors ${
                active
                  ? "text-accent-highlight"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
