"use client";

import { format, subDays } from "date-fns";
import { es } from "date-fns/locale";
import { MetricCard } from "@/components/metric-card";
import { PainTimeline } from "@/components/pain-timeline";
import { WeeklyHeatmap } from "@/components/weekly-heatmap";
import { NavBar } from "@/components/nav-bar";
import { useEntries } from "@/hooks/use-entries";

export default function DashboardPage() {
  const today = new Date();
  const startDate = format(subDays(today, 7), "yyyy-MM-dd");
  const endDate = format(today, "yyyy-MM-dd");
  const { data: entries, isLoading } = useEntries({
    start_date: startDate,
    end_date: endDate,
  });

  const heatmapStart = format(subDays(today, 35), "yyyy-MM-dd");
  const { data: heatmapEntries } = useEntries({
    start_date: heatmapStart,
    end_date: endDate,
  });

  const painValues = entries
    ?.map((e) => {
      const max = Math.max(...e.pain_records.map((p) => p.intensity), 0);
      return max;
    })
    .reverse();

  const avgPain =
    painValues && painValues.length > 0
      ? painValues.reduce((a, b) => a + b, 0) / painValues.length
      : null;

  const sleepValues = entries
    ?.map((e) => e.apple_health_records[0]?.sleep_hours ?? null)
    .filter((v): v is number => v !== null)
    .reverse();

  const avgSleep =
    sleepValues && sleepValues.length > 0
      ? sleepValues.reduce((a, b) => a + b, 0) / sleepValues.length
      : null;

  const activeDays =
    entries?.filter((e) => e.activity_records.length > 0).length ?? 0;
  const totalDays = entries?.length ?? 0;

  const medEffValues = entries
    ?.flatMap((e) => e.medication_records)
    .map((m) => m.effectiveness)
    .filter((v): v is number => v !== null);

  const avgMedEff =
    medEffValues && medEffValues.length > 0
      ? medEffValues.reduce((a, b) => a + b, 0) / medEffValues.length
      : null;

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-display text-h1 font-semibold text-text-primary">
            Pain Control
          </h1>
          <p className="font-body text-body text-text-secondary mt-1">
            {format(today, "EEEE, d 'de' MMMM", { locale: es })}
          </p>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-32" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <MetricCard
              label="Dolor · 7d"
              value={avgPain}
              colorScale="pain"
              sparklineData={painValues}
            />
            <MetricCard
              label="Sueño · 7d"
              value={avgSleep}
              unit="h"
              sparklineData={sleepValues}
            />
            <MetricCard
              label="Activo"
              value={`${activeDays}/${totalDays}`}
              unit="días"
            />
            <MetricCard
              label="Captor"
              value={avgMedEff}
              unit="/10"
            />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="md:col-span-2 bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-80">
            <PainTimeline entries={entries ?? []} />
          </div>
          <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4 h-80">
            <WeeklyHeatmap entries={heatmapEntries ?? []} />
          </div>
        </div>

        <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6 flex items-center justify-center h-40">
          <span className="text-text-muted font-body text-body">
            Alerts Panel — coming in Phase 5
          </span>
        </div>
      </main>
    </div>
  );
}
