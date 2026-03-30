"use client";

import { memo, useMemo, useState } from "react";
import { format, eachDayOfInterval, isAfter } from "date-fns";
import { es } from "date-fns/locale";
import { dataPresent } from "@/lib/design-tokens";
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
  { key: "mood", label: "Ánimo", check: (e) => e.mood_score !== null },
  { key: "habits", label: "Hábitos", check: (e) => e.stretching !== null },
  { key: "supplements", label: "Suplementos", check: (e) => e.omega3 !== null },
];

const AUTO_CATEGORIES: CategoryDef[] = [
  { key: "weather", label: "Clima", check: (e) => e.weather_records.length > 0 },
  { key: "appleHealth", label: "Apple Health", check: (e) => e.apple_health_records.length > 0 },
  { key: "nutriImport", label: "Nutrición imp.", check: (e) => e.nutrition_import_records.length > 0 },
  { key: "workouts", label: "Entrenos", check: (e) => e.workout_records.length > 0 },
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
      return entry.mood_score !== null ? `${entry.mood_score}/10` : "";
    case "habits": {
      const parts: string[] = [];
      if (entry.stretching) parts.push("Stretching");
      if (entry.alcohol) parts.push("Alcohol");
      if (entry.heavy_dinner) parts.push("Cena copiosa");
      return parts.length > 0 ? parts.join(", ") : "Sin hábitos marcados";
    }
    case "supplements": {
      const supps: string[] = [];
      if (entry.omega3) supps.push("Ω3");
      if (entry.vitamin_d) supps.push("Vit D");
      if (entry.magnesium) supps.push("Mg");
      if (entry.turmeric) supps.push("Cúrcuma");
      return supps.length > 0 ? supps.join(", ") : "Ninguno";
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

export const CoverageHeatmap = memo(function CoverageHeatmap({ entries, startDate, endDate, isLoading }: CoverageHeatmapProps) {
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
      <div className="space-y-[3px]" role="status" aria-label="Cargando datos">
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
        role="grid"
        aria-label="Mapa de cobertura de datos"
        style={{
          gridTemplateColumns: `clamp(60px, 15vw, 100px) repeat(${dates.length}, minmax(20px, 1fr))`,
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
          <span className="inline-block w-3 h-3 rounded-[2px]" style={{ backgroundColor: dataPresent }} />
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
          className="fixed z-50 bg-bg-surface border border-bg-tertiary rounded-card px-3 py-2 shadow-lg pointer-events-none max-w-[90vw]"
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
});

function showTooltip(
  target: HTMLElement,
  entry: DailyEntry,
  category: CategoryDef,
  date: Date,
  onHover: (h: { label: string; summary: string; x: number; y: number }) => void,
): void {
  requestAnimationFrame(() => {
    const rect = target.getBoundingClientRect();
    onHover({
      label: `${category.label} — ${format(date, "d MMM", { locale: es })}`,
      summary: buildTooltip(entry, category),
      x: rect.left + rect.width / 2,
      y: rect.top,
    });
  });
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
            role="gridcell"
            tabIndex={hasData ? 0 : -1}
            aria-label={`${category.label} — ${format(date, "d MMM", { locale: es })}: ${hasData ? "datos presentes" : "sin datos"}`}
            className={`h-6 rounded-[3px] transition-transform duration-150 hover:scale-[1.15] cursor-default focus-visible:ring-2 focus-visible:ring-accent-info ${
              hasData ? "" : "bg-bg-tertiary"
            }`}
            style={hasData ? { backgroundColor: dataPresent } : undefined}
            onMouseEnter={(e) => {
              if (entry && hasData) showTooltip(e.currentTarget, entry, category, date, onHover);
            }}
            onMouseLeave={() => onHover(null)}
            onKeyDown={(e) => {
              if ((e.key === 'Enter' || e.key === ' ') && entry && hasData) {
                e.preventDefault();
                showTooltip(e.currentTarget, entry, category, date, onHover);
              }
            }}
          />
        );
      })}
    </>
  );
}
