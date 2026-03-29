"use client";

import { memo, useState } from "react";
import { format, subDays } from "date-fns";
import { useReport } from "@/hooks/use-analysis";
import { accentColors, textColors } from "@/lib/design-tokens";
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
        style={{ color: diffColor ?? textColors.primary }}
      >
        {valueB ?? "—"}
        {unit && valueB !== null && (
          <span className="text-small ml-0.5" style={{ color: textColors.muted }}>
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

  if (!report || !report.period) {
    return (
      <div className="flex-1">
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {label}
        </span>
        <p className="font-body text-small text-text-muted mt-1">Sin datos</p>
      </div>
    );
  }

  return (
    <div className="flex-1">
      <span className="font-body text-label uppercase text-text-muted tracking-widest">
        {label}
      </span>
      <p className="font-body text-small text-text-secondary mt-1">
        {report.period.start} a {report.period.end} ({report.period.days} d&iacute;as)
      </p>
    </div>
  );
}

export const PeriodComparison = memo(function PeriodComparison() {
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
          <label htmlFor="period-a-start" className="font-body text-label uppercase text-text-muted tracking-widest block mb-2">
            Per&iacute;odo 1
          </label>
          <div className="flex gap-2">
            <input
              id="period-a-start"
              type="date"
              value={startA}
              onChange={(e) => setStartA(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-body sm:text-small rounded-md px-3 py-1.5 min-h-[44px] sm:min-h-0 border border-bg-tertiary focus:border-accent-info focus-visible:ring-2 focus-visible:ring-accent-info flex-1"
            />
            <input
              id="period-a-end"
              type="date"
              value={endA}
              onChange={(e) => setEndA(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-body sm:text-small rounded-md px-3 py-1.5 min-h-[44px] sm:min-h-0 border border-bg-tertiary focus:border-accent-info focus-visible:ring-2 focus-visible:ring-accent-info flex-1"
            />
          </div>
        </div>
        <div>
          <label htmlFor="period-b-start" className="font-body text-label uppercase text-text-muted tracking-widest block mb-2">
            Per&iacute;odo 2
          </label>
          <div className="flex gap-2">
            <input
              id="period-b-start"
              type="date"
              value={startB}
              onChange={(e) => setStartB(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-body sm:text-small rounded-md px-3 py-1.5 min-h-[44px] sm:min-h-0 border border-bg-tertiary focus:border-accent-info focus-visible:ring-2 focus-visible:ring-accent-info flex-1"
            />
            <input
              id="period-b-end"
              type="date"
              value={endB}
              onChange={(e) => setEndB(e.target.value)}
              className="bg-bg-tertiary text-text-primary font-body text-body sm:text-small rounded-md px-3 py-1.5 min-h-[44px] sm:min-h-0 border border-bg-tertiary focus:border-accent-info focus-visible:ring-2 focus-visible:ring-accent-info flex-1"
            />
          </div>
        </div>
      </div>

      {/* Period headers */}
      <div className="flex gap-4 mb-4">
        <PeriodSummary label="Per\u00edodo 1" report={reportA} isLoading={loadingA} />
        <PeriodSummary label="Per\u00edodo 2" report={reportB} isLoading={loadingB} />
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
              M&eacute;trica
            </span>
            <span className="font-body text-label uppercase text-text-muted tracking-widest text-center">
              Per&iacute;odo 1
            </span>
            <span className="font-body text-label uppercase text-text-muted tracking-widest text-center">
              Per&iacute;odo 2
            </span>
          </div>

          <StatRow
            label="Dolor (media)"
            valueA={formatStat(reportA?.pain?.mean)}
            valueB={formatStat(reportB?.pain?.mean)}
          />
          <StatRow
            label="Sue&ntilde;o (media)"
            valueA={formatStat(reportA?.sleep?.mean)}
            valueB={formatStat(reportB?.sleep?.mean)}
            unit="h"
            higherIsBetter
          />
          <StatRow
            label="D&iacute;as activos"
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
            label="Eficacia medicaci&oacute;n"
            valueA={formatStat(reportA?.medication?.mean_effectiveness)}
            valueB={formatStat(reportB?.medication?.mean_effectiveness)}
            unit="/10"
            higherIsBetter
          />
        </div>
      )}
    </div>
  );
});
