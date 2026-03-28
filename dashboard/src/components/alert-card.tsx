"use client";

interface AlertCardProps {
  title: string;
  body: string;
  metadata?: string;
  type?: "correlation" | "trend" | "pattern";
}

export function AlertCard({ title, body, metadata, type = "correlation" }: AlertCardProps) {
  return (
    <div className="bg-bg-surface border border-bg-tertiary rounded-card p-4 border-l-[3px] border-l-accent-warning transition-all duration-200 hover:border-l-[5px]">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-accent-warning">◆</span>
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {title}
        </span>
      </div>
      <p className="font-body text-body text-text-primary">{body}</p>
      {metadata && (
        <p className="font-body text-small text-text-muted mt-2">{metadata}</p>
      )}
    </div>
  );
}
