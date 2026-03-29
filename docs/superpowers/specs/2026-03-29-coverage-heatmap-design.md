# Coverage Heatmap — Data Completeness Dashboard

## Context

The pain-control system collects data from multiple sources: manual check-ins (6 categories) and auto-imports (4 sources). There is no visibility into which days have complete data and which have gaps. This makes it hard to know if correlations are reliable (missing data = weaker analysis).

This feature adds a dedicated `/coverage` page with a GitHub-style heatmap showing data presence per category per day.

## Design

### Page: `/coverage`

New page in the Next.js App Router dashboard at `app/coverage/page.tsx`.

### Layout

1. **Header**: Page title "Cobertura de datos" + range selector buttons (7d / 14d / 30d). Default: 14 days. Navigation arrows to shift the window backward/forward.

2. **Summary metric**: Global completeness bar for the selected period. Format: "78% — 11 de 14 días con check-in completo". A day counts as "complete" when all 6 manual categories have data.

3. **Heatmap grid**:
   - **Rows** = data categories, split into two visual groups with a separator:
     - **Manual** (normal text): Dolor, Medicación, Ánimo, Actividad, Estrés, Alcohol
     - **Auto-importado** (italic, muted text): Weather, Apple Health, Nutri Import, Workouts
   - **Columns** = days in the selected range, newest on the right
   - **Cells**: Green (`#2d5a3d`) = data present, dark (`#44403c`) = no data
   - **Hover tooltip**: Brief summary of what data exists (e.g., "Dolor lumbar 5/10, constante")
   - **Column headers**: Day number + abbreviated weekday

4. **Legend**: Color indicators + "Normal = manual, Italic = auto-imported" explanation.

### Data Source

Uses the existing `useEntries()` hook with appropriate `limit` parameter. No new backend endpoint needed.

Completeness logic (client-side):

```typescript
const categories = {
  // Manual
  pain: (e) => e.pain_records.length > 0,
  medication: (e) => e.medication_records.length > 0,
  mood: (e) => e.mood_records.length > 0,
  activity: (e) => e.activity_records.length > 0,
  stress: (e) => e.stress_records.length > 0,
  alcohol: (e) => e.nutrition_records.length > 0,
  // Auto-imported
  weather: (e) => e.weather_records.length > 0,
  appleHealth: (e) => e.apple_health_records.length > 0,
  nutriImport: (e) => e.nutrition_import_records.length > 0,
  workouts: (e) => e.workout_records.length > 0,
};
```

### Navigation

Add "Cobertura" link to the existing `NavBar` component (`components/nav-bar.tsx`).

### Files to Create/Modify

| File | Action |
|------|--------|
| `app/coverage/page.tsx` | Create — page component with range selector and heatmap |
| `components/coverage-heatmap.tsx` | Create — heatmap grid component |
| `components/nav-bar.tsx` | Modify — add /coverage link |

### Visual Design

Follows the existing "Warm Observatory" design system:
- Background: `#1c1917` page, `#292524` card backgrounds
- Text: `#f5f5f4` primary, `#a8a29e` secondary, `#78716c` muted
- Present cell: `#2d5a3d` (green from existing design tokens)
- Missing cell: `#44403c` (matches existing empty states)
- Typography: Newsreader for headings, Satoshi for body
- Cell border-radius: 3px (matches existing heatmap style)

### Interactions

- **Range buttons** (7d/14d/30d): Toggle active state, re-query entries
- **Arrow navigation**: Shift date window by the selected range size
- **Hover on cell**: Show tooltip with data summary
- **Click on day column header**: Navigate to `/history` with that date selected (existing daily-detail view)

### Non-Goals

- No editing data from this view
- No sub-field level granularity (e.g., "pain has location but not pattern") — category level only
- No backend changes
