import { NavBar } from "@/components/nav-bar";

export default function AnalysisPage() {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <NavBar />
      <main className="max-w-6xl mx-auto px-6 py-8">
        <h1 className="font-display text-h1 font-semibold">Analysis</h1>
        <p className="text-text-secondary mt-2 font-body text-body">
          Correlation exploration — coming in Phase 5
        </p>
      </main>
    </div>
  );
}
