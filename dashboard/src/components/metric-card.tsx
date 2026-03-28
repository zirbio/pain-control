"use client";

import { useEffect, useRef, useState } from "react";
import { getPainColor } from "@/lib/design-tokens";

interface MetricCardProps {
  label: string;
  value: number | string | null;
  trend?: { direction: "up" | "down" | "stable"; delta?: string };
  colorScale?: "pain";
  sparklineData?: number[];
  unit?: string;
}

function AnimatedNumber({ value }: { value: number }) {
  const [displayed, setDisplayed] = useState(0);
  const ref = useRef<number>(0);

  useEffect(() => {
    const start = ref.current;
    const end = value;
    const duration = 400;
    const startTime = performance.now();

    function animate(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * eased;
      setDisplayed(current);
      ref.current = current;
      if (progress < 1) requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }, [value]);

  return <>{displayed.toFixed(1)}</>;
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  if (data.length < 2) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const h = 24;
  const w = 100;
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-6 mt-2" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

const trendArrows: Record<string, string> = { up: "\u2197", down: "\u2198", stable: "\u2192" };
const trendColors: Record<string, string> = { down: "#6B8A7A", up: "#C4512A", stable: "#78716C" };

export function MetricCard({
  label,
  value,
  trend,
  colorScale,
  sparklineData,
  unit,
}: MetricCardProps) {
  const numericValue = typeof value === "number" ? value : null;
  const displayColor =
    colorScale === "pain" && numericValue !== null
      ? getPainColor(numericValue)
      : "#F5F5F4";

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(26,20,18,0.5)]">
      <div className="flex items-center justify-between mb-3">
        <span className="font-body text-label uppercase text-text-muted tracking-widest">
          {label}
        </span>
        {trend && (
          <span
            className="text-small"
            style={{ color: trendColors[trend.direction] }}
          >
            {trendArrows[trend.direction]} {trend.delta}
          </span>
        )}
      </div>
      <div
        className="font-display text-metric tabular-nums"
        style={{ color: displayColor }}
      >
        {numericValue !== null ? (
          <AnimatedNumber value={numericValue} />
        ) : (
          <span className="text-text-muted">{value ?? "—"}</span>
        )}
        {unit && <span className="text-h2 text-text-secondary ml-1">{unit}</span>}
      </div>
      {sparklineData && sparklineData.length > 1 && (
        <MiniSparkline data={sparklineData} color={displayColor} />
      )}
    </div>
  );
}
