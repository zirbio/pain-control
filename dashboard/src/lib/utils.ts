import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Spanish display labels for analysis variables.
 * Used in correlation matrix, lag explorer, and other analysis views.
 */
const VARIABLE_LABELS: Record<string, string> = {
  sleep_hours: "Horas de sueño",
  steps: "Pasos",
  stress_proxy: "Estrés (HRV)",
  resting_heart_rate: "FC en reposo",
  resting_hr: "FC en reposo",
  hrv: "VFC (HRV)",
  hrv_ms: "VFC (HRV)",
  active_energy: "Energía activa",
  med_effectiveness: "Eficacia medicación",
  medication_effectiveness: "Eficacia medicación",
  mood_score: "Ánimo",
  activity_pain_effect: "Efecto actividad",
  workout_total_min: "Minutos entreno",
  workout_count: "Entrenos",
  weather_pressure: "Presión atmosférica",
  pressure_hpa: "Presión (hPa)",
  pressure_change_hpa: "Cambio presión (hPa)",
  weather_temperature: "Temperatura",
  weather_humidity: "Humedad",
  humidity_pct: "Humedad (%)",
  alcohol: "Alcohol",
  caffeine_mg: "Cafeína (mg)",
  stretching: "Stretching",
  heavy_dinner: "Cena copiosa",
  omega3: "Omega 3",
  vitamin_d: "Vitamina D",
  magnesium: "Magnesio",
  turmeric: "Cúrcuma",
  pain_max: "Dolor (máx)",
};

/**
 * Returns a human-readable Spanish label for a variable name.
 * Falls back to Title Case conversion for unknown variables.
 */
export function formatVariable(name: string): string {
  return VARIABLE_LABELS[name] ?? name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Computes the arithmetic mean of an array of numbers.
 * Returns null for empty arrays.
 */
export function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}
