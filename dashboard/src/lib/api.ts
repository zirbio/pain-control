const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export interface PainRecord {
  id: number;
  location: string;
  intensity: number;
  pattern: string | null;
  time_of_day: string | null;
  notes: string | null;
}

export interface WeatherRecord {
  id: number;
  temperature_c: number | null;
  humidity_pct: number | null;
  pressure_hpa: number | null;
  pressure_change_hpa: number | null;
  conditions: string | null;
  location: string | null;
}

export interface AppleHealthRecord {
  id: number;
  sleep_hours: number | null;
  sleep_quality: string | null;
  resting_hr: number | null;
  hrv_ms: number | null;
  steps: number | null;
  active_calories: number | null;
  spo2_pct: number | null;
}

export interface DailyEntry {
  id: number;
  date: string;
  created_at: string;
  updated_at: string;
  pain_records: PainRecord[];
  medication_records: Array<{
    id: number;
    name: string;
    dose: string | null;
    time_taken: string | null;
    effectiveness: number | null;
  }>;
  mood_records: Array<{ id: number; score: number; emotions: string | null; notes: string | null }>;
  activity_records: Array<{
    id: number;
    type: string;
    duration_min: number | null;
    pain_effect: string | null;
    notes: string | null;
  }>;
  stress_records: Array<{ id: number; level: number; source: string | null; notes: string | null }>;
  nutrition_records: Array<{
    id: number;
    meals: string | null;
    alcohol: boolean | null;
    caffeine_cups: number | null;
    water_liters: number | null;
    notes: string | null;
  }>;
  weather_records: WeatherRecord[];
  apple_health_records: AppleHealthRecord[];
  extras: Array<{ id: number; key: string; value: string; value_type: string; first_seen: string | null }>;
}

export interface CorrelationResult {
  coefficient: number | null;
  p_value: number | null;
  n: number;
  method: string;
  significant: boolean;
}

export interface LagCorrelationResult {
  lag: number;
  coefficient: number | null;
  p_value: number | null;
  n: number;
  significant?: boolean;
}

export interface RankingResult {
  variable: string;
  coefficient: number;
  p_value: number;
  n: number;
  significant: boolean;
}

export interface ReportResult {
  period: { start: string; end: string; days: number };
  pain?: {
    mean: number;
    min: number;
    max: number;
    good_days: number;
    bad_days: number;
    trend: { direction: string; slope: number };
  };
  sleep?: { mean: number; min: number; max: number };
  activity?: { active_days: number; total_days: number; mean_minutes: number | null };
  medication?: { mean_effectiveness: number; trend: { direction: string } | null };
  top_correlations?: RankingResult[];
}

export const api = {
  entries: {
    list: (params?: { start_date?: string; end_date?: string; limit?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set("start_date", params.start_date);
      if (params?.end_date) searchParams.set("end_date", params.end_date);
      if (params?.limit) searchParams.set("limit", String(params.limit));
      const qs = searchParams.toString();
      return fetchApi<DailyEntry[]>(`/api/entries${qs ? `?${qs}` : ""}`);
    },
    get: (date: string) => fetchApi<DailyEntry>(`/api/entries/${date}`),
  },
  analysis: {
    correlation: (varA: string, varB: string) =>
      fetchApi<CorrelationResult>(`/api/analysis/correlation?var_a=${varA}&var_b=${varB}`),
    lagCorrelation: (target: string, variable: string, maxLag = 3) =>
      fetchApi<LagCorrelationResult[]>(
        `/api/analysis/lag-correlation?target=${target}&variable=${variable}&max_lag=${maxLag}`
      ),
    rankings: () => fetchApi<RankingResult[]>("/api/analysis/rankings"),
    report: (startDate: string, endDate: string) =>
      fetchApi<ReportResult>(`/api/analysis/report?start_date=${startDate}&end_date=${endDate}`),
  },
};
