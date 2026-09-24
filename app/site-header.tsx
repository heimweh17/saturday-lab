"use client";
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ArrowUpRight} from 'lucide-react';

const items=[['/','Rankings'],['/teams/','Find a team'],['/matchup/','Matchup Lab'],['/rank-trends/','Rank trends'],['/model/','Model'],['/methodology/','Methodology']];

export function SiteHeader(){
  const pathname=usePathname();
  return <><header className="masthead"><Link className="brand" href="/" aria-label="Saturday Lab home"><span className="brand-mark">SL</span><span>Saturday Lab<small>COLLEGE FOOTBALL DATA</small></span></Link><div className="masthead-note"><span>THE 2026 SEASON</span><strong>Every team. Every week. One field.</strong></div><a className="source-link" href="https://github.com/heimweh17/saturday-lab" target="_blank" rel="noreferrer">The project <ArrowUpRight size={16}/></a></header><div className="nav-wrap"><nav className="main-nav route-nav" aria-label="Primary navigation">{items.map(([href,label])=><Link key={href} href={href} className={pathname===href||href!=='/'&&pathname.startsWith(href)?'active':''}>{label}</Link>)}<span className="nav-divider" aria-hidden="true"/><Link href="/legal/" className={pathname.startsWith('/legal')?'active secondary-nav':'secondary-nav'}>Sources &amp; legal</Link></nav><span className="nav-meta">MODEL v6</span></div></>;
}
