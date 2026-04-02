"use client";

import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import { getPainColor, accentColors, textColors } from "@/lib/design-tokens";
import type { DailyEntry } from "@/lib/api";

interface DailyDetailProps {
  entry: DailyEntry | null;
  isLoading: boolean;
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="font-body text-label uppercase text-text-muted tracking-widest mb-2">
      {children}
    </h3>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="font-body text-small text-text-muted italic">{message}</p>
  );
}

function PainBar({ location, intensity }: { location: string; intensity: number }) {
  const color = getPainColor(intensity);
  const widthPct = Math.max((intensity / 10) * 100, 4);

  return (
    <div className="mb-2 last:mb-0">
      <div className="flex items-center justify-between mb-1">
        <span className="font-body text-small text-text-secondary capitalize">
          {location.replace(/_/g, " ")}
        </span>
        <span
          className="font-display text-small tabular-nums"
          style={{ color }}
        >
          {intensity}/10
        </span>
      </div>
      <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-300"
          style={{ width: `${widthPct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function SkeletonDetail() {
  return (
    <div
      className="space-y-4"
      role="status"
      aria-label="Cargando detalles"
    >
      <div className="skeleton h-6 w-3/4" />
      <div className="skeleton h-4 w-1/2" />
      <div className="skeleton h-20 w-full" />
      <div className="skeleton h-4 w-1/2" />
      <div className="skeleton h-16 w-full" />
      <div className="skeleton h-4 w-1/2" />
      <div className="skeleton h-12 w-full" />
    </div>
  );
}

const DAY_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  vacation: { label: "Vacaciones", color: accentColors.positive },
  weekend: { label: "Fin de semana", color: accentColors.info },
  workday: { label: "Laborable", color: textColors.muted },
};

const PAIN_EFFECT_COLORS: Record<string, string> = {
  mejoró: accentColors.positive,
  empeoró: accentColors.negative,
};

const PAIN_EFFECT_LABELS: Record<string, string> = {
  mejoró: "Mejora",
  empeoró: "Empeora",
};

function PainEffectLabel({ effect }: { effect: string }) {
  return (
    <span
      className="font-body text-small"
      style={{ color: PAIN_EFFECT_COLORS[effect] ?? textColors.muted }}
    >
      {PAIN_EFFECT_LABELS[effect] ?? "Sin cambio"}
    </span>
  );
}

export function DailyDetail({ entry, isLoading }: DailyDetailProps) {
  if (isLoading) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
        <SkeletonDetail />
      </div>
    );
  }

  if (!entry) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5 flex items-center justify-center min-h-[200px]">
        <p className="font-body text-body text-text-muted text-center">
          Selecciona un día del calendario
        </p>
      </div>
    );
  }

  const dateFormatted = format(parseISO(entry.date), "EEEE, d 'de' MMMM yyyy", {
    locale: es,
  });

  const weather = entry.weather_records[0] ?? null;
  const health = entry.apple_health_records[0] ?? null;
  const dayTypeCfg = entry.day_type && entry.day_type !== "workday"
    ? DAY_TYPE_CONFIG[entry.day_type]
    : null;

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5 space-y-5 overflow-y-auto max-h-[calc(100vh-12rem)]">
      {/* Date header */}
      <div className="flex items-center gap-3">
        <h2 className="font-display text-h2 text-text-primary capitalize">
          {dateFormatted}
        </h2>
        {dayTypeCfg && (
          <span
            className="font-body text-small px-2 py-0.5 rounded-full border"
            style={{ color: dayTypeCfg.color, borderColor: dayTypeCfg.color }}
          >
            {dayTypeCfg.label}
          </span>
        )}
      </div>

      {/* Pain records */}
      <div>
        <SectionTitle>Dolor</SectionTitle>
        {entry.pain_records.length > 0 ? (
          <div>
            {entry.pain_records.map((pr) => (
              <PainBar
                key={pr.id}
                location={pr.location}
                intensity={pr.intensity}
              />
            ))}
            {entry.pain_records.some((pr) => pr.notes) && (
              <div className="mt-2">
                {entry.pain_records
                  .filter((pr) => pr.notes)
                  .map((pr) => (
                    <p
                      key={`note-${pr.id}`}
                      className="font-body text-small text-text-muted"
                    >
                      {pr.location}: {pr.notes}
                    </p>
                  ))}
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="Sin registros de dolor" />
        )}
      </div>

      {/* Medication records */}
      <div>
        <SectionTitle>Medicaci&oacute;n</SectionTitle>
        {entry.medication_records.length > 0 ? (
          <div className="space-y-1.5">
            {entry.medication_records.map((med) => (
              <div
                key={med.id}
                className="flex items-center justify-between"
              >
                <div>
                  <span className="font-body text-small text-text-primary">
                    {med.name}
                  </span>
                  {med.dose && (
                    <span className="font-body text-small text-text-muted ml-2">
                      {med.dose}
                    </span>
                  )}
                  {med.time_taken && (
                    <span className="font-body text-small text-text-muted ml-2">
                      {med.time_taken}
                    </span>
                  )}
                </div>
                {med.effectiveness !== null && (
                  <span className="font-display text-small tabular-nums text-accent-warning">
                    {med.effectiveness}/10
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="Sin medicaci&oacute;n" />
        )}
      </div>

      {/* Mood */}
      <div>
        <SectionTitle>&Aacute;nimo</SectionTitle>
        {entry.mood_score !== null ? (
          <div className="flex items-center gap-3">
            <span className="font-display text-body tabular-nums text-text-primary">
              {entry.mood_score}/10
            </span>
            {entry.mood_emotions && (
              <span className="font-body text-small text-text-secondary">
                {(() => {
                  try {
                    const parsed = JSON.parse(entry.mood_emotions);
                    return Array.isArray(parsed) ? parsed.join(", ") : entry.mood_emotions;
                  } catch {
                    return entry.mood_emotions;
                  }
                })()}
              </span>
            )}
          </div>
        ) : (
          <EmptyState message="Sin registro de &aacute;nimo" />
        )}
      </div>

      {/* Activity & Pain Effect */}
      <div>
        <SectionTitle>Actividad</SectionTitle>
        {entry.workout_records.length > 0 ? (
          <div className="space-y-1.5">
            {entry.workout_records.map((w) => (
              <div key={w.id} className="flex items-center justify-between">
                <span className="font-body text-small text-text-primary capitalize">
                  {w.workout_type}
                </span>
                {w.duration_min !== null && (
                  <span className="font-body text-small text-text-secondary">
                    {Math.round(w.duration_min)} min
                  </span>
                )}
              </div>
            ))}
            {entry.activity_pain_effect && (
              <div className="mt-1">
                <PainEffectLabel effect={entry.activity_pain_effect} />
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="Sin actividad registrada" />
        )}
      </div>

      {/* Stress */}
      <div>
        <SectionTitle>Estr&eacute;s</SectionTitle>
        {entry.stress_source ? (
          <span className="font-body text-small text-text-secondary">
            {entry.stress_source}
          </span>
        ) : (
          <EmptyState message="Sin fuente de estr&eacute;s anotada" />
        )}
      </div>

      {/* Habits & Supplements */}
      <div>
        <SectionTitle>H&aacute;bitos</SectionTitle>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Stretching", value: entry.stretching },
            { label: "Alcohol", value: entry.alcohol },
            { label: "Cena copiosa", value: entry.heavy_dinner },
            { label: "Omega 3", value: entry.omega3 },
            { label: "Vitamina D", value: entry.vitamin_d },
            { label: "Magnesio", value: entry.magnesium },
            { label: "C\u00farcuma", value: entry.turmeric },
          ].map(({ label, value }) => (
            <div key={label}>
              <span className="font-body text-small text-text-muted block">
                {label}
              </span>
              <span className="font-display text-body tabular-nums text-text-primary">
                {value === null ? "\u2014" : value ? "S\u00ed" : "No"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Weather */}
      <div>
        <SectionTitle>Clima</SectionTitle>
        {weather ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1">
            {weather.conditions && (
              <div className="col-span-2 mb-1">
                <span className="font-body text-small text-text-primary capitalize">
                  {weather.conditions}
                </span>
              </div>
            )}
            {weather.temperature_c !== null && (
              <div>
                <span className="font-body text-small text-text-muted">
                  Temp.
                </span>
                <span className="font-display text-small tabular-nums text-text-secondary ml-2">
                  {weather.temperature_c}&deg;C
                </span>
              </div>
            )}
            {weather.humidity_pct !== null && (
              <div>
                <span className="font-body text-small text-text-muted">
                  Humedad
                </span>
                <span className="font-display text-small tabular-nums text-text-secondary ml-2">
                  {weather.humidity_pct}%
                </span>
              </div>
            )}
            {weather.pressure_hpa !== null && (
              <div>
                <span className="font-body text-small text-text-muted">
                  Presi&oacute;n
                </span>
                <span className="font-display text-small tabular-nums text-text-secondary ml-2">
                  {weather.pressure_hpa} hPa
                </span>
              </div>
            )}
            {weather.pressure_change_hpa !== null && (
              <div>
                <span className="font-body text-small text-text-muted">
                  Cambio
                </span>
                <span className="font-display text-small tabular-nums text-text-secondary ml-2">
                  {weather.pressure_change_hpa > 0 ? "+" : ""}
                  {weather.pressure_change_hpa} hPa
                </span>
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="Sin datos meteorol&oacute;gicos" />
        )}
      </div>

      {/* Apple Health */}
      <div>
        <SectionTitle>Apple Health</SectionTitle>
        {health ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
            {health.sleep_hours !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  Sue&ntilde;o
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.sleep_hours}h
                </span>
              </div>
            )}
            {health.resting_hr !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  FC reposo
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.resting_hr} bpm
                </span>
              </div>
            )}
            {health.hrv_ms !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  HRV
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.hrv_ms} ms
                </span>
              </div>
            )}
            {health.steps !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  Pasos
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.steps.toLocaleString()}
                </span>
              </div>
            )}
            {health.active_calories !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  Cal. activas
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.active_calories}
                </span>
              </div>
            )}
            {health.spo2_pct !== null && (
              <div>
                <span className="font-body text-small text-text-muted block">
                  SpO2
                </span>
                <span className="font-display text-body tabular-nums text-text-primary">
                  {health.spo2_pct}%
                </span>
              </div>
            )}
          </div>
        ) : (
          <EmptyState message="Sin datos de salud" />
        )}
      </div>

      {/* Extras */}
      {entry.extras.length > 0 && (
        <div>
          <SectionTitle>Extras</SectionTitle>
          <div className="space-y-1">
            {entry.extras.map((extra) => (
              <div
                key={extra.id}
                className="flex items-center justify-between"
              >
                <span className="font-body text-small text-text-secondary">
                  {extra.key}
                </span>
                <span className="font-body text-small text-text-primary">
                  {extra.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
