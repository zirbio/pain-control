export const painScale = [
  "#6B8A7A", // 0 — sage
  "#7B9A7E", // 1
  "#8DAA82", // 2
  "#A8B86A", // 3 — sage-lime
  "#C4A84E", // 4
  "#D4A03A", // 5 — amber
  "#D9882A", // 6
  "#D4702A", // 7 — warm orange
  "#C4512A", // 8 — cinnabar
  "#A63A2A", // 9
  "#8B2500", // 10 — deep terracotta
] as const;

export function getPainColor(intensity: number): string {
  const clamped = Math.max(0, Math.min(10, Math.round(intensity)));
  return painScale[clamped];
}

export const atmosphericColors = {
  highPressure: "#2A3040",
  normal: "#1C1917",
  lowPressure: "#2A2018",
} as const;

export const accentColors = {
  positive: "#6B8A7A",
  warning: "#D4A03A",
  negative: "#C4512A",
  info: "#7B9FBF",
  highlight: "#D4A03A",
} as const;

/** Shared tick style for Recharts axes across all chart components. */
export const chartTickStyle = {
  fill: "#78716C",
  fontSize: 11,
  fontFamily: "Satoshi, system-ui, sans-serif",
} as const;

/** Shared grid style for Recharts CartesianGrid. */
export const chartGridProps = {
  strokeDasharray: "3 3",
  stroke: "#44403C",
  strokeOpacity: 0.3,
  vertical: false,
} as const;
