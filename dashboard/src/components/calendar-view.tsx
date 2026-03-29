"use client";

import { memo, useMemo, useState } from "react";
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addMonths,
  subMonths,
  isSameMonth,
  isAfter,
} from "date-fns";
import { es } from "date-fns/locale";
import { getPainColor } from "@/lib/design-tokens";
import type { DailyEntry } from "@/lib/api";

interface CalendarViewProps {
  entries: DailyEntry[];
  selectedDate: string | null;
  onSelectDate: (date: string) => void;
}

const DAY_HEADERS = ["L", "M", "X", "J", "V", "S", "D"];

export const CalendarView = memo(function CalendarView({
  entries,
  selectedDate,
  onSelectDate,
}: CalendarViewProps) {
  const [currentMonth, setCurrentMonth] = useState(() => new Date());

  const painByDate = useMemo(() => {
    const map = new Map<string, number>();
    for (const entry of entries) {
      if (entry.pain_records.length > 0) {
        const maxPain = Math.max(
          ...entry.pain_records.map((p) => p.intensity),
        );
        map.set(entry.date, maxPain);
      }
    }
    return map;
  }, [entries]);

  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(currentMonth);
    const calStart = startOfWeek(monthStart, { weekStartsOn: 1 });
    const calEnd = endOfWeek(monthEnd, { weekStartsOn: 1 });

    const days: Array<{
      date: Date;
      dateStr: string;
      inMonth: boolean;
      future: boolean;
      pain: number | null;
    }> = [];

    let day = calStart;
    const today = new Date();
    while (!isAfter(day, calEnd)) {
      const dateStr = format(day, "yyyy-MM-dd");
      days.push({
        date: day,
        dateStr,
        inMonth: isSameMonth(day, currentMonth),
        future: isAfter(day, today),
        pain: painByDate.get(dateStr) ?? null,
      });
      day = addDays(day, 1);
    }

    return days;
  }, [currentMonth, painByDate]);

  const todayStr = format(new Date(), "yyyy-MM-dd");

  return (
    <div className="bg-bg-secondary border border-bg-tertiary rounded-card p-5">
      {/* Header with navigation */}
      <div className="flex items-center justify-between mb-5">
        <button
          onClick={() => setCurrentMonth((m) => subMonths(m, 1))}
          className="w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center rounded-full text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors focus-visible:ring-2 focus-visible:ring-accent-info"
          aria-label="Mes anterior"
        >
          &lsaquo;
        </button>
        <h2 className="font-display text-h2 text-text-primary capitalize">
          {format(currentMonth, "MMMM yyyy", { locale: es })}
        </h2>
        <button
          onClick={() => setCurrentMonth((m) => addMonths(m, 1))}
          className="w-10 h-10 sm:w-8 sm:h-8 flex items-center justify-center rounded-full text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors focus-visible:ring-2 focus-visible:ring-accent-info"
          aria-label="Mes siguiente"
        >
          &rsaquo;
        </button>
      </div>

      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {DAY_HEADERS.map((d) => (
          <div
            key={d}
            className="text-center font-body text-small text-text-muted py-1"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map((day) => {
          const isSelected = selectedDate === day.dateStr;
          const isToday = day.dateStr === todayStr;
          const hasPain = day.pain !== null;

          return (
            <button
              key={day.dateStr}
              onClick={() => {
                if (!day.future && day.inMonth) {
                  onSelectDate(day.dateStr);
                }
              }}
              disabled={day.future || !day.inMonth}
              aria-label={format(day.date, "d 'de' MMMM yyyy", { locale: es })}
              className={`
                relative flex flex-col items-center justify-center
                min-h-[44px] sm:h-10 rounded-lg transition-all duration-150
                ${!day.inMonth ? "opacity-20 cursor-default" : ""}
                ${day.future ? "opacity-20 cursor-default" : ""}
                ${day.inMonth && !day.future ? "cursor-pointer hover:bg-bg-tertiary" : ""}
                ${isSelected ? "ring-2 ring-accent-warning bg-bg-tertiary" : ""}
                ${isToday && !isSelected ? "bg-bg-primary" : ""}
              `}
            >
              <span
                className={`
                  font-body text-small tabular-nums
                  ${isSelected ? "text-text-primary font-semibold" : ""}
                  ${!isSelected && day.inMonth ? "text-text-secondary" : ""}
                  ${!day.inMonth ? "text-text-muted" : ""}
                `}
              >
                {format(day.date, "d")}
              </span>
              {hasPain && day.inMonth && (
                <span
                  className="absolute bottom-1 w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: getPainColor(day.pain!) }}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
});
