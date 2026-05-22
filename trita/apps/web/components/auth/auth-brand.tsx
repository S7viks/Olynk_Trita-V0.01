export function AuthBrand() {
  return (
    <div className="flex flex-col items-center text-center">
      <div
        className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-card shadow-sm"
        aria-hidden
      >
        <span className="font-heading text-lg font-black tracking-tighter text-primary">O</span>
      </div>
      <p className="text-2xl font-black tracking-tighter text-olynk-navy">OLYNK</p>
      <p className="mt-0.5 text-[10px] font-bold uppercase tracking-[0.25em] text-primary">
        Trita · Third Observer
      </p>
    </div>
  );
}
