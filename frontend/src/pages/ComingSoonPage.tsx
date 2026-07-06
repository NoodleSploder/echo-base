export function ComingSoonPage({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="flex h-full min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="mb-2 h-2.5 w-2.5 rounded-full bg-accent-400 shadow shadow-accent-400/50" />
      <h1 className="text-lg font-semibold text-slate-100">{title}</h1>
      <p className="mt-1 max-w-md text-sm text-slate-500">
        Not implemented yet -- see <span className="text-slate-300">{phase}</span> in ROADMAP.md. The Dashboard page
        shows what this section's panels will eventually look like, using sample data.
      </p>
    </div>
  );
}
