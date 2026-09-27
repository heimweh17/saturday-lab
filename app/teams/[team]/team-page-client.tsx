"use client";
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import type {Manifest,Report,Season} from '@/app/types';
import {Scouting} from '@/app/scouting';
import {Picker,dateLabel,weekName} from '@/app/ui';
import {asset} from '@/lib/paths';
import {teamPath,teamSeasonPath} from '@/lib/routes';
import {fetchLiveFeed,type LiveFeed} from '@/lib/live-feed';

export function TeamPageClient({teamId,initialSeason,latestSeason,seasonRoutes,routePath}:{teamId:string;initialSeason:number;latestSeason:number;seasonRoutes:Record<string,string>;routePath:string}){
  const router=useRouter();
  const [manifest,setManifest]=useState<Manifest|null>(null),[report,setReport]=useState<Report|null>(null),[data,setData]=useState<Season|null>(null),[liveFeed,setLiveFeed]=useState<LiveFeed|null>(null),[week,setWeek]=useState('99'),[error,setError]=useState('');
  const season=String(initialSeason);
  useEffect(()=>{Promise.all([fetch(asset('/data/manifest.json')).then(r=>r.json()),fetch(asset('/data/report.json')).then(r=>r.json())]).then(([m,r])=>{setManifest(m as Manifest);setReport(r as Report)}).catch(()=>setError('Team data could not load.'))},[]);
  useEffect(()=>{const c=new AbortController();fetch(asset(`/data/${season}.json`),{signal:c.signal}).then(r=>r.json()).then(d=>{setData(d as Season);setWeek('99')}).catch(e=>{if(e.name!=='AbortError')setError('This season could not load.')});return()=>c.abort()},[season]);
  useEffect(()=>{if(Number(season)!==latestSeason)return;const c=new AbortController();fetchLiveFeed(Number(season),c.signal).then(setLiveFeed).catch(()=>{/* Temporary feed failures fall back to the weekly snapshot. */});return()=>c.abort()},[season,latestSeason]);
  const currentData=data?.season===Number(season)?data:null,snapshot=currentData?.snapshots[week],team=snapshot?.teams.find(t=>t.id===teamId);
  const availableSeasons=Object.keys(seasonRoutes).map(Number);
  return <main><div className="context-toolbar"><div className="context-pickers"><Picker label="Season" value={season} onChange={value=>{const path=seasonRoutes[value];if(path)router.push(path)}} options={(manifest?.seasons??availableSeasons).filter(y=>availableSeasons.includes(y)).slice().reverse().map(y=>({value:String(y),label:String(y)}))}/>{currentData&&<Picker label="Snapshot" value={week} onChange={setWeek} options={currentData.weeks.map(w=>({value:String(w),label:weekName(w)}))}/>}</div><div className="snapshot-note"><span className="small-rule"/>Results through <strong>{dateLabel(snapshot?.through??null)}</strong><span>Saved snapshot</span></div></div>{error?<div className="notice">{error}</div>:!currentData||!report||!snapshot?<div className="loading">Loading team report…</div>:!team?<section className="surface empty-state"><h1>Not in the {season} FBS field</h1><p>This team does not appear in the selected season. Choose another season above.</p></section>:<Scouting key={`${season}-${week}-${teamId}`} config={report.config} data={currentData} snapshot={snapshot} week={week} latestSeason={latestSeason} liveFeed={liveFeed?.season===currentData.season?liveFeed:null} routePath={routePath} selected={teamId} onSelect={id=>{const next=snapshot.teams.find(t=>t.id===id);if(next)router.push(Number(season)===latestSeason?teamPath(next):teamSeasonPath(next,Number(season)))}} onCompare={id=>router.push(`/matchup/?a=${id}`)}/>}</main>;
}
