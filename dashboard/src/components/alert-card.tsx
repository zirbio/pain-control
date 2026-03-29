"use client";

import Link from "next/link";

interface AlertCardProps {
  title: string;
  body: string;
  metadata?: string;
  type?: "correlation" | "trend" | "pattern";
}

export function AlertCard({ title, body, metadata }: AlertCardProps) {
  return (
    <div className="bg-bg-surface border border-bg-tertiary rounded-card p-4 border-l-[3px] border-l-accent-warning transition-shadow duration-200 hover:shadow-[inset_2px_0_0_0_currentColor]">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-accent-warning" aria-hidden="true">◆</span>
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {title}
        </span>
      </div>
      <p className="font-body text-body text-text-primary">{body}</p>
      {metadata && (
        <p className="font-body text-small text-text-muted mt-2">{metadata}</p>
      )}
      <Link
        href="/analysis"
        className="font-body text-small text-accent-info hover:text-text-primary transition-colors mt-2 inline-block"
      >
        Ver en Análisis →
      </Link>
    </div>
  );
}
