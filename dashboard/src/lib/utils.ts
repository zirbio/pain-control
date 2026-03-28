import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Converts snake_case variable names to Title Case labels.
 * e.g. "sleep_hours" -> "Sleep Hours"
 */
export function formatVariable(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Computes the arithmetic mean of an array of numbers.
 * Returns null for empty arrays.
 */
export function average(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}
