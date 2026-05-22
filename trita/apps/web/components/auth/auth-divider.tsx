export function AuthDivider({ label = "or" }: { label?: string }) {
  return (
    <div className="relative py-1">
      <div className="absolute inset-x-0 top-1/2 h-px bg-border" aria-hidden />
      <p className="relative mx-auto w-fit bg-card px-3 text-[10px] font-black uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
    </div>
  );
}
