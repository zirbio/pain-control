"use client";

import { memo, useMemo } from "react";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import { useEntries } from "@/hooks/use-entries";
import { accentColors, chartTickStyle, chartGridProps } from "@/lib/design-tokens";

interface ChartDataPoint {
  date: string;
  dateLabel: string;
  pain_max: number | null;
  pressure_hpa: number | null;
}

interface OverlayTooltipProps {
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number | null;
    stroke?: string;
    color?: string;
  }>;
}

function OverlayTooltip({ active, payload }: OverlayTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const pain = payload.find((p) => p.dataKey === "pain_max");
  const pressure = payload.find((p) => p.dataKey === "pressure_hpa");

  return (
    <div className="bg-bg-surface border border-bg-tertiary rounded-card p-3 shadow-lg min-w-[140px] max-w-[90vw]">
      {pain?.value != null && (
        <div className="flex justify-between gap-4 mb-1">
          <span className="font-body text-small text-text-muted">Dolor</span>
          <span
            className="font-display text-small tabular-nums"
            style={{ color: accentColors.negative }}
          >
            {pain.value}/10
          </span>
        </div>
      )}
      {pressure?.value != null && (
        <div className="flex justify-between gap-4">
          <span className="font-body text-small text-text-muted">Presión</span>
          <span
            className="font-display text-small tabular-nums"
            style={{ color: accentColors.info }}
          >
            {pressure.value} hPa
          </span>
        </div>
      )}
    </div>
  );
}

export const WeatherOverlay = memo(function WeatherOverlay() {
  const { data: entries, isLoading, error, refetch } = useEntries({ limit: 30 });

  const chartData = useMemo(() => {
    if (!entries || entries.length === 0) return [];

    const sorted = [...entries].sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    );

    return sorted.map((entry): ChartDataPoint => {
      const maxPain =
        entry.pain_records.length > 0
          ? Math.max(...entry.pain_records.map((p) => p.intensity))
          : null;

      return {
        date: entry.date,
        dateLabel: format(parseISO(entry.date), "d MMM", { locale: es }),
        pain_max: maxPain,
        pressure_hpa: entry.weather_records[0]?.pressure_hpa ?? null,
      };
    });
  }, [entries]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="skeleton w-full h-48" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3">
        <span className="text-text-muted font-body text-body">
          No se pudieron cargar los datos meteorológicos
        </span>
        <button
          onClick={() => refetch()}
          className="font-body text-small text-accent-info hover:text-text-primary transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <span className="font-body text-body text-text-muted">
          Aún no hay datos meteorológicos
        </span>
      </div>
    );
  }

  const pressureValues = chartData
    .map((d) => d.pressure_hpa)
    .filter((p): p is number => p !== null);
  const pressureMin = pressureValues.length > 0 ? Math.min(...pressureValues) - 5 : 995;
  const pressureMax = pressureValues.length > 0 ? Math.max(...pressureValues) + 5 : 1035;

  return (
    <div role="region" aria-label="Correlación clima y dolor" className="h-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={chartData}
          margin={{ top: 8, right: 8, bottom: 0, left: -8 }}
        >
          <defs>
          <linearGradient id="pressureGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accentColors.info} stopOpacity={0.3} />
            <stop offset="100%" stopColor={accentColors.info} stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid {...chartGridProps} />
        <XAxis
          dataKey="dateLabel"
          tick={chartTickStyle}
          axisLine={{ stroke: chartGridProps.stroke }}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          yAxisId="pain"
          orientation="left"
          domain={[0, 10]}
          tick={chartTickStyle}
          axisLine={false}
          tickLine={false}
          width={30}
          label={{
            value: "Dolor",
            angle: -90,
            position: "insideLeft",
            style: { ...chartTickStyle, fontSize: 10 },
          }}
        />
        <YAxis
          yAxisId="pressure"
          orientation="right"
          domain={[pressureMin, pressureMax]}
          tick={chartTickStyle}
          axisLine={false}
          tickLine={false}
          width={45}
          label={{
            value: "hPa",
            angle: 90,
            position: "insideRight",
            style: { ...chartTickStyle, fontSize: 10 },
          }}
        />
        <Tooltip
          content={<OverlayTooltip />}
          cursor={{ stroke: chartTickStyle.fill, strokeDasharray: "3 3" }}
        />
        <Area
          yAxisId="pressure"
          type="monotone"
          dataKey="pressure_hpa"
          fill="url(#pressureGradient)"
          stroke={accentColors.info}
          strokeWidth={1.5}
          strokeOpacity={0.6}
          connectNulls
        />
        <Line
          yAxisId="pain"
          type="monotone"
          dataKey="pain_max"
          stroke={accentColors.negative}
          strokeWidth={2}
          dot={false}
          activeDot={{
            r: 4,
            stroke: accentColors.negative,
            strokeWidth: 2,
            fill: "var(--color-bg-primary)",
          }}
          connectNulls
        />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
});
