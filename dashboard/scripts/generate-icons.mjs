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

// OG Image: 1200×630
const ogSvg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" fill="none">
  <rect width="1200" height="630" fill="#1c1917"/>
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#292524" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="1200" height="630" fill="url(#grid)" opacity="0.15"/>
  <g transform="translate(480, 235)">
    <path d="M 30 6 C 14 8, 4 18, 6 32 C 8 46, 18 58, 32 58 C 46 58, 56 46, 58 32 C 60 18, 50 8, 40 6"
      stroke="#D4A03A" stroke-width="3.5" stroke-linecap="round" fill="none"/>
    <circle cx="30" cy="6" r="2.5" fill="#D4A03A" opacity="0.6"/>
  </g>
  <text x="552" y="290" fill="#F5F5F4" font-family="Georgia, serif" font-size="36" font-weight="500" letter-spacing="0.5">Pain Control</text>
  <text x="552" y="318" fill="#A8A29E" font-family="system-ui, sans-serif" font-size="12" font-weight="400" letter-spacing="4">CHRONIC PAIN OBSERVATORY</text>
  <rect x="0" y="627" width="1200" height="3" fill="#D4A03A" opacity="0.4"/>
</svg>`);

await sharp(ogSvg).png().toFile(resolve(publicDir, "og-image.png"));
console.log("✓ og-image.png (1200×630)");

console.log("\nDone! All icons generated.");
