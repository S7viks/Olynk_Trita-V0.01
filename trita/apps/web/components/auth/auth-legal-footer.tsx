export function AuthLegalFooter() {
  return (
    <p className="text-center text-[11px] leading-relaxed text-muted-foreground">
      By continuing, you agree to OLynk&apos;s{" "}
      <a
        href="https://olynk.ai/terms"
        className="font-medium text-primary underline-offset-2 hover:underline"
        target="_blank"
        rel="noopener noreferrer"
      >
        Terms
      </a>{" "}
      and{" "}
      <a
        href="https://olynk.ai/privacy"
        className="font-medium text-primary underline-offset-2 hover:underline"
        target="_blank"
        rel="noopener noreferrer"
      >
        Privacy Policy
      </a>
      .
    </p>
  );
}
