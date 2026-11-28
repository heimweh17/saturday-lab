"use client";
import Link from 'next/link';
import {usePathname} from 'next/navigation';
import {ChevronRight} from 'lucide-react';

const items=[['/','Rankings'],['/games/','Scores'],['/teams/','Teams'],['/matchup/','Compare'],['/rank-trends/','Trends']];

export function SiteHeader(){
  const pathname=usePathname();
  return <><header className="masthead"><Link className="brand" href="/" aria-label="Saturday Lab home"><span className="brand-mark">SL</span><span>Saturday Lab<small>COLLEGE FOOTBALL DATA</small></span></Link><Link className="source-link" href="/introduction/">About <ChevronRight size={16}/></Link></header><div className="nav-wrap"><nav className="main-nav route-nav" aria-label="Primary navigation">{items.map(([href,label])=>{const active=label==='Rankings'?(pathname==='/'||pathname.startsWith('/rankings')):pathname===href||pathname.startsWith(href);return <Link key={href} href={href} className={active?'active':''} aria-current={active?'page':undefined}>{label}</Link>})}</nav></div></>;
}
