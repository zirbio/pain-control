"use client";

import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";
import { getPainColor } from "@/lib/design-tokens";
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
    <div className="space-y-4">
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
  const nutrition = entry.nutrition_records[0] ?? null;

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5 space-y-5 overflow-y-auto max-h-[calc(100vh-12rem)]">
      {/* Date header */}
      <div>
        <h2 className="font-display text-h2 text-text-primary capitalize">
          {dateFormatted}
        </h2>
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
        {entry.mood_records.length > 0 ? (
          <div className="space-y-1">
            {entry.mood_records.map((mood) => (
              <div key={mood.id} className="flex items-center gap-3">
                <span className="font-display text-body tabular-nums text-text-primary">
                  {mood.score}/10
                </span>
                {mood.emotions && (
                  <span className="font-body text-small text-text-secondary">
                    {mood.emotions}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="Sin registro de &aacute;nimo" />
        )}
      </div>

      {/* Activity records */}
      <div>
        <SectionTitle>Actividad</SectionTitle>
        {entry.activity_records.length > 0 ? (
          <div className="space-y-1.5">
            {entry.activity_records.map((act) => (
              <div
                key={act.id}
                className="flex items-center justify-between"
              >
                <span className="font-body text-small text-text-primary capitalize">
                  {act.type}
                </span>
                <div className="flex items-center gap-2">
                  {act.duration_min !== null && (
                    <span className="font-body text-small text-text-secondary">
                      {act.duration_min} min
                    </span>
                  )}
                  {act.pain_effect && (
                    <span
                      className="font-body text-small"
                      style={{
                        color:
                          act.pain_effect === "better"
                            ? "#6B8A7A"
                            : act.pain_effect === "worse"
                              ? "#C4512A"
                              : "#78716C",
                      }}
                    >
                      {act.pain_effect === "better"
                        ? "Mejora"
                        : act.pain_effect === "worse"
                          ? "Empeora"
                          : "Sin cambio"}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="Sin actividad registrada" />
        )}
      </div>

      {/* Stress */}
      <div>
        <SectionTitle>Estr&eacute;s</SectionTitle>
        {entry.stress_records.length > 0 ? (
          <div className="space-y-1">
            {entry.stress_records.map((s) => (
              <div key={s.id} className="flex items-center gap-3">
                <span className="font-display text-body tabular-nums text-text-primary">
                  {s.level}/10
                </span>
                {s.source && (
                  <span className="font-body text-small text-text-secondary">
                    {s.source}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="Sin registro de estr&eacute;s" />
        )}
      </div>

      {/* Nutrition */}
      <div>
        <SectionTitle>Nutrici&oacute;n</SectionTitle>
        {nutrition ? (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <span className="font-body text-small text-text-muted block">
                Agua
              </span>
              <span className="font-display text-body tabular-nums text-text-primary">
                {nutrition.water_liters !== null
                  ? `${nutrition.water_liters}L`
                  : "—"}
              </span>
            </div>
            <div>
              <span className="font-body text-small text-text-muted block">
                Caf&eacute;
              </span>
              <span className="font-display text-body tabular-nums text-text-primary">
                {nutrition.caffeine_cups !== null
                  ? `${nutrition.caffeine_cups}`
                  : "—"}
              </span>
            </div>
            <div>
              <span className="font-body text-small text-text-muted block">
                Alcohol
              </span>
              <span className="font-display text-body tabular-nums text-text-primary">
                {nutrition.alcohol !== null
                  ? nutrition.alcohol
                    ? "S\u00ed"
                    : "No"
                  : "—"}
              </span>
            </div>
          </div>
        ) : (
          <EmptyState message="Sin datos de nutrici&oacute;n" />
        )}
      </div>

      {/* Weather */}
      <div>
        <SectionTitle>Clima</SectionTitle>
        {weather ? (
          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
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
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
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
