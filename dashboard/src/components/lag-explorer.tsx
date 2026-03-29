"use client";

import { memo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useLagCorrelation } from "@/hooks/use-analysis";
import { accentColors, chartTickStyle, chartGridProps, chartCursorOverlay } from "@/lib/design-tokens";
import { formatVariable } from "@/lib/utils";

const TARGET = "pain_max";

const VARIABLES = [
  "sleep_hours",
  "steps",
  "stress_level",
  "activity_minutes",
  "pressure_hpa",
  "pressure_change_hpa",
  "humidity_pct",
  "medication_effectiveness",
  "mood_score",
  "resting_hr",
  "hrv_ms",
  "alcohol",
  "caffeine_cups",
] as const;

interface LagTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: { lag: number; coefficient: number | null; significant?: boolean; p_value: number | null };
  }>;
}

function LagTooltip({ active, payload }: LagTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0]?.payload;
  if (!d) return null;

  return (
    <div className="bg-bg-surface border border-bg-tertiary rounded-card p-3 shadow-lg">
      <p className="font-body text-small text-text-secondary mb-1">
        Lag {d.lag > 0 ? `+${d.lag}` : d.lag} días
      </p>
      <p className="font-display text-body tabular-nums text-text-primary">
        r = {d.coefficient !== null ? d.coefficient.toFixed(3) : "N/D"}
      </p>
      {d.p_value !== null && (
        <p className="font-body text-small text-text-muted">
          p = {d.p_value < 0.001 ? "<0.001" : d.p_value.toFixed(3)}
          {d.significant && " *"}
        </p>
      )}
    </div>
  );
}

export const LagExplorer = memo(function LagExplorer() {
  const [variable, setVariable] = useState<string>(VARIABLES[0]);

  const { data: lagData, isLoading, error, refetch } = useLagCorrelation(TARGET, variable);

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <label className="font-body text-small text-text-muted">
          Objetivo:
          <span className="ml-1 text-text-secondary">Dolor (máx)</span>
        </label>
        <label htmlFor="lag-variable" className="font-body text-small text-text-muted">
          vs
          <select
            id="lag-variable"
            value={variable}
            onChange={(e) => setVariable(e.target.value)}
            className="ml-2 bg-bg-tertiary text-text-primary font-body text-small rounded-md px-2 py-2 sm:py-1 min-h-[44px] sm:min-h-0 border border-bg-tertiary outline-none focus-visible:ring-2 focus-visible:ring-accent-info"
          >
            {VARIABLES.map((v) => (
              <option key={v} value={v}>
                {formatVariable(v)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex-1 min-h-0">
        {isLoading && (
          <div className="h-full flex items-center justify-center">
            <div className="skeleton w-full h-48" />
          </div>
        )}

        {error && (
          <div className="h-full flex flex-col items-center justify-center gap-3">
            <span className="text-text-muted font-body text-body">
              No se pudieron cargar los datos de desfase
            </span>
            <button
              onClick={() => refetch()}
              className="font-body text-small text-accent-info hover:text-text-primary transition-colors"
            >
              Reintentar
            </button>
          </div>
        )}

        {lagData && lagData.length > 0 && (
          <div role="region" aria-label="Explorador de correlación con desfase temporal" className="h-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={lagData}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid {...chartGridProps} />
              <XAxis
                dataKey="lag"
                tick={chartTickStyle}
                axisLine={{ stroke: chartGridProps.stroke }}
                tickLine={false}
                tickFormatter={(v: number) => (v > 0 ? `+${v}` : String(v))}
              />
              <YAxis
                domain={[-1, 1]}
                tick={chartTickStyle}
                axisLine={false}
                tickLine={false}
                width={35}
              />
              <Tooltip
                content={<LagTooltip />}
                cursor={{ fill: chartCursorOverlay }}
              />
              <Bar dataKey="coefficient" radius={[4, 4, 0, 0]}>
                {lagData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.significant
                        ? accentColors.highlight
                        : chartTickStyle.fill
                    }
                    fillOpacity={entry.significant ? 1 : 0.5}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          </div>
        )}

        {lagData && lagData.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <span className="text-text-muted font-body text-body">
              Necesitas más registros para analizar correlaciones con desfase
            </span>
          </div>
        )}
      </div>
    </div>
  );
});
