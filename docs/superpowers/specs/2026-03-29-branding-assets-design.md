# Pain Control — Branding & Assets Design Spec

**Date:** 2026-03-29
**Status:** Approved

## Overview

Complete branding and asset system for Pain Control, built around an ensō-inspired logo mark. Covers logo system, app icons, OG images, empty states, navigation icons, and background textures.

## Design Direction

- **Mark concept:** Ensō — incomplete brushstroke circle, organic/calligraphic energy
- **Color:** Amber solid (`#D4A03A`) as primary brand color. No gradients in the mark.
- **Energy:** Japanese design studio — Muji, Sori Yanagi, Kenya Hara. Precision through organic simplicity.
- **Principle:** Imperfection controlled. The mark feels hand-drawn but is deliberate.

## 1. Logo System

### The Mark

An incomplete circle inspired by the zen ensō — a single brushstroke with organic character. The opening (gap) sits at the upper-right quadrant (~1h–2h clock position) and represents continuous observation, never closed.

**SVG path anatomy:**
- Main arc: cubic bezier curve, ~300° of a circle, stroke-linecap round
- Ink splatter: small circle at stroke start point, opacity 0.6
- Brush texture: SVG `feDisplacementMap` + `feTurbulence` filter for organic feel. This is the production approach — no external brush assets needed

**Mark rules:**
- Opening always at upper-right. Never close the circle.
- Ink splatter dot omitted at sizes ≤24px
- Minimum clear space: 25% of mark width on each side
- Never rotate the mark

### Logo Variants

1. **Full horizontal:** Mark + "Pain Control" (Newsreader 500) + "CHRONIC PAIN OBSERVATORY" (Satoshi 400, letter-spacing 3px)
2. **Mark only:** For favicons, app icons, social avatars
3. **Color variants:**
   - Primary: amber `#D4A03A` on dark `#1c1917`
   - Monochrome light: `#F5F5F4` on dark
   - Monochrome dark: `#1c1917` on light `#F5F5F4`
   - Primary on light: amber `#D4A03A` on `#F5F5F4`

## 2. App Assets — Favicon & PWA Icons

| File | Size | Notes |
|------|------|-------|
| `favicon.ico` | 16×16 | Mark only, thicker stroke (8px viewBox-relative), no splatter |
| `favicon-32.png` | 32×32 | Mark only, medium stroke (5.5px), splatter visible |
| `apple-touch-icon.png` | 180×180 | Mark on `#1c1917` bg, rounded corners applied by OS |
| `icon-192.png` | 192×192 | PWA manifest icon |
| `icon-512.png` | 512×512 | PWA manifest icon, full detail |
| `icon-maskable-512.png` | 512×512 | 20% safe zone padding for Android circular crop |

**Stroke scaling rule:** Stroke width increases proportionally as render size decreases to maintain visual weight. At 16px, the stroke is ~8 viewBox units. At 512px, it's ~3.5.

## 3. Open Graph Image

- **Size:** 1200×630
- **Background:** `#1c1917` with subtle observatory grid pattern (24px, opacity 0.15)
- **Content:** Centered — mark (80px) + "Pain Control" (Newsreader) + subtitle (Satoshi)
- **Accent:** Bottom edge has a horizontal amber line with gradient transparency (`linear-gradient(90deg, transparent, #D4A03A, transparent)`, opacity 0.4)

## 4. PWA Manifest

```json
{
  "name": "Pain Control",
  "short_name": "Pain Control",
  "description": "Chronic pain observatory",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1c1917",
  "theme_color": "#D4A03A",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

## 5. Empty States

Reusable `<EmptyState>` component with variants. Each uses minimal ensō-family SVG illustrations.

### Variants

| Variant | Illustration | Title | Subtitle |
|---------|-------------|-------|----------|
| `no-entries` | Dashed circle + incomplete ensō + plus sign | "Sin registros" | "Tu primer check-in empieza el observatorio" |
| `no-data` | Flat line + 3 latent dots (center amber) | "Sin datos en este período" | "Ajusta el rango de fechas o registra nuevos días" |
| `insufficient-data` | Scattered dots + dashed trend line | "Insuficientes datos" | "Se necesitan ≥14 días para detectar correlaciones" |

**Component API:**
```tsx
<EmptyState variant="no-entries" />
<EmptyState variant="no-data" />
<EmptyState variant="insufficient-data" />
```

Styled with: `bg-bg-secondary`, `border border-bg-tertiary`, `rounded-xl`, centered layout. Illustrations are inline SVGs within the component.

## 6. Navigation Icons

Custom SVG icons replacing the current text-only navbar. Stroke-based, 1.5px weight, organic style consistent with the ensō mark.

| Route | Icon | Description |
|-------|------|-------------|
| `/` (Panel) | Mini ensō | Simplified incomplete circle — brand reinforcement |
| `/analysis` | Organic curve + dot | Freehand trend line with a highlighted data point |
| `/history` | Stacked lines | Three horizontal lines of varying length — log/journal |
| `/coverage` | Dot grid | 3×3 grid of dots with variable opacity — heatmap reference |

**Integration:** Icon above label, vertical stack. Active state uses `#D4A03A` (amber), inactive uses `#9a918a` (text-muted). Touch targets remain ≥44px (WCAG).

## 7. Background Textures

CSS-only patterns added as utility classes. No external images.

| Class | Pattern | Use case |
|-------|---------|----------|
| `.bg-grid` | Linear gradient grid, 24px spacing, opacity 0.15 | Hero sections, splash screens |
| `.bg-dots` | Radial gradient dots, 16px spacing, opacity 0.2 | Card backgrounds, sections |
| `.bg-grain` | SVG feTurbulence noise filter, opacity 0.04 | General depth overlay |

## 8. Integration Plan

### Files to create (12)
- `public/favicon.ico`
- `public/favicon-32.png`
- `public/apple-touch-icon.png`
- `public/icon-192.png`
- `public/icon-512.png`
- `public/icon-maskable-512.png`
- `public/og-image.png`
- `public/logo-full.svg`
- `public/logo-mark.svg`
- `public/manifest.json`
- `src/components/empty-state.tsx`
- `src/components/nav-icons.tsx`

### Files to modify (7)
- `src/app/layout.tsx` — metadata: favicon links, og:image, manifest link
- `src/app/globals.css` — add `.bg-grid`, `.bg-dots`, `.bg-grain` utility classes
- `src/components/nav-bar.tsx` — integrate nav icons above labels
- `src/app/page.tsx` — use `<EmptyState>` for empty data states
- `src/app/analysis/page.tsx` — use `<EmptyState>` for insufficient data
- `src/app/history/page.tsx` — use `<EmptyState>` for no entries
- `src/app/coverage/page.tsx` — use `<EmptyState>` for no coverage data

### Files to delete (5)
- `public/file.svg`
- `public/globe.svg`
- `public/next.svg`
- `public/vercel.svg`
- `public/window.svg`

### PNG Generation Strategy
SVG → PNG via Playwright headless browser screenshots. This ensures pixel-perfect rendering of the SVG marks at exact target sizes. The `favicon.ico` is generated from the 16×16 PNG via `png-to-ico` or equivalent tool.

## 9. Meta Tags (layout.tsx)

```tsx
export const metadata: Metadata = {
  title: "Pain Control",
  description: "Chronic pain tracking and pattern analysis",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "16x16" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },
  openGraph: {
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  manifest: "/manifest.json",
};
```
