"use client";
import {ArrowDown,ArrowUp} from 'lucide-react';
import type {Team} from './types';
import {Logo} from './ui';

export function SnapshotPulse({teams,onSelect,onTrends}:{teams:Team[];onSelect:(id:string)=>void;onTrends:()=>void}){
  const withMoves=teams.filter(t=>(t.modelChange??t.change)!==0);
  const risers=withMoves.filter(t=>(t.modelChange??t.change)>0).sort((a,b)=>(b.modelChange??b.change)-(a.modelChange??a.change)).slice(0,4);
  const fallers=withMoves.filter(t=>(t.modelChange??t.change)<0).sort((a,b)=>(a.modelChange??a.change)-(b.modelChange??b.change)).slice(0,4);
  const items=[
    ...risers.map(team=>({team,label:'Moved up',value:`+${team.modelChange??team.change} spots`,icon:ArrowUp,tone:'up'})),
    ...fallers.map(team=>({team,label:'Moved down',value:`${team.modelChange??team.change} spots`,icon:ArrowDown,tone:'down'})),
  ];
  return <section className="snapshot-pulse"><div className="pulse-head"><div><span>AROUND THE RANKINGS</span><h2>What moved this week</h2></div><button onClick={onTrends}>See every trend →</button></div><div className="pulse-grid">{items.map(({team,label,value,icon:Icon,tone})=><button key={`${label}-${team.id}`} className={`pulse-item ${tone}`} onClick={()=>onSelect(team.id)}><Icon size={16}/><Logo team={team} size={34}/><span><small>{label}</small><strong>{team.short}</strong><em>{value} · now #{team.modelRank??team.rank}</em></span></button>)}</div></section>;
}
