import type { Metadata } from "next";
import "./globals.css";
import {SiteHeader} from './site-header';

export const metadata: Metadata = {
  metadataBase: new URL("https://heimweh17.github.io/saturday-lab/"),
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
      <body className="antialiased"><div className="site-shell"><SiteHeader/>{children}<footer><span>Saturday Lab</span><p>Independent college football analytics. Not affiliated with the NCAA, ESPN or any university.</p><span>MODEL v6 · DATED SNAPSHOTS</span></footer></div></body>
    </html>
  );
}
