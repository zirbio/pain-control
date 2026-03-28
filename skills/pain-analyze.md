---
name: pain-analyze
description: Answer natural language questions about pain patterns by querying the analysis API — correlations, trends, comparisons
---

# Pain Analysis

Translate the user's question into an API call and present results in natural language.

## Question patterns

| User asks | API call | How to present |
|---|---|---|
| "¿X afecta mi dolor?" | GET /api/analysis/correlation?var_a=pain_max&var_b=X | Coefficient + significance + plain language |
| "¿Qué es lo que más me ayuda/perjudica?" | GET /api/analysis/rankings | Top 5 ranked factors |
| "¿El efecto de X es inmediato o al día siguiente?" | GET /api/analysis/lag-correlation?target=pain_max&variable=X | Show which lag has strongest correlation |
| "Compara febrero vs marzo" | GET /api/analysis/report for each period | Side-by-side stats |
| "¿Cómo voy esta semana?" | GET /api/analysis/report?start_date=...&end_date=... | Weekly summary |
| "¿Cuándo fue mi último brote?" | GET /api/entries?limit=90, then filter pain_max >= 7 | Show date + full context |

## Variable name mapping

Map natural language to column names:
- sueño → sleep_hours
- pasos/caminar → steps
- presión/barométrica → pressure_hpa / pressure_change_hpa
- estrés → stress_level
- ánimo → mood_score
- ejercicio/actividad → activity_minutes / activity_flag
- alcohol → alcohol
- café/cafeína → caffeine_cups
- medicación/medication → medication_effectiveness
- frecuencia cardíaca → resting_hr
- HRV/variabilidad → hrv_ms

## Presenting results

- Always include the statistical context (n, p-value, significant or not)
- Use plain language: "significativo" = "hay suficientes datos para confiar en esta correlación"
- For non-significant results: "No hay suficiente evidencia todavía (solo N días de datos)"
- Round to 1 decimal place for readability
