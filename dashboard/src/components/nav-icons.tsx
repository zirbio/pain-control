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
    [8, 8],
    [14, 8],
    [20, 8],
    [8, 14],
    [14, 14],
    [20, 14],
    [8, 20],
    [14, 20],
    [20, 20],
  ];
  return (
    <svg width="22" height="22" viewBox="0 0 28 28" fill="none" aria-hidden="true" {...props}>
      {positions.map(([cx, cy], i) => (
        <circle key={i} cx={cx} cy={cy} r={2} fill="currentColor" opacity={opacities[i]} />
      ))}
    </svg>
  );
}
