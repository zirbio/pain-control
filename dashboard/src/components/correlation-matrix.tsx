"use client";

import { memo, useMemo } from "react";
import { useRankings } from "@/hooks/use-analysis";
import { accentColors, warningBgLight } from "@/lib/design-tokens";
import { formatVariable } from "@/lib/utils";

function SignificanceBadge({ significant }: { significant: boolean }) {
  if (!significant) return null;
  return (
    <span
      className="inline-block px-1.5 py-0.5 rounded text-small font-body"
      style={{ backgroundColor: warningBgLight, color: accentColors.warning }}
    >
      sig
    </span>
  );
}

export const CorrelationMatrix = memo(function CorrelationMatrix() {
  const { data: rankings, isLoading, error, refetch } = useRankings();

  const sorted = useMemo(
    () => [...(rankings ?? [])].sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient)),
    [rankings],
  );

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="skeleton h-10" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-8">
        <span className="font-body text-body text-text-muted">
          No se pudieron cargar las correlaciones. Los datos est&aacute;n seguros.
        </span>
        <button
          onClick={() => refetch()}
          className="font-body text-small text-accent-info hover:text-text-primary transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!rankings || rankings.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <span className="font-body text-body text-text-muted">
          A&uacute;n no hay datos de correlaci&oacute;n
        </span>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-bg-tertiary">
            <th className="text-left font-body text-label uppercase text-text-muted tracking-widest py-3 pr-4">
              Variable
            </th>
            <th className="text-right font-body text-label uppercase text-text-muted tracking-widest py-3 px-4">
              <abbr title="Positivo (rojo) = se asocia con más dolor. Negativo (verde) = se asocia con menos dolor." className="no-underline cursor-help">
                Coeficiente
              </abbr>
            </th>
            <th className="hidden sm:table-cell text-right font-body text-label uppercase text-text-muted tracking-widest py-3 px-4">
              p-valor
            </th>
            <th className="hidden sm:table-cell text-right font-body text-label uppercase text-text-muted tracking-widest py-3 px-4">
              n
            </th>
            <th className="text-center font-body text-label uppercase text-text-muted tracking-widest py-3 pl-4">
              <abbr title="Significancia estadística (p < 0.05)" className="no-underline cursor-help">
                Sig.
              </abbr>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const coeffColor =
              row.coefficient > 0
                ? accentColors.negative
                : accentColors.positive;

            return (
              <tr
                key={row.variable}
                className="border-b border-bg-tertiary/50 transition-colors hover:bg-bg-tertiary/20"
              >
                <td className="py-3 pr-4">
                  <span className="font-body text-body text-text-primary">
                    {formatVariable(row.variable)}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <span
                    className="font-display text-body tabular-nums"
                    style={{ color: coeffColor }}
                  >
                    {row.coefficient > 0 ? "+" : ""}
                    {row.coefficient.toFixed(3)}
                  </span>
                </td>
                <td className="hidden sm:table-cell py-3 px-4 text-right">
                  <span className="font-body text-small tabular-nums text-text-secondary">
                    {row.p_value < 0.001
                      ? "<0.001"
                      : row.p_value.toFixed(3)}
                  </span>
                </td>
                <td className="hidden sm:table-cell py-3 px-4 text-right">
                  <span className="font-body text-small tabular-nums text-text-muted">
                    {row.n}
                  </span>
                </td>
                <td className="py-3 pl-4 text-center">
                  <SignificanceBadge significant={row.significant} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
});
