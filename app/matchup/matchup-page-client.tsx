"use client";
import {useEffect,useState} from 'react';
import {useSearchParams} from 'next/navigation';
import type {Report,Season} from '@/app/types';
import {Matchup} from '@/app/matchup';
import {asset} from '@/lib/paths';
export function MatchupPageClient(){const query=useSearchParams(),[data,setData]=useState<Season|null>(null),[report,setReport]=useState<Report|null>(null);useEffect(()=>{Promise.all([fetch(asset('/data/2026.json')).then(r=>r.json()),fetch(asset('/data/report.json')).then(r=>r.json())]).then(([d,r])=>{setData(d as Season);setReport(r as Report)})},[]);if(!data||!report)return <main><div className="loading">Loading matchup lab…</div></main>;const snapshot=data.snapshots['99'],a=snapshot.teams.some(t=>t.id===query.get('a'))?query.get('a')!:'194',b=snapshot.teams.some(t=>t.id===query.get('b'))?query.get('b')!:a==='333'?'194':'333';return <main><div className="route-intro"><span className="scoreline">HYPOTHETICAL MATCHUP</span><h1>Matchup Lab</h1><p>Choose any two FBS teams and a venue. Scheduled games have their own game-center pages.</p></div><Matchup key={`${a}-${b}`} data={data} snapshot={snapshot} report={report} initial={a} initialB={b} initialVenue="neutral" week="99"/></main>}
