export default function AuthCallbackLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-mesh-cream px-4">
      <div className="max-w-sm text-center">
        <p className="text-[10px] font-black uppercase tracking-widest text-primary">
          Signing you in
        </p>
        <p className="mt-2 text-[13px] text-muted-foreground">
          Finishing Google sign-in and starting your workspace…
        </p>
      </div>
    </div>
  );
}
