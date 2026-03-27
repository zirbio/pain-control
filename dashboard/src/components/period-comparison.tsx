"use client";

import { useState } from "react";
import { format, subDays } from "date-fns";
import { useReport } from "@/hooks/use-analysis";
import { accentColors } from "@/lib/design-tokens";
import type { ReportResult } from "@/lib/api";

function StatRow({
  label,
  valueA,
  valueB,
  unit,
  higherIsBetter = false,
}: {
  label: string;
  valueA: string | null;
  valueB: string | null;
  unit?: string;
  higherIsBetter?: boolean;
}) {
  const numA = valueA !== null ? parseFloat(valueA) : null;
  const numB = valueB !== null ? parseFloat(valueB) : null;

  let diffColor: string | undefined;
  if (numA !== null && numB !== null && numA !== numB) {
    const better = higherIsBetter ? numB > numA : numB < numA;
    diffColor = better ? accentColors.positive : accentColors.negative;
  }

  return (
    <div className="grid grid-cols-3 gap-4 py-3 border-b border-bg-tertiary/50">
      <span className="font-body text-small text-text-muted">{label}</span>
      <span className="font-display text-body tabular-nums text-text-primary text-center">
        {valueA ?? "—"}
        {unit && valueA !== null && (
          <span className="text-text-muted text-small ml-0.5">{unit}</span>
        )}
      </span>
      <span
        className="font-display text-body tabular-nums text-center"
        style={{ color: diffColor ?? "#F5F5F4" }}
      >
        {valueB ?? "—"}
        {unit && valueB !== null && (
          <span className="text-small ml-0.5" style={{ color: "#78716C" }}>
            {unit}
          </span>
        )}
      </span>
    </div>
  );
}

function formatStat(value: number | undefined | null): string | null {
  if (value === undefined || value === null) return null;
  return value.toFixed(1);
}

function PeriodSummary({
  label,
  report,
  isLoading,
}: {
  label: string;
  report: ReportResult | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex-1">
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {label}
        </span>
        <div className="skeleton h-6 mt-2 w-24" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex-1">
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {label}
        </span>
        <p className="font-body text-small text-text-muted mt-1">Select dates</p>
      </div>
    );
  }

  return (
    <div className="flex-1">
      <span className="font-body text-label uppercase text-text-muted tracking-widest">
        {label}
      </span>
      <p className="font-body text-small text-text-secondary mt-1">
        {report.period.start} to {report.period.end} ({report.period.days} days)
      </p>
    </div>
  );
}

export function PeriodComparison() {
  const today = format(new Date(), "yyyy-MM-dd");
  const fourteenAgo = format(subDays(new Date(), 14), "yyyy-MM-dd");
  const twentyEightAgo = format(subDays(new Date(), 28), "yyyy-MM-dd");

  const [startA, setStartA] = useState(twentyEightAgo);
  const [endA, setEndA] = useState(fourteenAgo);
  const [startB, setStartB] = useState(fourteenAgo);
  const [endB, setEndB] = useState(today);

  const {
    data: reportA,
    isLoading: loadingA,
  } = useReport(startA, endA);
  const {
    data: reportB,
    isLoading: loadingB,
  } = useReport(startB, endB);

  const isLoading = loadingA || loadingB;

  return (
    <div>
      {/* Date pickers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <span className="font-body text-label uppercase text-text-muted tracking-widest block mb-2">
            Period A
          </span>
          <div className="flex gap-2">
            <input
              type="date"
              value={startA}
              onChange={(e) => setStartA(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-small rounded-md px-3 py-1.5 border border-bg-tertiary outline-none focus:border-accent-info flex-1"
            />
            <input
              type="date"
              value={endA}
              onChange={(e) => setEndA(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-small rounded-md px-3 py-1.5 border border-bg-tertiary outline-none focus:border-accent-info flex-1"
            />
          </div>
        </div>
        <div>
          <span className="font-body text-label uppercase text-text-muted tracking-widest block mb-2">
            Period B
          </span>
          <div className="flex gap-2">
            <input
              type="date"
              value={startB}
              onChange={(e) => setStartB(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-small rounded-md px-3 py-1.5 border border-bg-tertiary outline-none focus:border-accent-info flex-1"
            />
            <input
              type="date"
              value={endB}
              onChange={(e) => setEndB(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-small rounded-md px-3 py-1.5 border border-bg-tertiary outline-none focus:border-accent-info flex-1"
            />
          </div>
        </div>
      </div>

      {/* Period headers */}
      <div className="flex gap-4 mb-4">
        <PeriodSummary label="Period A" report={reportA} isLoading={loadingA} />
        <PeriodSummary label="Period B" report={reportB} isLoading={loadingB} />
      </div>

      {/* Comparison table */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-10" />
          ))}
        </div>
      ) : (
        <div>
          {/* Header */}
          <div className="grid grid-cols-3 gap-4 pb-2 border-b border-bg-tertiary">
            <span className="font-body text-label uppercase text-text-muted tracking-widest">
              Metric
            </span>
            <span className="font-body text-label uppercase text-text-muted tracking-widest text-center">
              Period A
            </span>
            <span className="font-body text-label uppercase text-text-muted tracking-widest text-center">
              Period B
            </span>
          </div>

          <StatRow
            label="Pain (mean)"
            valueA={formatStat(reportA?.pain?.mean)}
            valueB={formatStat(reportB?.pain?.mean)}
          />
          <StatRow
            label="Sleep (mean)"
            valueA={formatStat(reportA?.sleep?.mean)}
            valueB={formatStat(reportB?.sleep?.mean)}
            unit="h"
            higherIsBetter
          />
          <StatRow
            label="Active days"
            valueA={
              reportA?.activity
                ? `${reportA.activity.active_days}/${reportA.activity.total_days}`
                : null
            }
            valueB={
              reportB?.activity
                ? `${reportB.activity.active_days}/${reportB.activity.total_days}`
                : null
            }
          />
          <StatRow
            label="Med effectiveness"
            valueA={formatStat(reportA?.medication?.mean_effectiveness)}
            valueB={formatStat(reportB?.medication?.mean_effectiveness)}
            unit="/10"
            higherIsBetter
          />
        </div>
      )}
    </div>
  );
}
