"use client";

import { useState } from "react";
import { NavBar } from "@/components/nav-bar";
import { CalendarView } from "@/components/calendar-view";
import { DailyDetail } from "@/components/daily-detail";
import { useEntries, useEntry } from "@/hooks/use-entries";
import { EmptyState } from "@/components/empty-state";

export default function HistoryPage() {
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const { data: entries } = useEntries({ limit: 90 });
  const { data: selectedEntry, isLoading: isEntryLoading } = useEntry(
    selectedDate ?? "",
  );

  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="font-display text-h1 font-semibold text-text-primary">
            Historial
          </h1>
        </div>

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
      </main>
    </div>
  );
}
