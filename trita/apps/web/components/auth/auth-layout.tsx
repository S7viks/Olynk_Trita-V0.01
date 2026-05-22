import { AuthBrand } from "@/components/auth/auth-brand";
import { AuthLegalFooter } from "@/components/auth/auth-legal-footer";
import { OrbitCard } from "@/components/orbit/card";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
  showLegal = true,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  showLegal?: boolean;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-mesh-cream px-4 py-10 sm:py-14">
      <div className="w-full max-w-[420px] animate-fade-in-up">
        <AuthBrand />
        <OrbitCard variant="glass-strong" className="mt-8 shadow-sm">
          <header className="border-b border-border/80 pb-5">
            <h1 className="font-heading text-xl font-black tracking-tight text-foreground">
              {title}
            </h1>
            {subtitle ? (
              <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">{subtitle}</p>
            ) : null}
          </header>
          <div className="pt-6">{children}</div>
          {footer ? <div className="mt-6 border-t border-border/80 pt-5">{footer}</div> : null}
        </OrbitCard>
        {showLegal ? (
          <div className="mt-6 px-2">
            <AuthLegalFooter />
          </div>
        ) : null}
        <p className="mt-4 text-center text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground/80">
          Inventory intelligence for Indian D2C
        </p>
      </div>
    </div>
  );
}
