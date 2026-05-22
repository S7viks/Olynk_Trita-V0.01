/** Server route starts OAuth so PKCE verifier is stored in cookies (not localStorage). */
export function googleSignInPath(nextPath = "/onboarding"): string {
  return `/auth/google?next=${encodeURIComponent(nextPath)}`;
}

/** Navigate to server OAuth handler — same origin as the page (localhost vs 127.0.0.1 matters). */
export function startGoogleSignIn(nextPath = "/onboarding"): void {
  window.location.assign(googleSignInPath(nextPath));
}
