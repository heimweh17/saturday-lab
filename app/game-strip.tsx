"use client";
import {useEffect,useMemo,useState} from 'react';
import {ChevronRight} from 'lucide-react';
import type {Season,Team} from './types';
import {asset} from '@/lib/paths';
import {modelPredict} from '@/lib/model';
import {Logo} from './ui';

type Fixture={id:string;date:string;week:number;home:string;away:string;homeName:string;awayName:string;neutral:boolean;completed:boolean;status:string;fbs:boolean};
type Fixtures={games:Fixture[]};
type BoardGame=Fixture&{awayTeam:Team;homeTeam:Team;awayProbability:number|null};

const kickoff=(date:string)=>new Date(date).toLocaleString('en-US',{weekday:'short',hour:'numeric',minute:'2-digit',timeZone:'America/New_York'}).replace(',',' ·');

export function GameStrip({data,onOpenTeam,onOpenMatchup}:{data:Season;onOpenTeam:(id:string)=>void;onOpenMatchup:(id:string)=>void}){
  const [fixtures,setFixtures]=useState<Fixtures|null>(null);
  useEffect(()=>{const c=new AbortController();fetch(asset('/data/fixtures.json'),{signal:c.signal}).then(r=>r.json()).then(d=>setFixtures(d as Fixtures)).catch(()=>{});return()=>c.abort()},[]);
  const board=useMemo(()=>{
    if(!fixtures||data.season!==2026)return {week:null,games:[] as BoardGame[]};
    const latest=data.snapshots['99'],byId=new Map(latest.teams.map(t=>[t.id,t]));
    const future=fixtures.games.filter(g=>!g.completed&&g.fbs&&g.status==='STATUS_SCHEDULED'&&g.date>String(latest.through)&&byId.has(g.home)&&byId.has(g.away));
    const week=Math.min(...future.map(g=>g.week));
    const games=future.filter(g=>g.week===week).map(g=>{
      const awayTeam=byId.get(g.away)!,homeTeam=byId.get(g.home)!;
      const awayProbability=data.model&&awayTeam.modelState&&homeTeam.modelState?modelPredict(awayTeam.modelState,homeTeam.modelState,g.neutral?0:-1,data.model,g.date).probability:null;
      return {...g,awayTeam,homeTeam,awayProbability};
    }).sort((a,b)=>((a.awayTeam.modelRank??a.awayTeam.rank)+(a.homeTeam.modelRank??a.homeTeam.rank))-((b.awayTeam.modelRank??b.awayTeam.rank)+(b.homeTeam.modelRank??b.homeTeam.rank))).slice(0,7);
    return {week,games};
  },[fixtures,data]);
  if(!board.games.length)return null;
  return <section className="game-strip" aria-label={`Featured week ${board.week} games`}><div className="game-strip-label"><span>UP NEXT</span><strong>Week {board.week}</strong><small>Model preview</small></div><div className="game-strip-scroll">{board.games.map(g=>{
    const awayPct=g.awayProbability==null?null:Math.round(g.awayProbability*100),homePct=awayPct==null?null:100-awayPct;
    return <article className="ticker-game" key={g.id}><div className="ticker-time"><span>{kickoff(g.date)} ET</span><button onClick={()=>onOpenMatchup(g.awayTeam.id)}>Matchup <ChevronRight size={13}/></button></div><button className="ticker-team" onClick={()=>onOpenTeam(g.awayTeam.id)}><Logo team={g.awayTeam} size={25}/><strong><i>#{g.awayTeam.modelRank??g.awayTeam.rank}</i>{g.awayTeam.abbr}</strong><b>{awayPct??'—'}{awayPct!=null&&'%'}</b></button><button className="ticker-team" onClick={()=>onOpenTeam(g.homeTeam.id)}><Logo team={g.homeTeam} size={25}/><strong><i>#{g.homeTeam.modelRank??g.homeTeam.rank}</i>{g.homeTeam.abbr}</strong><b>{homePct??'—'}{homePct!=null&&'%'}</b></button>{awayPct!=null&&<div className="ticker-prob"><i style={{width:`${awayPct}%`,background:g.awayTeam.color}}/><i style={{width:`${homePct}%`,background:g.homeTeam.color}}/></div>}</article>})}</div></section>;
}
