import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Saturday Lab | College Football Analytics",
  description: "Explore opponent-adjusted NCAA football rankings, team data, matchup probabilities and transparent historical validation.",
  icons: {
    icon: `${process.env.NEXT_PUBLIC_BASE_PATH??''}/favicon.svg`,
    shortcut: `${process.env.NEXT_PUBLIC_BASE_PATH??''}/favicon.svg`,
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
