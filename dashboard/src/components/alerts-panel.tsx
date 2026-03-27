"use client";

import { AlertCard } from "./alert-card";
import { useRankings } from "@/hooks/use-analysis";

export function AlertsPanel() {
  const { data: rankings, isLoading } = useRankings();

  if (isLoading) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6">
        <div className="skeleton h-24" />
      </div>
    );
  }

  const significantCorrelations = rankings?.filter((r) => r.significant).slice(0, 3) ?? [];

  if (significantCorrelations.length === 0) {
    return (
      <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-6 flex items-center justify-center h-40">
        <span className="text-text-muted font-body text-body">
          Sin alertas — necesitas más datos para detectar patrones
        </span>
      </div>
    );
  }

  const variableLabels: Record<string, string> = {
    sleep_hours: "horas de sueño",
    steps: "pasos diarios",
    stress_level: "nivel de estrés",
    activity_minutes: "minutos de actividad",
    pressure_hpa: "presión barométrica",
    pressure_change_hpa: "cambio de presión",
    humidity_pct: "humedad",
    temperature_c: "temperatura",
    medication_effectiveness: "efectividad del Captor",
    mood_score: "estado de ánimo",
    resting_hr: "frecuencia cardíaca en reposo",
    hrv_ms: "variabilidad cardíaca (HRV)",
    alcohol: "consumo de alcohol",
    caffeine_cups: "consumo de cafeína",
    water_liters: "hidratación",
    active_calories: "calorías activas",
  };

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-4">
      <h3 className="font-body text-label uppercase text-text-muted tracking-widest mb-4">
        ◆ Alertas
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {significantCorrelations.map((corr) => {
          const label = variableLabels[corr.variable] || corr.variable.replace(/_/g, " ");
          const direction = corr.coefficient > 0 ? "+" : "";
          const effect = corr.coefficient > 0 ? "empeora" : "mejora";

          return (
            <AlertCard
              key={corr.variable}
              title="Correlación detectada"
              body={`${label} ${effect} tu dolor (${direction}${corr.coefficient.toFixed(2)})`}
              metadata={`p=${corr.p_value.toFixed(3)} · n=${corr.n} días`}
            />
          );
        })}
      </div>
    </div>
  );
}
