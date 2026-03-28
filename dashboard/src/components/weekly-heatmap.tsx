"use client";

import { useMemo, useState } from "react";
import {
  format,
  parseISO,
  startOfWeek,
  addDays,
  subWeeks,
  isAfter,
} from "date-fns";
import { es } from "date-fns/locale";
import { getPainColor } from "@/lib/design-tokens";
import type { DailyEntry } from "@/lib/api";

interface WeeklyHeatmapProps {
  entries: DailyEntry[];
  weeks?: number;
}

const DAY_LABELS = ["L", "M", "X", "J", "V", "S", "D"];

export function WeeklyHeatmap({ entries, weeks = 5 }: WeeklyHeatmapProps) {
  const [hoveredDay, setHoveredDay] = useState<{
    date: string;
    pain: number | null;
    x: number;
    y: number;
  } | null>(null);

  const grid = useMemo(() => {
    // Build a map of date string -> max pain intensity
    const map = new Map<string, number>();
    for (const entry of entries) {
      if (entry.pain_records.length > 0) {
        const maxPain = Math.max(
          ...entry.pain_records.map((p) => p.intensity),
        );
        map.set(entry.date, maxPain);
      }
    }

    // Build grid: 5 weeks, starting from Monday of the week that is (weeks-1) weeks ago
    const today = new Date();
    const currentWeekStart = startOfWeek(today, { weekStartsOn: 1 }); // Monday
    const gridStart = subWeeks(currentWeekStart, weeks - 1);

    const rows: Array<
      Array<{
        date: Date;
        dateStr: string;
        pain: number | null;
        future: boolean;
      }>
    > = [];
    for (let w = 0; w < weeks; w++) {
      const weekStart = addDays(gridStart, w * 7);
      const row = [];
      for (let d = 0; d < 7; d++) {
        const date = addDays(weekStart, d);
        const dateStr = format(date, "yyyy-MM-dd");
        const isFuture = isAfter(date, today);
        row.push({
          date,
          dateStr,
          pain: map.get(dateStr) ?? null,
          future: isFuture,
        });
      }
      rows.push(row);
    }

    return rows;
  }, [entries, weeks]);

  return (
    <div className="relative h-full flex flex-col">
      <h3 className="font-body text-label uppercase text-text-muted tracking-widest mb-3">
        Heatmap &middot; {weeks}s
      </h3>

      {/* Day labels */}
      <div className="grid grid-cols-7 gap-[3px] mb-1">
        {DAY_LABELS.map((d) => (
          <div
            key={d}
            className="text-center font-body text-small text-text-muted"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Grid */}
      <div className="flex-1 grid grid-rows-5 gap-[3px]">
        {grid.map((week, wi) => (
          <div key={wi} className="grid grid-cols-7 gap-[3px]">
            {week.map((day) => {
              if (day.future) {
                return (
                  <div
                    key={day.dateStr}
                    className="rounded-[4px] bg-bg-primary"
                  />
                );
              }

              const hasPain = day.pain !== null;
              return (
                <div
                  key={day.dateStr}
                  className={`rounded-[4px] cursor-pointer transition-transform duration-150 hover:scale-[1.15] ${
                    !hasPain
                      ? "border border-dashed border-bg-tertiary bg-bg-secondary"
                      : ""
                  }`}
                  style={
                    hasPain
                      ? { backgroundColor: getPainColor(day.pain!) }
                      : undefined
                  }
                  onMouseEnter={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    setHoveredDay({
                      date: day.dateStr,
                      pain: day.pain,
                      x: rect.left + rect.width / 2,
                      y: rect.top,
                    });
                  }}
                  onMouseLeave={() => setHoveredDay(null)}
                />
              );
            })}
          </div>
        ))}
      </div>

      {/* Tooltip */}
      {hoveredDay && (
        <div
          className="fixed z-50 bg-bg-surface border border-bg-tertiary rounded-card px-3 py-2 shadow-lg pointer-events-none"
          style={{
            left: hoveredDay.x,
            top: hoveredDay.y - 8,
            transform: "translate(-50%, -100%)",
          }}
        >
          <p className="font-body text-small text-text-secondary">
            {format(parseISO(hoveredDay.date), "d MMM", { locale: es })}
          </p>
          {hoveredDay.pain !== null ? (
            <p
              className="font-display text-body tabular-nums"
              style={{ color: getPainColor(hoveredDay.pain) }}
            >
              {hoveredDay.pain}/10
            </p>
          ) : (
            <p className="font-body text-small text-text-muted">Sin datos</p>
          )}
        </div>
      )}
    </div>
  );
}
