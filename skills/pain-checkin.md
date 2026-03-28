---
name: pain-checkin
description: Daily pain check-in — parse natural language input, extract structured health data, ask for missing fields, save via API
---

# Daily Pain Check-In

**Before starting**: Read `personal/medical-context.md` if it exists — it contains the user's actual medication names, pain locations, and field mappings.

Parse the user's free-form description of their day and save structured data.

## Process

1. **Parse input**: Extract all mentioned data points:
   - Pain: location(s), intensity (0-10), pattern, time of day
   - Medication: name, dose, time taken, effectiveness
   - Mood: score (1-10), emotions
   - Activity: type, duration, effect on pain
   - Stress: level (1-10), source
   - Nutrition: meals, alcohol, caffeine, water
   - Extras: any new fields not in the standard schema

2. **Check required fields** — if missing, ask ONE follow-up question:
   - Required: at least one pain record (location + intensity), medication, mood score
   - Frame questions naturally: "¿Tomaste tu medicación hoy?" not "Medication name required"

3. **Determine date**: Default to **yesterday** unless the user specifies otherwise.
   Compute yesterday's date programmatically (today minus 1 day).

4. **Fetch weather**: Fetch weather for the entry date via the API:
   ```bash
   curl -s -X POST "http://localhost:8420/api/weather/YYYY-MM-DD"
   ```
   Replace `YYYY-MM-DD` with the entry date (default: yesterday).
   If the user mentions they are in a different city, add the city query param:
   ```bash
   curl -s -X POST "http://localhost:8420/api/weather/YYYY-MM-DD?city=CityName"
   ```

5. **Save entry**: POST to the API:
   ```bash
   curl -X POST http://localhost:8420/api/entries \
     -H "Content-Type: application/json" \
     -d '<structured JSON>'
   ```
   Include `"date": "YYYY-MM-DD"` in the JSON body (yesterday's date by default).

6. **Report back**: Confirm what was saved. If any alerts from recent data, mention them.

## Field mapping

When the user says... → extract:
- "dolor lumbar 6" → pain_records: [{location: "lumbar", intensity: 6}]
- "knee hurts a 3" → pain_records: [{location: "left_knee", intensity: 3}]
- "Ibuprofen at 8" → medication_records: [{name: "Ibuprofen", dose: "400mg", time_taken: "08:00"}]
- "dormí 5 horas" → this comes from Apple Health import, but note it if mentioned
- "caminé media hora" → activity_records: [{type: "caminata", duration_min: 30}]
- "me ayudó" / "mejoró" → pain_effect: "mejoró"
- "estrés laboral fuerte" → stress_records: [{level: 8, source: "laboral"}]
- "un par de cervezas" → nutrition_records: [{alcohol: true}]
- Any field not recognized → extras: [{key: "field_name", value: "value", value_type: "text|integer|boolean"}]

## Tone

Brief, warm, clinical-but-human. Never minimize pain ("solo un 6"). Acknowledge bad days simply.
