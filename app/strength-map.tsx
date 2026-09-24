"use client";
import {useState} from 'react';
import {Expand} from 'lucide-react';
import type {Team} from './types';
import {Logo,signed,pct} from './ui';
import {Button} from '@/components/ui/button';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle,DialogTrigger} from '@/components/ui/dialog';

function Field({teams,onSelect,large=false}:{teams:Team[];onSelect:(id:string)=>void;large?:boolean}){
  const [activeId,setActiveId]=useState<string|null>(null);
  const active=teams.find(t=>t.id===activeId)??teams.find(t=>(t.modelRank??t.rank)===1)??teams[0];
  const width=large?960:720,height=large?610:480;
  const left=56,right=width-28,top=28,bottom=height-62;
  const x=(v:number)=>Math.max(left,Math.min(right,(left+right)/2+v/40*(right-left)/2));
  const y=(v:number)=>Math.max(top,Math.min(bottom,(top+bottom)/2-v/40*(bottom-top)/2));
  const ticks=[-30,-15,0,15,30];
  return <div className="strength-map-body">
    <svg viewBox={`0 0 ${width} ${height}`} className="strength-chart" role="img" aria-label="Interactive offense and defense map. Better offense is to the right and better defense is higher.">
      <rect x={left} y={top} width={right-left} height={bottom-top} fill="#eef4f7"/>
      <path d={`M${left} ${top}H${right}V${bottom}H${left}Z`} fill="none" stroke="#b9cad4"/>
      {ticks.map(n=><g key={n}><line x1={x(n)} x2={x(n)} y1={top} y2={bottom} stroke={n===0?'#8299a8':'#d2dfe5'} strokeDasharray={n===0?'0':'4 7'}/><line x1={left} x2={right} y1={y(n)} y2={y(n)} stroke={n===0?'#8299a8':'#d2dfe5'} strokeDasharray={n===0?'0':'4 7'}/><text x={x(n)} y={bottom+25} textAnchor="middle">{n>0?`+${n}`:n}</text><text x={left-10} y={y(n)+4} textAnchor="end">{n>0?`+${n}`:n}</text></g>)}
      <text x={right-10} y={top+22} textAnchor="end" className="quadrant">ELITE BOTH WAYS</text><text x={left+12} y={bottom-13} className="quadrant">BUILDING</text>
      {teams.slice().reverse().map(t=>{const rank=t.modelRank??t.rank,isActive=t.id===active?.id;return <g key={t.id} role="button" tabIndex={0} aria-label={`${t.short}, rank ${rank}, offense ${t.offense.toFixed(1)}, defense ${t.defense.toFixed(1)}. Open team report.`} onMouseEnter={()=>setActiveId(t.id)} onFocus={()=>setActiveId(t.id)} onClick={()=>onSelect(t.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(t.id)}}} className="plot-point">
        <circle cx={x(t.offense)} cy={y(t.defense)} r={isActive?12:rank<=10?7:4.2} fill={rank<=25?t.color:'#7893a2'} opacity={isActive?1:rank<=25?.88:.48} stroke="white" strokeWidth={isActive?3:1.4}/>
        {(isActive||rank<=5)&&<text x={x(t.offense)+11} y={y(t.defense)-9} className="point-label">{t.abbr}</text>}
      </g>})}
      <text x={(left+right)/2} y={height-13} textAnchor="middle" className="axis-label">Opponent-adjusted offense →</text>
      <text transform={`translate(16 ${(top+bottom)/2}) rotate(-90)`} textAnchor="middle" className="axis-label">Better defense →</text>
    </svg>
    {active&&<button className="map-team-readout" onClick={()=>onSelect(active.id)} aria-label={`Open ${active.name} team report`}>
      <Logo team={active} size={48}/><span><small>#{active.modelRank??active.rank} nationally</small><strong>{active.name}</strong><em>{active.wins}–{active.losses} · {active.conference.replace(' Conference','')}</em></span><dl><div><dt>Strength</dt><dd>{pct(active.winIndex)}</dd></div><div><dt>Offense</dt><dd>{signed(active.offense)}</dd></div><div><dt>Defense</dt><dd>{signed(active.defense)}</dd></div></dl>
    </button>}
  </div>;
}

export function StrengthMap({teams,onSelect}:{teams:Team[];onSelect:(id:string)=>void}){
  return <section className="strength-map-panel">
    <div className="panel-title"><div><h2>Offense × defense map</h2><p>Every dot is a team. Hover for its profile; select it for the full report.</p></div><Dialog><DialogTrigger asChild><Button variant="outline"><Expand size={16}/> Expand</Button></DialogTrigger><DialogContent className="strength-map-dialog" onOpenAutoFocus={e=>e.preventDefault()}><DialogHeader><DialogTitle>FBS offense × defense map</DialogTitle><DialogDescription>Opponent-adjusted points per game. Right and up are better.</DialogDescription></DialogHeader><Field teams={teams} onSelect={onSelect} large/></DialogContent></Dialog></div>
    <Field teams={teams} onSelect={onSelect}/>
  </section>;
}
