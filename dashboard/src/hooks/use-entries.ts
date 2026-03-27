import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEntries(params?: {
  start_date?: string;
  end_date?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["entries", params],
    queryFn: () => api.entries.list(params),
  });
}

export function useEntry(date: string) {
  return useQuery({
    queryKey: ["entry", date],
    queryFn: () => api.entries.get(date),
    enabled: !!date,
  });
}
