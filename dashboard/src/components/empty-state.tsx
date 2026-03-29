type EmptyStateVariant = "no-entries" | "no-data" | "insufficient-data";

interface EmptyStateProps {
  variant: EmptyStateVariant;
}

const variants: Record<EmptyStateVariant, { title: string; subtitle: string; illustration: React.ReactNode }> = {
  "no-entries": {
    title: "Sin registros",
    subtitle: "Tu primer check-in empieza el observatorio",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <circle cx={40} cy={36} r={22} stroke="#44403c" strokeWidth={1.5} strokeDasharray="4 4" fill="none" />
        <path
          d="M 36 26 C 28 28, 24 34, 26 40 C 28 46, 34 48, 40 48"
          stroke="#D4A03A"
          strokeWidth={2}
          strokeLinecap="round"
          fill="none"
          opacity={0.5}
        />
        <line x1={40} y1={32} x2={40} y2={42} stroke="#78716c" strokeWidth={1.5} strokeLinecap="round" />
        <line x1={35} y1={37} x2={45} y2={37} stroke="#78716c" strokeWidth={1.5} strokeLinecap="round" />
      </svg>
    ),
  },
  "no-data": {
    title: "Sin datos en este período",
    subtitle: "Ajusta el rango de fechas o registra nuevos días",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <line x1={12} y1={40} x2={68} y2={40} stroke="#44403c" strokeWidth={1.5} strokeLinecap="round" />
        <circle cx={28} cy={30} r={2.5} fill="#44403c" />
        <circle cx={40} cy={30} r={2.5} fill="#D4A03A" opacity={0.4} />
        <circle cx={52} cy={30} r={2.5} fill="#44403c" />
      </svg>
    ),
  },
  "insufficient-data": {
    title: "Insuficientes datos",
    subtitle: "Se necesitan ≥14 días para detectar correlaciones",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <circle cx={22} cy={44} r={2} fill="#44403c" />
        <circle cx={35} cy={28} r={2} fill="#44403c" />
        <circle cx={48} cy={38} r={2} fill="#D4A03A" opacity={0.4} />
        <circle cx={58} cy={32} r={2} fill="#44403c" />
        <line x1={18} y1={46} x2={62} y2={28} stroke="#44403c" strokeWidth={1} strokeDasharray="3 3" opacity={0.5} />
      </svg>
    ),
  },
};

export function EmptyState({ variant }: EmptyStateProps) {
  const { title, subtitle, illustration } = variants[variant];
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 bg-bg-secondary border border-bg-tertiary rounded-xl">
      <div className="mb-4">{illustration}</div>
      <p className="font-display text-body text-text-primary mb-1">{title}</p>
      <p className="font-body text-small text-text-muted text-center max-w-[240px]">{subtitle}</p>
    </div>
  );
}
