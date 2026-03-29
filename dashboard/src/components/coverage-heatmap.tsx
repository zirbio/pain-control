"use client";

import { useMemo, useState } from "react";
import { format, eachDayOfInterval, isAfter } from "date-fns";
import { es } from "date-fns/locale";
import type { DailyEntry } from "@/lib/api";

interface CoverageHeatmapProps {
  entries: DailyEntry[];
  startDate: Date;
  endDate: Date;
  isLoading: boolean;
}

export interface CategoryDef {
  key: string;
  label: string;
  check: (e: DailyEntry) => boolean;
}

export const MANUAL_CATEGORIES: CategoryDef[] = [
  { key: "pain", label: "Dolor", check: (e) => e.pain_records.length > 0 },
  { key: "medication", label: "Medicación", check: (e) => e.medication_records.length > 0 },
  { key: "mood", label: "Ánimo", check: (e) => e.mood_records.length > 0 },
  { key: "activity", label: "Actividad", check: (e) => e.activity_records.length > 0 },
  { key: "stress", label: "Estrés", check: (e) => e.stress_records.length > 0 },
  { key: "alcohol", label: "Alcohol", check: (e) => e.nutrition_records.length > 0 },
];

const AUTO_CATEGORIES: CategoryDef[] = [
  { key: "weather", label: "Weather", check: (e) => e.weather_records.length > 0 },
  { key: "appleHealth", label: "Apple Health", check: (e) => e.apple_health_records.length > 0 },
  { key: "nutriImport", label: "Nutri Import", check: (e) => e.nutrition_import_records.length > 0 },
  { key: "workouts", label: "Workouts", check: (e) => e.workout_records.length > 0 },
];

function buildTooltip(entry: DailyEntry, category: CategoryDef): string {
  switch (category.key) {
    case "pain":
      return entry.pain_records
        .map((p) => `${p.location} ${p.intensity}/10${p.pattern ? ` (${p.pattern})` : ""}`)
        .join(", ");
    case "medication":
      return entry.medication_records
        .map((m) => `${m.name}${m.dose ? ` ${m.dose}` : ""}`)
        .join(", ");
    case "mood":
      return entry.mood_records.map((m) => `${m.score}/10`).join(", ");
    case "activity":
      return entry.activity_records
        .map((a) => `${a.type}${a.duration_min ? ` ${a.duration_min}min` : ""}`)
        .join(", ");
    case "stress":
      return entry.stress_records
        .map((s) => `${s.level}/10${s.source ? ` (${s.source})` : ""}`)
        .join(", ");
    case "alcohol": {
      const n = entry.nutrition_records[0];
      if (!n) return "";
      const parts: string[] = [];
      if (n.alcohol != null) parts.push(n.alcohol ? "Sí" : "No");
      return parts.join(", ") || "Registrado";
    }
    case "weather": {
      const w = entry.weather_records[0];
      if (!w) return "";
      const parts: string[] = [];
      if (w.temperature_c != null) parts.push(`${w.temperature_c}°C`);
      if (w.conditions) parts.push(w.conditions);
      return parts.join(", ");
    }
    case "appleHealth": {
      const h = entry.apple_health_records[0];
      if (!h) return "";
      const parts: string[] = [];
      if (h.sleep_hours != null) parts.push(`${h.sleep_hours.toFixed(1)}h sueño`);
      if (h.steps != null) parts.push(`${h.steps} pasos`);
      if (h.resting_hr != null) parts.push(`${h.resting_hr} bpm`);
      return parts.join(", ");
    }
    case "nutriImport": {
      const ni = entry.nutrition_import_records[0];
      if (!ni) return "";
      const parts: string[] = [];
      if (ni.calories_kj != null) parts.push(`${Math.round(ni.calories_kj / 4.184)} kcal`);
      if (ni.protein_g != null) parts.push(`${Math.round(ni.protein_g)}g prot`);
      return parts.join(", ");
    }
    case "workouts":
      return entry.workout_records
        .map((w) => `${w.workout_type}${w.duration_min ? ` ${Math.round(w.duration_min)}min` : ""}`)
        .join(", ");
    default:
      return "";
  }
}

export function CoverageHeatmap({ entries, startDate, endDate, isLoading }: CoverageHeatmapProps) {
  const [hovered, setHovered] = useState<{
    label: string;
    summary: string;
    x: number;
    y: number;
  } | null>(null);

  const { dates, entryMap } = useMemo(() => {
    const today = new Date();
    const interval = eachDayOfInterval({ start: startDate, end: endDate }).filter(
      (d) => !isAfter(d, today)
    );
    const map = new Map<string, DailyEntry>();
    for (const entry of entries) {
      map.set(entry.date, entry);
    }
    return { dates: interval, entryMap: map };
  }, [entries, startDate, endDate]);

  if (isLoading) {
    return (
      <div className="space-y-[3px]">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="skeleton h-6 rounded-[3px]" />
        ))}
      </div>
    );
  }

  return (
    <div className="relative overflow-x-auto">
      <div
        className="grid gap-[3px]"
        style={{
          gridTemplateColumns: `100px repeat(${dates.length}, minmax(28px, 1fr))`,
        }}
      >
        {/* Header row: dates */}
        <div /> {/* empty corner */}
        {dates.map((date) => {
          const dateStr = format(date, "yyyy-MM-dd");
          return (
            <div key={dateStr} className="text-center">
              <div className="font-body text-small text-text-muted leading-tight">
                {format(date, "EEE", { locale: es })}
              </div>
              <div className="font-body text-small text-text-secondary leading-tight">
                {format(date, "d")}
              </div>
            </div>
          );
        })}

        {/* Manual category rows */}
        {MANUAL_CATEGORIES.map((cat) => (
          <RowFragment
            key={cat.key}
            category={cat}
            dates={dates}
            entryMap={entryMap}
            labelClass="text-text-secondary"
            onHover={setHovered}
          />
        ))}

        {/* Separator */}
        <div
          className="border-b border-bg-tertiary"
          style={{ gridColumn: `1 / -1`, margin: "4px 0" }}
        />

        {/* Auto category rows */}
        {AUTO_CATEGORIES.map((cat) => (
          <RowFragment
            key={cat.key}
            category={cat}
            dates={dates}
            entryMap={entryMap}
            labelClass="text-text-muted italic"
            onHover={setHovered}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 font-body text-small text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-[2px] bg-[#2d5a3d]" />
          Datos presentes
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 rounded-[2px] bg-bg-tertiary" />
          Sin datos
        </span>
        <span className="text-text-secondary">Normal = manual</span>
        <span className="italic">Cursiva = auto</span>
      </div>

      {/* Tooltip */}
      {hovered && (
        <div
          className="fixed z-50 bg-bg-surface border border-bg-tertiary rounded-card px-3 py-2 shadow-lg pointer-events-none max-w-xs"
          style={{
            left: hovered.x,
            top: hovered.y - 8,
            transform: "translate(-50%, -100%)",
          }}
        >
          <p className="font-body text-small text-text-muted">{hovered.label}</p>
          <p className="font-body text-small text-text-secondary">{hovered.summary}</p>
        </div>
      )}
    </div>
  );
}

function RowFragment({
  category,
  dates,
  entryMap,
  labelClass,
  onHover,
}: {
  category: CategoryDef;
  dates: Date[];
  entryMap: Map<string, DailyEntry>;
  labelClass: string;
  onHover: (h: { label: string; summary: string; x: number; y: number } | null) => void;
}) {
  return (
    <>
      <div className={`font-body text-small ${labelClass} flex items-center`}>
        {category.label}
      </div>
      {dates.map((date) => {
        const dateStr = format(date, "yyyy-MM-dd");
        const entry = entryMap.get(dateStr);
        const hasData = entry ? category.check(entry) : false;

        return (
          <div
            key={`${category.key}-${dateStr}`}
            className={`h-6 rounded-[3px] transition-transform duration-150 hover:scale-[1.15] cursor-default ${
              hasData ? "bg-[#2d5a3d]" : "bg-bg-tertiary"
            }`}
            onMouseEnter={(e) => {
              if (!entry || !hasData) return;
              const rect = e.currentTarget.getBoundingClientRect();
              const summary = buildTooltip(entry, category);
              onHover({
                label: `${category.label} — ${format(date, "d MMM", { locale: es })}`,
                summary,
                x: rect.left + rect.width / 2,
                y: rect.top,
              });
            }}
            onMouseLeave={() => onHover(null)}
          />
        );
      })}
    </>
  );
}
