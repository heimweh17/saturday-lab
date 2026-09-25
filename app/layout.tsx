import type { Metadata } from "next";
import Link from "next/link";
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
      <body className="antialiased"><div className="site-shell"><SiteHeader/>{children}<footer className="site-footer"><div className="footer-brand"><strong>Saturday Lab</strong><p>Independent college football rankings, scores and matchup analysis.</p><span>Model v6 · Dated snapshots</span></div><nav aria-label="Explore Saturday Lab"><strong>Explore</strong><Link href="/">Rankings</Link><Link href="/teams/">Teams</Link><Link href="/games/">Scores &amp; schedule</Link><Link href="/matchup/">Matchup Lab</Link></nav><nav aria-label="Project information"><strong>About the data</strong><Link href="/model/">Model performance</Link><Link href="/methodology/">Methodology</Link><Link href="/legal/">Sources &amp; legal</Link><a href="https://github.com/heimweh17/saturday-lab" target="_blank" rel="noreferrer">GitHub source</a></nav><p className="footer-legal">Team names and marks belong to their respective owners. Saturday Lab is not affiliated with ESPN, the NCAA or any university.</p></footer></div></body>
    </html>
  );
}
