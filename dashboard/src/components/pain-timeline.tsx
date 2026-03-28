"use client";

import { useMemo } from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import type { DailyEntry } from "@/lib/api";

const LOCATION_COLORS: Record<string, string> = {
  lower_back: "#C4512A",
  left_knee: "#D4A03A",
  knee: "#D4A03A",
  shoulder: "#A8B86A",
  neck: "#A8B86A",
};

const DEFAULT_COLOR = "#7B9FBF";

function getLocationColor(location: string): string {
  const normalized = location.toLowerCase();
  for (const [key, color] of Object.entries(LOCATION_COLORS)) {
    if (normalized.includes(key)) return color;
  }
  return DEFAULT_COLOR;
}

interface TimelineDataPoint {
  date: string;
  dateLabel: string;
  pressure_hpa: number | null;
  sleep_hours: number | null;
  conditions: string | null;
  [key: string]: string | number | null;
}

function CustomTooltip({ active, payload }: {
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number | null; stroke: string; payload: TimelineDataPoint }>;
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const data = payload[0]?.payload;
  if (!data) return null;

  return (
    <div className="bg-bg-surface border border-bg-tertiary rounded-card p-3 shadow-lg min-w-[180px]">
      <p className="font-body text-small text-text-secondary mb-2">
        {format(parseISO(data.date), "EEEE d MMM", { locale: es })}
      </p>
      {payload
        .filter((p) => p.value !== null && p.value !== undefined)
        .map((p) => (
          <div
            key={p.dataKey}
            className="flex justify-between items-center gap-4 mb-1"
          >
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: p.stroke }}
              />
              <span className="font-body text-small text-text-primary capitalize">
                {p.dataKey.replace(/_/g, " ")}
              </span>
            </div>
            <span className="font-display text-small tabular-nums text-text-primary">
              {p.value}/10
            </span>
          </div>
        ))}
      {data.sleep_hours != null && (
        <div className="mt-2 pt-2 border-t border-bg-tertiary flex justify-between">
          <span className="text-small text-text-muted">Sueño</span>
          <span className="text-small text-text-secondary">
            {data.sleep_hours}h
          </span>
        </div>
      )}
      {data.conditions != null && (
        <div className="flex justify-between">
          <span className="text-small text-text-muted">Clima</span>
          <span className="text-small text-text-secondary">
            {data.conditions}
          </span>
        </div>
      )}
      {data.pressure_hpa != null && (
        <div className="flex justify-between">
          <span className="text-small text-text-muted">Presión</span>
          <span className="text-small text-text-secondary">
            {data.pressure_hpa} hPa
          </span>
        </div>
      )}
    </div>
  );
}

interface PainTimelineProps {
  entries: DailyEntry[];
}

export function PainTimeline({ entries }: PainTimelineProps) {
  const { chartData, locations } = useMemo(() => {
    if (!entries.length) return { chartData: [], locations: new Set<string>() };

    const locs = new Set<string>();
    const sorted = [...entries].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    );

    const data: TimelineDataPoint[] = sorted.map((entry) => {
      const point: TimelineDataPoint = {
        date: entry.date,
        dateLabel: format(parseISO(entry.date), "EEE", { locale: es }),
        pressure_hpa: entry.weather_records[0]?.pressure_hpa ?? null,
        sleep_hours: entry.apple_health_records[0]?.sleep_hours ?? null,
        conditions: entry.weather_records[0]?.conditions ?? null,
      };

      for (const pr of entry.pain_records) {
        locs.add(pr.location);
        point[pr.location] = pr.intensity;
      }

      return point;
    });

    return { chartData: data, locations: locs };
  }, [entries]);

  if (chartData.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="text-text-muted font-body text-body">
          Sin datos de dolor todavía
        </span>
      </div>
    );
  }

  const locationArray = Array.from(locations);

  // Compute atmospheric gradient stops based on pressure data
  const pressureValues = chartData
    .map((d) => d.pressure_hpa)
    .filter((p): p is number => p !== null);
  const minPressure = pressureValues.length
    ? Math.min(...pressureValues)
    : 1010;
  const maxPressure = pressureValues.length
    ? Math.max(...pressureValues)
    : 1020;

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart
        data={chartData}
        margin={{ top: 8, right: 8, bottom: 0, left: -16 }}
      >
        <defs>
          <linearGradient id="atmosphericBg" x1="0" y1="0" x2="1" y2="0">
            {chartData.map((point, i) => {
              const pressure = point.pressure_hpa ?? 1013;
              const range = maxPressure - minPressure || 10;
              const normalized = (pressure - minPressure) / range;
              // Low pressure -> amber (#2A2018), High -> blue-gray (#2A3040)
              const r = Math.round(42 + 0 * normalized);
              const g = Math.round(32 + 16 * normalized);
              const b = Math.round(24 + 40 * normalized);
              const offset =
                chartData.length > 1 ? i / (chartData.length - 1) : 0;
              return (
                <stop
                  key={i}
                  offset={`${offset * 100}%`}
                  stopColor={`rgb(${r}, ${g}, ${b})`}
                  stopOpacity={0.6}
                />
              );
            })}
          </linearGradient>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="url(#atmosphericBg)"
        />
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#44403C"
          strokeOpacity={0.3}
          vertical={false}
        />
        <XAxis
          dataKey="dateLabel"
          tick={{
            fill: "#78716C",
            fontSize: 11,
            fontFamily: "Satoshi, system-ui, sans-serif",
          }}
          axisLine={{ stroke: "#44403C" }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 10]}
          tick={{
            fill: "#78716C",
            fontSize: 11,
            fontFamily: "Satoshi, system-ui, sans-serif",
          }}
          axisLine={false}
          tickLine={false}
          width={30}
        />
        <Tooltip
          content={<CustomTooltip />}
          cursor={{ stroke: "#78716C", strokeDasharray: "3 3" }}
        />
        {locationArray.map((loc) => (
          <Line
            key={loc}
            type="natural"
            dataKey={loc}
            stroke={getLocationColor(loc)}
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              stroke: getLocationColor(loc),
              strokeWidth: 2,
              fill: "#1C1917",
            }}
            connectNulls
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
