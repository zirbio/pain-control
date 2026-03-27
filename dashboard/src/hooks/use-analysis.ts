import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useCorrelation(varA: string, varB: string) {
  return useQuery({
    queryKey: ["correlation", varA, varB],
    queryFn: () => api.analysis.correlation(varA, varB),
    enabled: !!varA && !!varB,
  });
}

export function useLagCorrelation(target: string, variable: string, maxLag = 3) {
  return useQuery({
    queryKey: ["lag-correlation", target, variable, maxLag],
    queryFn: () => api.analysis.lagCorrelation(target, variable, maxLag),
    enabled: !!target && !!variable,
  });
}

export function useRankings() {
  return useQuery({
    queryKey: ["rankings"],
    queryFn: () => api.analysis.rankings(),
  });
}

export function useReport(startDate: string, endDate: string) {
  return useQuery({
    queryKey: ["report", startDate, endDate],
    queryFn: () => api.analysis.report(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
}
