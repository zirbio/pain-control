# Branding & Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the ensō-based branding system — logo SVGs, favicons, PWA icons, OG image, empty states, nav icons, and background textures.

**Architecture:** Static SVG assets in `public/`, React components for empty states and nav icons, CSS utility classes for textures. PNGs generated via a one-time Node script using `sharp`. No runtime image processing.

**Tech Stack:** SVG (hand-crafted paths), sharp (devDep, PNG generation), Next.js 16 metadata API, React 19, Tailwind CSS v4.

**Spec:** `docs/superpowers/specs/2026-03-29-branding-assets-design.md`

---

### Task 1: Create Logo SVG Source Files

**Files:**
- Create: `dashboard/public/logo-mark.svg`
- Create: `dashboard/public/logo-full.svg`

- [ ] **Step 1: Create the mark SVG**

Create `dashboard/public/logo-mark.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" fill="none">
  <defs>
    <filter id="brush" x="-2%" y="-2%" width="104%" height="104%">
      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="noise"/>
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
  </defs>
  <path d="M 30 6 C 14 8, 4 18, 6 32 C 8 46, 18 58, 32 58 C 46 58, 56 46, 58 32 C 60 18, 50 8, 40 6"
    stroke="#D4A03A" stroke-width="3.5" stroke-linecap="round" fill="none" filter="url(#brush)"/>
  <circle cx="30" cy="6" r="2.5" fill="#D4A03A" opacity="0.6"/>
</svg>
```

The path is a cubic bezier forming ~300° of a circle with the gap at upper-right (~1h–2h). The small circle is the ink splatter at the stroke start. The `feTurbulence` + `feDisplacementMap` filter adds organic brush texture — per spec, this is the production approach.

Note: The PNG icon generation script (Task 3) uses the same path **without** the filter, since `sharp`'s SVG renderer doesn't support SVG filters reliably, and at small icon sizes the texture is invisible anyway. The filter is a display-time enhancement for the SVG when rendered in browsers.

- [ ] **Step 2: Create the full horizontal logo SVG**

Create `dashboard/public/logo-full.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="280" height="60" viewBox="0 0 280 60" fill="none">
  <defs>
    <filter id="brush" x="-2%" y="-2%" width="104%" height="104%">
      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="noise"/>
      <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.5" xChannelSelector="R" yChannelSelector="G"/>
    </filter>
  </defs>
  <!-- Mark -->
  <path d="M 28 8 C 12 10, 2 22, 4 34 C 6 46, 18 54, 30 54 C 42 54, 52 46, 54 34 C 56 22, 48 12, 38 9"
    stroke="#D4A03A" stroke-width="3.5" stroke-linecap="round" fill="none" filter="url(#brush)"/>
  <circle cx="28" cy="8" r="2.5" fill="#D4A03A" opacity="0.6"/>
  <!-- Wordmark -->
  <text x="76" y="28" fill="#F5F5F4" font-family="Newsreader, Georgia, serif" font-size="22" font-weight="500" letter-spacing="0.5">Pain Control</text>
  <text x="76" y="46" fill="#A8A29E" font-family="Satoshi, system-ui, sans-serif" font-size="10" font-weight="400" letter-spacing="3">CHRONIC PAIN OBSERVATORY</text>
</svg>
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/public/logo-mark.svg dashboard/public/logo-full.svg
git commit -m "feat(branding): add ensō logo mark and full logo SVGs"
```

---

### Task 2: Create PWA Manifest

**Files:**
- Create: `dashboard/public/manifest.json`

- [ ] **Step 1: Create manifest.json**

Create `dashboard/public/manifest.json`:

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

- [ ] **Step 2: Commit**

```bash
git add dashboard/public/manifest.json
git commit -m "feat(branding): add PWA manifest"
```

---

### Task 3: Generate PNG Icons from SVG

**Files:**
- Create: `dashboard/scripts/generate-icons.mjs`
- Create: `dashboard/public/favicon-32.png`
- Create: `dashboard/public/apple-touch-icon.png`
- Create: `dashboard/public/icon-192.png`
- Create: `dashboard/public/icon-512.png`
- Create: `dashboard/public/icon-maskable-512.png`
- Create: `dashboard/public/favicon.ico`

**Depends on:** Task 1 (logo-mark.svg must exist)

- [ ] **Step 1: Install sharp as dev dependency**

```bash
cd dashboard && npm install --save-dev sharp
```

- [ ] **Step 2: Create the icon generation script**

Create `dashboard/scripts/generate-icons.mjs`:

```javascript
import sharp from "sharp";
import { readFileSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = resolve(__dirname, "../public");

// The ensō mark SVG at different stroke widths for different sizes.
// Stroke gets thicker at smaller sizes to maintain visual weight.
function markSvg(size, strokeWidth, showSplatter = true) {
  const splatter = showSplatter
    ? `<circle cx="30" cy="6" r="2.5" fill="#D4A03A" opacity="0.6"/>`
    : "";
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 64 64" fill="none">
  <rect width="64" height="64" fill="#1c1917"/>
  <path d="M 30 6 C 14 8, 4 18, 6 32 C 8 46, 18 58, 32 58 C 46 58, 56 46, 58 32 C 60 18, 50 8, 40 6"
    stroke="#D4A03A" stroke-width="${strokeWidth}" stroke-linecap="round" fill="none"/>
  ${splatter}
</svg>`);
}

// Maskable icon needs 20% safe zone padding
function maskableSvg(size) {
  const padding = Math.round(size * 0.2);
  const innerSize = size - padding * 2;
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" fill="none">
  <rect width="${size}" height="${size}" fill="#1c1917"/>
  <svg x="${padding}" y="${padding}" width="${innerSize}" height="${innerSize}" viewBox="0 0 64 64">
    <path d="M 30 6 C 14 8, 4 18, 6 32 C 8 46, 18 58, 32 58 C 46 58, 56 46, 58 32 C 60 18, 50 8, 40 6"
      stroke="#D4A03A" stroke-width="3.5" stroke-linecap="round" fill="none"/>
    <circle cx="30" cy="6" r="2.5" fill="#D4A03A" opacity="0.6"/>
  </svg>
</svg>`);
}

const icons = [
  { name: "favicon-32.png", size: 32, strokeWidth: 5.5, splatter: true },
  { name: "apple-touch-icon.png", size: 180, strokeWidth: 3.5, splatter: true },
  { name: "icon-192.png", size: 192, strokeWidth: 3.5, splatter: true },
  { name: "icon-512.png", size: 512, strokeWidth: 3.5, splatter: true },
];

for (const icon of icons) {
  const svg = markSvg(icon.size, icon.strokeWidth, icon.splatter);
  await sharp(svg).resize(icon.size, icon.size).png().toFile(resolve(publicDir, icon.name));
  console.log(`✓ ${icon.name} (${icon.size}×${icon.size})`);
}

// Maskable icon
const maskSvg = maskableSvg(512);
await sharp(maskSvg).resize(512, 512).png().toFile(resolve(publicDir, "icon-maskable-512.png"));
console.log("✓ icon-maskable-512.png (512×512, maskable)");

// Favicon: 16×16 PNG, then wrap as ICO
// For simplicity, generate a 16px PNG. Modern browsers accept PNG favicons.
// We'll also create a 16px ICO by wrapping the PNG in ICO format.
const favicon16Svg = markSvg(16, 8, false);
const favicon16Png = await sharp(favicon16Svg).resize(16, 16).png().toBuffer();

// ICO format: header (6 bytes) + entry (16 bytes) + PNG data
const icoHeader = Buffer.alloc(6);
icoHeader.writeUInt16LE(0, 0);     // reserved
icoHeader.writeUInt16LE(1, 2);     // ICO type
icoHeader.writeUInt16LE(1, 4);     // 1 image

const icoEntry = Buffer.alloc(16);
icoEntry.writeUInt8(16, 0);        // width
icoEntry.writeUInt8(16, 1);        // height
icoEntry.writeUInt8(0, 2);         // color palette
icoEntry.writeUInt8(0, 3);         // reserved
icoEntry.writeUInt16LE(1, 4);      // color planes
icoEntry.writeUInt16LE(32, 6);     // bits per pixel
icoEntry.writeUInt32LE(favicon16Png.length, 8);  // size of PNG data
icoEntry.writeUInt32LE(22, 12);    // offset (6 + 16 = 22)

const ico = Buffer.concat([icoHeader, icoEntry, favicon16Png]);
writeFileSync(resolve(publicDir, "favicon.ico"), ico);
console.log("✓ favicon.ico (16×16 ICO wrapping PNG)");

console.log("\nDone! All icons generated.");
```

- [ ] **Step 3: Run the generation script**

```bash
cd dashboard && node scripts/generate-icons.mjs
```

Expected output:
```
✓ favicon-32.png (32×32)
✓ apple-touch-icon.png (180×180)
✓ icon-192.png (192×192)
✓ icon-512.png (512×512)
✓ icon-maskable-512.png (512×512, maskable)
✓ favicon.ico (16×16 ICO wrapping PNG)

Done! All icons generated.
```

- [ ] **Step 4: Verify generated files exist**

```bash
ls -la dashboard/public/favicon.ico dashboard/public/favicon-32.png dashboard/public/apple-touch-icon.png dashboard/public/icon-192.png dashboard/public/icon-512.png dashboard/public/icon-maskable-512.png
```

All 6 files should exist with non-zero sizes.

- [ ] **Step 5: Commit**

```bash
git add dashboard/scripts/generate-icons.mjs dashboard/public/favicon.ico dashboard/public/favicon-32.png dashboard/public/apple-touch-icon.png dashboard/public/icon-192.png dashboard/public/icon-512.png dashboard/public/icon-maskable-512.png
git commit -m "feat(branding): generate favicon and PWA icon PNGs from ensō mark"
```

---

### Task 4: Generate Open Graph Image

**Files:**
- Create: `dashboard/public/og-image.png`

**Depends on:** Task 3 (sharp installed)

- [ ] **Step 1: Add OG image generation to script**

Append to `dashboard/scripts/generate-icons.mjs`, before the final "Done" log:

```javascript
// OG Image: 1200×630
const ogSvg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" fill="none">
  <rect width="1200" height="630" fill="#1c1917"/>
  <!-- Grid texture -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#292524" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="1200" height="630" fill="url(#grid)" opacity="0.15"/>
  <!-- Ensō mark -->
  <g transform="translate(480, 235)">
    <path d="M 30 6 C 14 8, 4 18, 6 32 C 8 46, 18 58, 32 58 C 46 58, 56 46, 58 32 C 60 18, 50 8, 40 6"
      stroke="#D4A03A" stroke-width="3.5" stroke-linecap="round" fill="none"/>
    <circle cx="30" cy="6" r="2.5" fill="#D4A03A" opacity="0.6"/>
  </g>
  <!-- Wordmark -->
  <text x="552" y="290" fill="#F5F5F4" font-family="Georgia, serif" font-size="36" font-weight="500" letter-spacing="0.5">Pain Control</text>
  <text x="552" y="318" fill="#A8A29E" font-family="system-ui, sans-serif" font-size="12" font-weight="400" letter-spacing="4">CHRONIC PAIN OBSERVATORY</text>
  <!-- Bottom accent line -->
  <rect x="0" y="627" width="1200" height="3" fill="#D4A03A" opacity="0.4"/>
</svg>`);

await sharp(ogSvg).png().toFile(resolve(publicDir, "og-image.png"));
console.log("✓ og-image.png (1200×630)");
```

Note: The OG image uses Georgia/system-ui as font fallbacks since Newsreader/Satoshi won't be available to sharp's SVG renderer. The result is visually close enough for social sharing cards.

- [ ] **Step 2: Re-run the generation script**

```bash
cd dashboard && node scripts/generate-icons.mjs
```

Verify `og-image.png` appears in output.

- [ ] **Step 3: Commit**

```bash
git add dashboard/scripts/generate-icons.mjs dashboard/public/og-image.png
git commit -m "feat(branding): generate OG image for social sharing"
```

---

### Task 5: Update Layout Metadata & Cleanup Default Assets

**Files:**
- Modify: `dashboard/src/app/layout.tsx`
- Delete: `dashboard/public/file.svg`
- Delete: `dashboard/public/globe.svg`
- Delete: `dashboard/public/next.svg`
- Delete: `dashboard/public/vercel.svg`
- Delete: `dashboard/public/window.svg`

- [ ] **Step 1: Update metadata in layout.tsx**

Replace the existing `metadata` export in `dashboard/src/app/layout.tsx`:

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
    title: "Pain Control",
    description: "Chronic pain tracking and pattern analysis",
    images: [{ url: "/og-image.png", width: 1200, height: 630 }],
  },
  manifest: "/manifest.json",
};
```

- [ ] **Step 2: Delete default Next.js SVGs**

```bash
rm dashboard/public/file.svg dashboard/public/globe.svg dashboard/public/next.svg dashboard/public/vercel.svg dashboard/public/window.svg
```

- [ ] **Step 3: Verify no code references deleted files**

```bash
cd dashboard && grep -r "file\.svg\|globe\.svg\|next\.svg\|vercel\.svg\|window\.svg" src/ || echo "No references found — safe to delete"
```

Expected: "No references found — safe to delete"

- [ ] **Step 4: Commit**

```bash
git add dashboard/src/app/layout.tsx
git rm dashboard/public/file.svg dashboard/public/globe.svg dashboard/public/next.svg dashboard/public/vercel.svg dashboard/public/window.svg
git commit -m "feat(branding): update layout metadata with favicon, OG image, manifest; remove default Next.js assets"
```

---

### Task 6: Create Navigation Icons Component

**Files:**
- Create: `dashboard/src/components/nav-icons.tsx`

- [ ] **Step 1: Create nav-icons.tsx**

Create `dashboard/src/components/nav-icons.tsx`:

```tsx
import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

/** Mini ensō — brand reinforcement for Panel/home */
export function PanelIcon(props: IconProps) {
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true" {...props}>
      <path
        d="M 12 4 C 5 5, 2 10, 3 15 C 4 20, 9 24, 14 24 C 19 24, 24 20, 25 15 C 26 10, 22 5, 17 4"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

/** Organic trend curve with data point — for Análisis */
export function AnalysisIcon(props: IconProps) {
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true" {...props}>
      <path
        d="M 4 22 C 8 20, 10 12, 14 14 C 18 16, 20 8, 24 6"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinecap="round"
        fill="none"
      />
      <circle cx={14} cy={14} r={1.5} fill="currentColor" opacity={0.6} />
    </svg>
  );
}

/** Stacked lines of varying length — journal/log for Historial */
export function HistoryIcon(props: IconProps) {
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true" {...props}>
      <line x1={6} y1={8} x2={22} y2={8} stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
      <line x1={6} y1={14} x2={18} y2={14} stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
      <line x1={6} y1={20} x2={20} y2={20} stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
    </svg>
  );
}

/** 3×3 dot grid with variable opacity — heatmap reference for Cobertura */
export function CoverageIcon(props: IconProps) {
  const opacities = [0.3, 0.6, 0.9, 0.6, 0.9, 0.3, 0.9, 0.3, 0.6];
  const positions = [
    [8, 8], [14, 8], [20, 8],
    [8, 14], [14, 14], [20, 14],
    [8, 20], [14, 20], [20, 20],
  ];
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true" {...props}>
      {positions.map(([cx, cy], i) => (
        <circle key={i} cx={cx} cy={cy} r={2} fill="currentColor" opacity={opacities[i]} />
      ))}
    </svg>
  );
}
```

All icons use `currentColor` so they inherit text color from the parent — active amber, inactive muted. `aria-hidden="true"` since the adjacent label provides the accessible name.

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/components/nav-icons.tsx
git commit -m "feat(branding): add custom navigation icon components"
```

---

### Task 7: Integrate Navigation Icons into NavBar

**Files:**
- Modify: `dashboard/src/components/nav-bar.tsx`

**Depends on:** Task 6 (nav-icons.tsx must exist)

- [ ] **Step 1: Rewrite nav-bar.tsx to include icons**

Replace the full contents of `dashboard/src/components/nav-bar.tsx`:

```tsx
"use client";

import type { ComponentType, SVGProps } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelIcon, AnalysisIcon, HistoryIcon, CoverageIcon } from "./nav-icons";

const links: { href: string; label: string; Icon: ComponentType<SVGProps<SVGSVGElement>> }[] = [
  { href: "/", label: "Panel", Icon: PanelIcon },
  { href: "/analysis", label: "Análisis", Icon: AnalysisIcon },
  { href: "/history", label: "Historial", Icon: HistoryIcon },
  { href: "/coverage", label: "Cobertura", Icon: CoverageIcon },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-bg-secondary border-t border-bg-tertiary z-50 md:static md:border-t-0 md:border-b"
      style={{ paddingBottom: "max(env(safe-area-inset-bottom, 0px), 0px)" }}
    >
      <div className="max-w-6xl mx-auto flex items-center justify-center gap-4 md:gap-8 px-4 md:px-6 py-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`min-h-[44px] flex flex-col items-center justify-center gap-0.5 font-body text-small transition-colors focus-visible:ring-2 focus-visible:ring-accent-info focus-visible:rounded-md px-2 ${
                active
                  ? "text-accent-highlight"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              <link.Icon />
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
```

Key changes from original:
- Import icon components and associate them with each link
- Layout switches from horizontal text to vertical icon + label stack (`flex-col`, `gap-0.5`)
- Font size changes from `text-body` to `text-small` for the label
- Padding adjusted: `py-3` → `py-2` (icon takes up vertical space now)
- Icons inherit `currentColor` from the active/inactive text color

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/components/nav-bar.tsx
git commit -m "feat(branding): integrate custom ensō-family icons into navbar"
```

---

### Task 8: Create Empty State Component

**Files:**
- Create: `dashboard/src/components/empty-state.tsx`

- [ ] **Step 1: Create empty-state.tsx**

Create `dashboard/src/components/empty-state.tsx`:

```tsx
type EmptyStateVariant = "no-entries" | "no-data" | "insufficient-data";

interface EmptyStateProps {
  variant: EmptyStateVariant;
}

const variants: Record<EmptyStateVariant, { title: string; subtitle: string; illustration: React.ReactNode }> = {
  "no-entries": {
    title: "Sin registros",
    subtitle: "Tu primer check-in empieza el observatorio",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <circle cx={40} cy={36} r={22} stroke="#44403c" strokeWidth={1.5} strokeDasharray="4 4" fill="none" />
        <path
          d="M 36 26 C 28 28, 24 34, 26 40 C 28 46, 34 48, 40 48"
          stroke="#D4A03A" strokeWidth={2} strokeLinecap="round" fill="none" opacity={0.5}
        />
        <line x1={40} y1={32} x2={40} y2={42} stroke="#78716c" strokeWidth={1.5} strokeLinecap="round" />
        <line x1={35} y1={37} x2={45} y2={37} stroke="#78716c" strokeWidth={1.5} strokeLinecap="round" />
      </svg>
    ),
  },
  "no-data": {
    title: "Sin datos en este período",
    subtitle: "Ajusta el rango de fechas o registra nuevos días",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <line x1={12} y1={40} x2={68} y2={40} stroke="#44403c" strokeWidth={1.5} strokeLinecap="round" />
        <circle cx={28} cy={30} r={2.5} fill="#44403c" />
        <circle cx={40} cy={30} r={2.5} fill="#D4A03A" opacity={0.4} />
        <circle cx={52} cy={30} r={2.5} fill="#44403c" />
      </svg>
    ),
  },
  "insufficient-data": {
    title: "Insuficientes datos",
    subtitle: "Se necesitan ≥14 días para detectar correlaciones",
    illustration: (
      <svg width="80" height="80" viewBox="0 0 80 80" fill="none" aria-hidden="true">
        <circle cx={22} cy={44} r={2} fill="#44403c" />
        <circle cx={35} cy={28} r={2} fill="#44403c" />
        <circle cx={48} cy={38} r={2} fill="#D4A03A" opacity={0.4} />
        <circle cx={58} cy={32} r={2} fill="#44403c" />
        <line x1={18} y1={46} x2={62} y2={28} stroke="#44403c" strokeWidth={1} strokeDasharray="3 3" opacity={0.5} />
      </svg>
    ),
  },
};

export function EmptyState({ variant }: EmptyStateProps) {
  const { title, subtitle, illustration } = variants[variant];
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 bg-bg-secondary border border-bg-tertiary rounded-xl">
      <div className="mb-4">{illustration}</div>
      <p className="font-display text-body text-text-primary mb-1">{title}</p>
      <p className="font-body text-small text-text-muted text-center max-w-[240px]">{subtitle}</p>
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/components/empty-state.tsx
git commit -m "feat(branding): add EmptyState component with ensō-family illustrations"
```

---

### Task 9: Integrate Empty States into Pages

**Files:**
- Modify: `dashboard/src/app/page.tsx`
- Modify: `dashboard/src/app/analysis/page.tsx`
- Modify: `dashboard/src/app/history/page.tsx`
- Modify: `dashboard/src/app/coverage/page.tsx`

**Depends on:** Task 8 (empty-state.tsx must exist)

- [ ] **Step 1: Add empty state to dashboard page (page.tsx)**

In `dashboard/src/app/page.tsx`, add import at top:

```tsx
import { EmptyState } from "@/components/empty-state";
```

Then replace the existing `isLoading` ternary block (lines 65-96). After the loading skeleton block, add an empty state check before the metric cards:

```tsx
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton h-32" />
            ))}
          </div>
        ) : !entries?.length ? (
          <div className="mb-8">
            <EmptyState variant="no-entries" />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-8">
```

The existing cards JSX and closing tags remain unchanged.

- [ ] **Step 2: Add empty state to analysis page**

In `dashboard/src/app/analysis/page.tsx`, add import:

```tsx
import { EmptyState } from "@/components/empty-state";
```

This page always renders its components (they handle their own loading). No structural change needed — the CorrelationMatrix and LagExplorer components handle empty data internally. Skip this page.

Actually, on review: the analysis page components already handle empty states internally via their data fetching hooks. No change needed here. Remove this file from scope.

- [ ] **Step 3: Add empty state to history page**

In `dashboard/src/app/history/page.tsx`, add import:

```tsx
import { EmptyState } from "@/components/empty-state";
```

Wrap the grid section with an empty check. Replace the grid div (lines 27-42):

```tsx
        {!entries?.length ? (
          <EmptyState variant="no-entries" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2">
              <CalendarView
                entries={entries ?? []}
                selectedDate={selectedDate}
                onSelectDate={setSelectedDate}
              />
            </div>
            <div className="md:col-span-1">
              <DailyDetail
                entry={selectedDate ? (selectedEntry ?? null) : null}
                isLoading={!!selectedDate && isEntryLoading}
              />
            </div>
          </div>
        )}
```

- [ ] **Step 4: Add empty state to coverage page**

In `dashboard/src/app/coverage/page.tsx`, add import:

```tsx
import { EmptyState } from "@/components/empty-state";
```

After the date range label `<p>` and before the summary bar, add:

```tsx
          {!isLoading && !entries.length ? (
            <EmptyState variant="no-data" />
          ) : (
            <>
              {/* Summary bar */}
              <div className="bg-bg-secondary rounded-card p-4">
                {/* ... existing summary bar content ... */}
              </div>

              {/* Heatmap */}
              <div className="bg-bg-secondary rounded-card p-4">
                <CoverageHeatmap ... />
              </div>
            </>
          )}
```

Wrap the summary bar and heatmap in a fragment conditional on having data.

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/app/page.tsx dashboard/src/app/history/page.tsx dashboard/src/app/coverage/page.tsx
git commit -m "feat(branding): integrate EmptyState component into dashboard, history, and coverage pages"
```

---

### Task 10: Add Background Texture CSS Classes

**Files:**
- Modify: `dashboard/src/app/globals.css`

- [ ] **Step 1: Add texture utility classes**

Append to the end of `dashboard/src/app/globals.css` (after the `.tabular-nums` rule):

```css
/* Background textures — Warm Observatory */
.bg-grid {
  position: relative;
}
.bg-grid::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(#292524 1px, transparent 1px),
    linear-gradient(90deg, #292524 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.15;
  pointer-events: none;
}

.bg-dots {
  position: relative;
}
.bg-dots::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #44403c 0.5px, transparent 0.5px);
  background-size: 16px 16px;
  opacity: 0.2;
  pointer-events: none;
}

.bg-grain {
  position: relative;
}
.bg-grain::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  opacity: 0.04;
  pointer-events: none;
}
```

Note: All pseudo-elements use `pointer-events: none` so they don't intercept clicks. Elements using these classes need `position: relative` (already set by the class itself) and `overflow: hidden` if you want to clip the texture to rounded corners.

- [ ] **Step 2: Verify build passes**

```bash
cd dashboard && npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add dashboard/src/app/globals.css
git commit -m "feat(branding): add background texture utility classes (grid, dots, grain)"
```

---

### Task 11: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: TypeScript check**

```bash
cd dashboard && npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 2: ESLint**

```bash
cd dashboard && npm run lint
```

Expected: 0 errors.

- [ ] **Step 3: Production build**

```bash
cd dashboard && npm run build
```

Expected: Build succeeds with no warnings about missing assets.

- [ ] **Step 4: Verify all new assets exist**

```bash
ls -la dashboard/public/favicon.ico dashboard/public/favicon-32.png dashboard/public/apple-touch-icon.png dashboard/public/icon-192.png dashboard/public/icon-512.png dashboard/public/icon-maskable-512.png dashboard/public/og-image.png dashboard/public/logo-mark.svg dashboard/public/logo-full.svg dashboard/public/manifest.json
```

All 10 files should exist.

- [ ] **Step 5: Verify old assets removed**

```bash
ls dashboard/public/file.svg dashboard/public/globe.svg dashboard/public/next.svg dashboard/public/vercel.svg dashboard/public/window.svg 2>&1
```

Expected: All return "No such file or directory".

- [ ] **Step 6: Verify no references to deleted files**

```bash
cd dashboard && grep -r "file\.svg\|globe\.svg\|next\.svg\|vercel\.svg\|window\.svg" src/ || echo "Clean — no dangling references"
```

Expected: "Clean — no dangling references"

---

## Task Dependency Graph

```
Task 1 (SVGs) ──→ Task 3 (Icons) ──→ Task 4 (OG) ──→ Task 5 (Meta/Cleanup)
Task 2 (Manifest) ──────────────────────────────────→ Task 5 (Meta/Cleanup)
Task 6 (Nav Icons) ──→ Task 7 (Navbar Integration)
Task 8 (Empty State) ──→ Task 9 (Page Integration)
Task 10 (CSS Textures) — independent
Task 11 (Verification) — depends on ALL above
```

**Parallelizable groups:**
- Group A: Tasks 1, 2, 6, 8, 10 (all independent, can run in parallel)
- Group B: Tasks 3, 7, 9 (depend on Group A)
- Group C: Tasks 4, 5 (depend on Task 3)
- Group D: Task 11 (depends on everything)
