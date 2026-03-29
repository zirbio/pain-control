"use client";

import { NavBar } from "@/components/nav-bar";
import { EmptyState } from "@/components/empty-state";
import { CorrelationMatrix } from "@/components/correlation-matrix";
import { LagExplorer } from "@/components/lag-explorer";
import { WeatherOverlay } from "@/components/weather-overlay";
import { PeriodComparison } from "@/components/period-comparison";
import { useEntries } from "@/hooks/use-entries";

export default function AnalysisPage() {
  const { data: entries } = useEntries({ limit: 14 });
  const hasEnoughData = (entries?.length ?? 0) >= 14;

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-display text-h1 font-semibold text-text-primary">
            An&aacute;lisis
          </h1>
          <p className="text-text-secondary mt-2 font-body text-body">
            Correlaciones y patrones en tus datos de dolor
          </p>
        </div>

        {!hasEnoughData && entries !== undefined && (
          <div className="mb-8">
            <EmptyState variant="insufficient-data" />
          </div>
        )}

        {/* Correlation Matrix — full width */}
        <section className="mb-8">
          <h2 className="font-display text-h2 text-text-primary mb-4">
            Ranking de correlaciones
          </h2>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
            <CorrelationMatrix />
          </div>
        </section>

        {/* Lag Explorer + Weather Overlay — 2 cols on desktop */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div>
            <h2 className="font-display text-h2 text-text-primary mb-4">
              Explorador de desfase
            </h2>
            <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-64 sm:h-72 md:h-80">
              <LagExplorer />
            </div>
          </div>
          <div>
            <h2 className="font-display text-h2 text-text-primary mb-4">
              Clima y dolor
            </h2>
            <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-64 sm:h-72 md:h-80">
              <WeatherOverlay />
            </div>
          </div>
        </section>

        {/* Period Comparison — full width */}
        <section className="mb-8">
          <h2 className="font-display text-h2 text-text-primary mb-4">
            Comparaci&oacute;n de per&iacute;odos
          </h2>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
            <PeriodComparison />
          </div>
        </section>
      </main>
    </div>
  );
}
