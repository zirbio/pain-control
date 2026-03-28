"use client";

import { useState } from "react";
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
import { accentColors } from "@/lib/design-tokens";

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

function formatLabel(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

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
        Lag {d.lag > 0 ? `+${d.lag}` : d.lag} days
      </p>
      <p className="font-display text-body tabular-nums text-text-primary">
        r = {d.coefficient !== null ? d.coefficient.toFixed(3) : "N/A"}
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

export function LagExplorer() {
  const [variable, setVariable] = useState<string>(VARIABLES[0]);

  const { data: lagData, isLoading, error } = useLagCorrelation(TARGET, variable);

  return (
    <div className="flex flex-col h-full">
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <label className="font-body text-small text-text-muted">
          Target:
          <span className="ml-1 text-text-secondary">Pain (max)</span>
        </label>
        <label className="font-body text-small text-text-muted">
          vs
          <select
            value={variable}
            onChange={(e) => setVariable(e.target.value)}
            className="ml-2 bg-bg-tertiary text-text-primary font-body text-small rounded-md px-2 py-1 border border-bg-tertiary outline-none focus:border-accent-info"
          >
            {VARIABLES.map((v) => (
              <option key={v} value={v}>
                {formatLabel(v)}
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
          <div className="h-full flex items-center justify-center">
            <span className="font-body text-body text-text-muted">
              Error loading lag data
            </span>
          </div>
        )}

        {lagData && lagData.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={lagData}
              margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#44403C"
                strokeOpacity={0.3}
                vertical={false}
              />
              <XAxis
                dataKey="lag"
                tick={{
                  fill: "#78716C",
                  fontSize: 11,
                  fontFamily: "Satoshi, system-ui, sans-serif",
                }}
                axisLine={{ stroke: "#44403C" }}
                tickLine={false}
                tickFormatter={(v: number) => (v > 0 ? `+${v}` : String(v))}
              />
              <YAxis
                domain={[-1, 1]}
                tick={{
                  fill: "#78716C",
                  fontSize: 11,
                  fontFamily: "Satoshi, system-ui, sans-serif",
                }}
                axisLine={false}
                tickLine={false}
                width={35}
              />
              <Tooltip
                content={<LagTooltip />}
                cursor={{ fill: "rgba(68, 64, 60, 0.2)" }}
              />
              <Bar dataKey="coefficient" radius={[4, 4, 0, 0]}>
                {lagData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.significant
                        ? accentColors.highlight
                        : "#78716C"
                    }
                    fillOpacity={entry.significant ? 1 : 0.5}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}

        {lagData && lagData.length === 0 && (
          <div className="h-full flex items-center justify-center">
            <span className="font-body text-body text-text-muted">
              No lag data available
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
