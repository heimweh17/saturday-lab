import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Saturday Lab | College Football Analytics",
  description: "Explore NCAA football power ratings, compare teams and inspect honest, week-forward historical backtests.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
