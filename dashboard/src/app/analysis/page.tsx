"use client";

import { NavBar } from "@/components/nav-bar";
import { CorrelationMatrix } from "@/components/correlation-matrix";
import { LagExplorer } from "@/components/lag-explorer";
import { WeatherOverlay } from "@/components/weather-overlay";
import { PeriodComparison } from "@/components/period-comparison";

export default function AnalysisPage() {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-display text-h1 font-semibold text-text-primary">
            Analysis
          </h1>
          <p className="text-text-secondary mt-2 font-body text-body">
            Explore correlations and patterns in your pain data
          </p>
        </div>

        {/* Correlation Matrix — full width */}
        <section className="mb-8">
          <h2 className="font-display text-h2 text-text-primary mb-4">
            Correlation Rankings
          </h2>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
            <CorrelationMatrix />
          </div>
        </section>

        {/* Lag Explorer + Weather Overlay — 2 cols on desktop */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div>
            <h2 className="font-display text-h2 text-text-primary mb-4">
              Lag Explorer
            </h2>
            <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-80">
              <LagExplorer />
            </div>
          </div>
          <div>
            <h2 className="font-display text-h2 text-text-primary mb-4">
              Weather Overlay
            </h2>
            <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-80">
              <WeatherOverlay />
            </div>
          </div>
        </section>

        {/* Period Comparison — full width */}
        <section className="mb-8">
          <h2 className="font-display text-h2 text-text-primary mb-4">
            Period Comparison
          </h2>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
            <PeriodComparison />
          </div>
        </section>
      </main>
    </div>
  );
}
