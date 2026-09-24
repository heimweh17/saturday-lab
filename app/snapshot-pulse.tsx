"use client";
import {ArrowDown,ArrowUp,Shield,TrendingUp} from 'lucide-react';
import type {Team} from './types';
import {Logo,signed} from './ui';

export function SnapshotPulse({teams,onSelect,onTrends}:{teams:Team[];onSelect:(id:string)=>void;onTrends:()=>void}){
  const withMoves=teams.filter(t=>(t.modelChange??t.change)!==0);
  const riser=withMoves.slice().sort((a,b)=>(b.modelChange??b.change)-(a.modelChange??a.change))[0];
  const faller=withMoves.slice().sort((a,b)=>(a.modelChange??a.change)-(b.modelChange??b.change))[0];
  const offense=teams.slice().sort((a,b)=>b.offense-a.offense)[0];
  const defense=teams.slice().sort((a,b)=>b.defense-a.defense)[0];
  const items=[
    {team:riser,label:'Biggest riser',value:`+${riser?.modelChange??riser?.change} spots`,icon:ArrowUp,tone:'up'},
    {team:faller,label:'Biggest slide',value:`${faller?.modelChange??faller?.change} spots`,icon:ArrowDown,tone:'down'},
    {team:offense,label:'Best offense',value:`${signed(offense?.offense)} adj. pts`,icon:TrendingUp,tone:'offense'},
    {team:defense,label:'Best defense',value:`${signed(defense?.defense)} adj. pts`,icon:Shield,tone:'defense'},
  ].filter(x=>x.team) as {team:Team;label:string;value:string;icon:typeof ArrowUp;tone:string}[];
  return <section className="snapshot-pulse"><div className="pulse-head"><div><span>AROUND THE RANKINGS</span><h2>What moved this week</h2></div><button onClick={onTrends}>See every trend →</button></div><div className="pulse-grid">{items.map(({team,label,value,icon:Icon,tone})=><button key={label} className={`pulse-item ${tone}`} onClick={()=>onSelect(team.id)}><Icon size={16}/><Logo team={team} size={34}/><span><small>{label}</small><strong>{team.short}</strong><em>{value} · now #{team.modelRank??team.rank}</em></span></button>)}</div></section>;
}
