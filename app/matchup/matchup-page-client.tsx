"use client";
import {useCallback,useEffect,useState} from 'react';
import {useSearchParams} from 'next/navigation';
import type {Report,Season} from '@/app/types';
import {Matchup} from '@/app/matchup';
import {asset} from '@/lib/paths';

type Defaults={a:string;b:string;venue:'a'|'b'|'neutral';label:string};
const storageKey='saturday-lab-matchup';

export function MatchupPageClient(){
  const query=useSearchParams(),[data,setData]=useState<Season|null>(null),[report,setReport]=useState<Report|null>(null),[defaults,setDefaults]=useState<Defaults|null>(null);
  const remember=useCallback((a:string,b:string,venue:'a'|'b'|'neutral')=>{if(b!=='__choose__')localStorage.setItem(storageKey,JSON.stringify({a,b,venue}))},[]);
  useEffect(()=>{Promise.all([fetch(asset('/data/2026.json')).then(r=>r.json()),fetch(asset('/data/report.json')).then(r=>r.json())]).then(([rawData,rawReport])=>{
    const season=rawData as Season,snapshot=season.snapshots['99'],valid=(id:string|null)=>Boolean(id&&snapshot.teams.some(t=>t.id===id)),qa=query.get('a'),qb=query.get('b'),qv=query.get('venue'),venue=qv==='a'||qv==='b'?qv:'neutral';
    const ranked=snapshot.teams.slice().sort((x,y)=>(x.modelRank??x.rank)-(y.modelRank??y.rank));let next:Defaults;
    if(valid(qa))next={a:qa!,b:valid(qb)&&qb!==qa?qb!:'__choose__',venue,label:valid(qb)&&qb!==qa?'Linked comparison':'Choose an opponent'};
    else{
      let saved:Partial<Defaults>|null=null;try{saved=JSON.parse(localStorage.getItem(storageKey)??'null') as Partial<Defaults>|null}catch{}
      if(valid(saved?.a??null)&&valid(saved?.b??null)&&saved?.a!==saved?.b)next={a:saved!.a!,b:saved!.b!,venue:saved?.venue==='a'||saved?.venue==='b'?saved.venue:'neutral',label:'Last comparison'};
      else next={a:ranked[0].id,b:ranked[1].id,venue:'neutral',label:'Featured · current top two'};
    }
    setData(season);setReport(rawReport as Report);setDefaults(next);
  })},[query]);
  if(!data||!report||!defaults)return <main><div className="loading">Loading matchup lab…</div></main>;
  const snapshot=data.snapshots['99'];
  return <main><div className="route-intro"><span className="scoreline">HYPOTHETICAL MATCHUP · {defaults.label}</span><h1>Matchup Lab</h1><p>Choose any two FBS teams and a venue. Scheduled games have their own game-center pages.</p></div><Matchup key={`${defaults.a}-${defaults.b}-${defaults.venue}`} data={data} snapshot={snapshot} report={report} initial={defaults.a} initialB={defaults.b} initialVenue={defaults.venue} week="99" onSelectionChange={remember}/></main>;
}
