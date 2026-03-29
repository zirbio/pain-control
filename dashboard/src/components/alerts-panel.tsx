"use client";

import { memo } from "react";
import Link from "next/link";
import { AlertCard } from "./alert-card";
import { useRankings } from "@/hooks/use-analysis";
import { formatVariable } from "@/lib/utils";

export const AlertsPanel = memo(function AlertsPanel() {
  const { data: rankings, isLoading } = useRankings();

  if (isLoading) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6">
        <div className="skeleton h-24" />
      </div>
    );
  }

  const significantCorrelations = rankings?.filter((r) => r.significant).slice(0, 3) ?? [];

  if (significantCorrelations.length === 0) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6 flex flex-col items-center justify-center h-40">
        <span className="text-text-muted font-body text-body">
          Sin alertas — necesitas más datos para detectar patrones
        </span>
        <Link
          href="/history"
          className="font-body text-small text-accent-info hover:text-text-primary transition-colors mt-2 inline-block"
        >
          Registra más datos →
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4">
      <h2 className="font-body text-label uppercase text-text-muted tracking-widest mb-4">
        ◆ Alertas
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {significantCorrelations.map((corr) => {
          const label = formatVariable(corr.variable);
          const direction = corr.coefficient > 0 ? "+" : "";
          const effect = corr.coefficient > 0 ? "se asocia con más dolor" : "se asocia con menos dolor";

          return (
            <AlertCard
              key={corr.variable}
              title="Correlación detectada"
              body={`${label} ${effect} (${direction}${corr.coefficient.toFixed(2)})`}
              metadata={`p=${corr.p_value.toFixed(3)} · n=${corr.n} días`}
            />
          );
        })}
      </div>
    </div>
  );
});
