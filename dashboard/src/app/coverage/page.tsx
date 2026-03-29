"use client";

import { useMemo, useState } from "react";
import { format, subDays } from "date-fns";
import { NavBar } from "@/components/nav-bar";
import { CoverageHeatmap, MANUAL_CATEGORIES } from "@/components/coverage-heatmap";
import { useEntries } from "@/hooks/use-entries";
import { accentColors } from "@/lib/design-tokens";
import type { DailyEntry } from "@/lib/api";
import { EmptyState } from "@/components/empty-state";

const RANGE_OPTIONS = [7, 14, 30] as const;

export default function CoveragePage() {
  const [days, setDays] = useState<number>(14);
  const [offset, setOffset] = useState(0);

  const { startDate, endDate } = useMemo(() => {
    const end = subDays(new Date(), 1 + offset * days);
    const start = subDays(end, days - 1);
    return { startDate: start, endDate: end };
  }, [days, offset]);

  const { data: entries = [], isLoading } = useEntries({
    start_date: format(startDate, "yyyy-MM-dd"),
    end_date: format(endDate, "yyyy-MM-dd"),
    limit: days,
  });

  const { completeDays, totalDays, pct } = useMemo(() => {
    const total = days;
    const entryMap = new Map(entries.map((e) => [e.date, e]));

    function isComplete(entry: DailyEntry): boolean {
      return MANUAL_CATEGORIES.every((cat) => cat.check(entry));
    }

    let complete = 0;
    for (let i = 0; i < days; i++) {
      const date = subDays(new Date(), 1 + offset * days + (days - 1 - i));
      const dateStr = format(date, "yyyy-MM-dd");
      const entry = entryMap.get(dateStr);
      if (entry && isComplete(entry)) {
        complete++;
      }
    }

    return {
      completeDays: complete,
      totalDays: total,
      pct: total > 0 ? Math.round((complete / total) * 100) : 0,
    };
  }, [entries, days, offset]);

  const barColor =
    pct > 70 ? accentColors.positive :
    pct >= 40 ? accentColors.warning :
    accentColors.negative;

  return (
    <>
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8 pb-20 md:pb-8">
        <div className="flex flex-col gap-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h1 className="font-display text-h1 text-text-primary">
              Cobertura de datos
            </h1>

            <div className="flex items-center gap-2">
              {/* Arrow nav */}
              <button
                onClick={() => setOffset((o) => o + 1)}
                className="font-body text-body text-text-muted hover:text-text-secondary px-2 py-1 min-h-[44px] sm:min-h-0 rounded transition-colors focus-visible:ring-2 focus-visible:ring-accent-info"
                aria-label="Periodo anterior"
              >
                &larr;
              </button>

              {/* Range selector */}
              {RANGE_OPTIONS.map((r) => (
                <button
                  key={r}
                  onClick={() => {
                    setDays(r);
                    setOffset(0);
                  }}
                  className={`font-body text-small px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded transition-colors focus-visible:ring-2 focus-visible:ring-accent-info ${
                    days === r
                      ? "bg-bg-tertiary text-text-primary"
                      : "text-text-muted hover:text-text-secondary"
                  }`}
                >
                  {r}d
                </button>
              ))}

              <button
                onClick={() => setOffset((o) => Math.max(0, o - 1))}
                disabled={offset === 0}
                className="font-body text-body text-text-muted hover:text-text-secondary px-2 py-1 min-h-[44px] sm:min-h-0 rounded transition-colors focus-visible:ring-2 focus-visible:ring-accent-info disabled:opacity-30 disabled:cursor-not-allowed"
                aria-label="Periodo siguiente"
              >
                &rarr;
              </button>
            </div>
          </div>

          {/* Date range label */}
          <p className="font-body text-small text-text-muted -mt-4">
            {format(startDate, "d MMM")} &mdash; {format(endDate, "d MMM yyyy")}
          </p>

          {!isLoading && !entries.length ? (
            <EmptyState variant="no-data" />
          ) : (
            <>
              {/* Summary bar */}
              <div className="bg-bg-secondary rounded-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-body text-body text-text-secondary">
                    Registro completo (6 categorías manuales)
                  </span>
                  <span
                    className="font-display text-body tabular-nums"
                    style={{ color: barColor }}
                  >
                    {pct}% &mdash; {completeDays} de {totalDays} días
                  </span>
                </div>
                <div className="h-2 bg-bg-tertiary rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: barColor }}
                  />
                </div>
              </div>

              {/* Heatmap */}
              <div className="bg-bg-secondary rounded-card p-4">
                <CoverageHeatmap
                  entries={entries}
                  startDate={startDate}
                  endDate={endDate}
                  isLoading={isLoading}
                />
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
}
