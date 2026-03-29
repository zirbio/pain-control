"use client";

import type { ComponentType, SVGProps } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelIcon, AnalysisIcon, HistoryIcon, CoverageIcon } from "./nav-icons";

const links: { href: string; label: string; Icon: ComponentType<SVGProps<SVGSVGElement>> }[] = [
  { href: "/", label: "Panel", Icon: PanelIcon },
  { href: "/analysis", label: "Análisis", Icon: AnalysisIcon },
  { href: "/history", label: "Historial", Icon: HistoryIcon },
  { href: "/coverage", label: "Cobertura", Icon: CoverageIcon },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-tertiary z-50 md:static md:border-t-0 md:border-b"
      style={{ paddingBottom: "max(env(safe-area-inset-bottom, 0px), 0px)" }}
    >
      <div className="max-w-6xl mx-auto flex items-center justify-center gap-4 md:gap-8 px-4 md:px-6 py-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`min-h-[44px] flex flex-col items-center justify-center gap-0.5 font-body text-small transition-colors focus-visible:ring-2 focus-visible:ring-accent-info focus-visible:rounded-md px-2 ${
                active
                  ? "text-accent-highlight"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              <link.Icon />
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
