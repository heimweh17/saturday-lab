"use client";
import {useEffect,useMemo,useState} from 'react';
import Link from 'next/link';
import {ArrowRight,Search} from 'lucide-react';
import type {Season,Team} from '@/app/types';
import {asset} from '@/lib/paths';
import {teamPath} from '@/lib/routes';
import {Logo,pct} from '@/app/ui';

const featured=['87','194','333','61','251','130','57','30'];

function TeamCard({team}:{team:Team}){return <Link href={teamPath(team)} className="directory-team-card" style={{'--team-color':team.color} as React.CSSProperties}><Logo team={team} size={62}/><div><span>#{team.modelRank??team.rank} · {team.conference}</span><h2>{team.short}</h2><p>{team.wins}–{team.losses} · {pct(team.winIndex)} strength</p></div><ArrowRight/></Link>}

export function TeamDirectory(){
  const [data,setData]=useState<Season|null>(null),[query,setQuery]=useState(''),[error,setError]=useState(false);
  useEffect(()=>{const c=new AbortController();fetch(asset('/data/2026.json'),{signal:c.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(d=>setData(d as Season)).catch(e=>{if(e.name!=='AbortError')setError(true)});return()=>c.abort()},[]);
  const teams=useMemo(()=>data?.snapshots['99'].teams.slice().sort((a,b)=>a.name.localeCompare(b.name))??[],[data]);
  const results=useMemo(()=>{const q=query.trim().toLowerCase();return q?teams.filter(t=>`${t.name} ${t.short} ${t.abbr} ${t.conference}`.toLowerCase().includes(q)):[]},[query,teams]);
  const popular=featured.map(id=>teams.find(t=>t.id===id)).filter((t):t is Team=>Boolean(t));
  return <main><header className="route-intro"><span className="scoreline">TEAM DIRECTORY · 2026 FBS</span><h1>FIND YOUR TEAM</h1><p>Search by school, nickname, abbreviation or conference. Every result opens the team’s permanent report with rankings, schedule forecasts, results and detailed statistics.</p></header><section className="team-search-hero"><Search/><input autoFocus aria-label="Search teams" placeholder="Try Florida, Buckeyes, SEC…" value={query} onChange={e=>setQuery(e.target.value)}/><span>{query?`${results.length} matches`:`${teams.length||138} FBS teams`}</span></section>{error?<div className="notice">Team directory data could not load.</div>:!data?<div className="loading">Loading the team directory…</div>:query?<section><div className="directory-heading"><h2>Search results</h2><p>Select a team to open its full report.</p></div><div className="team-directory-grid">{results.map(team=><TeamCard key={team.id} team={team}/>)}</div>{!results.length&&<div className="surface empty-state"><h2>No team found</h2><p>Try a school name, nickname, abbreviation or conference.</p></div>}</section>:<><section><div className="directory-heading"><h2>Featured programs</h2><p>Quick access to frequently followed teams.</p></div><div className="team-directory-grid featured">{popular.map(team=><TeamCard key={team.id} team={team}/>)}</div></section><section><div className="directory-heading"><h2>All FBS teams</h2><p>Alphabetical directory.</p></div><div className="team-directory-grid compact">{teams.map(team=><TeamCard key={team.id} team={team}/>)}</div></section></>}</main>;
}
