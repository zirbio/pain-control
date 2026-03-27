---
name: pain-checkin
description: Daily pain check-in — parse natural language input, extract structured health data, ask for missing fields, save via API
---

# Daily Pain Check-In

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
   - Frame questions naturally: "¿Tomaste Captor hoy?" not "Medication name required"

3. **Fetch weather**: Run this command to get today's weather:
   ```bash
   curl -s "http://localhost:8000/api/entries" | head -1
   ```
   Then fetch weather via the API (the API auto-fetches from OpenWeatherMap).

4. **Save entry**: POST to the API:
   ```bash
   curl -X POST http://localhost:8000/api/entries \
     -H "Content-Type: application/json" \
     -d '<structured JSON>'
   ```

5. **Report back**: Confirm what was saved. If any alerts from recent data, mention them.

## Field mapping

When the user says... → extract:
- "dolor lumbar 6" → pain_records: [{location: "lumbar", intensity: 6}]
- "tobillo molesta un 3" → pain_records: [{location: "tobillo_izquierdo", intensity: 3}]
- "Captor a las 8" → medication_records: [{name: "Captor", dose: "75mg tramadol + paracetamol", time_taken: "08:00"}]
- "dormí 5 horas" → this comes from Apple Health import, but note it if mentioned
- "caminé media hora" → activity_records: [{type: "caminata", duration_min: 30}]
- "me ayudó" / "mejoró" → pain_effect: "mejoró"
- "estrés laboral fuerte" → stress_records: [{level: 8, source: "laboral"}]
- "un par de cervezas" → nutrition_records: [{alcohol: true}]
- Any field not recognized → extras: [{key: "field_name", value: "value", value_type: "text|integer|boolean"}]

## Tone

Brief, warm, clinical-but-human. Never minimize pain ("solo un 6"). Acknowledge bad days simply.
