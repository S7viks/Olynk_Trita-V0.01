import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trita",
  description: "Third Observer — OLynk inventory intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
