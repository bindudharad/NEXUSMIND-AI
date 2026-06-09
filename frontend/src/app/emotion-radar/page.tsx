import { CompanyEmotionMapPanel } from "@/components/dashboard/CompanyEmotionMapPanel";

export default function EmotionRadarPage() {
  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <CompanyEmotionMapPanel />
      </div>
    </main>
  );
}
