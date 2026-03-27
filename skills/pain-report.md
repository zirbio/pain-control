---
name: pain-report
description: Generate structured weekly or monthly pain reports with trends, correlations, and alerts
---

# Pain Report

Generate a formatted report for a given period.

## Usage

`/pain-report semana` — last 7 days
`/pain-report mes` — last 30 days
`/pain-report 2026-01-01 2026-03-31` — custom range

## Process

1. Determine date range from arguments
2. Call: `curl -s "http://localhost:8000/api/analysis/report?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"`
3. Format the response into a readable report

## Report template

```
# Informe [Semanal|Mensual] — [date range]

## Resumen dolor
- Media: X.X/10 ([↑|↓|→] X.X vs periodo anterior)
- Rango: X — X
- Días buenos (≤3): X | Días malos (≥7): X

## Sueño
- Media: X.Xh
- Correlación sueño→dolor: X.XX ([fuerte|moderada|débil])

## Actividad
- X/X días activo
- Días activos: dolor medio X.X vs X.X inactivos

## Medicación
- Efectividad media: X.X/10
- Tendencia: [estable|subiendo|bajando]

## Top correlaciones
1. [variable] → dolor [+|-]X.X (p=X.XX)
2. ...

## Alertas
[Any detected alerts]
```
