"use client";
import {useState} from 'react';
import type {Season} from './types';
import {dateLabel,download,signed} from './ui';
import {Button} from '@/components/ui/button';

export function RankHistory({data,teamId,week}:{data:Season;teamId:string;week:string}){
  const [fullScale,setFullScale]=useState(false);
  const [hovered,setHovered]=useState<number|null>(null);
  const cutoff=data.weeks.indexOf(Number(week));
  const points=data.weeks.slice(0,cutoff+1).flatMap((w,i)=>{
    const snapshot=data.snapshots[String(w)];
    const team=snapshot.teams.find(t=>t.id===teamId);
    if(!team)return [];
    const priorWeek=i?data.weeks[i-1]:null;
    return [{label:priorWeek===null?'Preseason':priorWeek>=30?`After postseason ${priorWeek-30}`:`After week ${priorWeek}`,short:priorWeek===null?'Pre':priorWeek>=30?`Post ${priorWeek-30}`:`W${priorWeek}`,rank:team.modelRank??team.rank,through:snapshot.through,teams:snapshot.teams.length}];
  });
  if(!points.length)return null;
  const explanation=data.snapshots[week]?.teams.find(t=>t.id===teamId)?.ratingExplanation;
  const last=points[points.length-1],first=points[0],change=first.rank-last.rank;
  const active=points[Math.min(hovered??points.length-1,points.length-1)];
  const total=Math.max(...points.map(p=>p.teams));
  const x=(i:number)=>64+i/Math.max(1,points.length-1)*660;
  const low=fullScale?1:Math.max(1,Math.floor((Math.min(...points.map(p=>p.rank))-5)/5)*5);
  const high=fullScale?total:Math.min(total,Math.max(low+15,Math.ceil((Math.max(...points.map(p=>p.rank))+5)/5)*5));
  const y=(rank:number)=>38+(rank-low)/Math.max(1,high-low)*214;
  const step=high-low>60?25:high-low>30?10:5;
  const ticks=[low,...Array.from({length:Math.ceil(high/step)},(_,i)=>(i+1)*step).filter(n=>n>low+2&&n<high-2),high];
  return <section className="surface rank-history">
    <div className="panel-title"><div><h2>Season ranking history</h2><p className="subcopy">{data.season} national model rank after each completed week. Higher on the chart means a stronger ranking.</p></div><Button variant="outline" onClick={()=>download(`rank-history-${teamId}-${data.season}.csv`,points)}>Export ranking history</Button></div>
    <div className="rank-history-summary"><strong>#{last.rank}<small>{last.label}</small></strong><p>{change===0?'Unchanged':`${Math.abs(change)} ${Math.abs(change)===1?'place':'places'} ${change>0?'up':'down'}`} from preseason <span>#{first.rank}</span></p></div>
    <label className="rank-scale"><input type="checkbox" checked={fullScale} onChange={e=>setFullScale(e.target.checked)}/> Show all {total} ranks</label><div className="rank-chart-scroll"><svg viewBox="0 0 780 305" className="rank-chart" style={{minWidth:points.length>8?560:undefined}} role="group" aria-label="Weekly national ranking. Rank one is at the top. Focus a point for its exact rank.">
      {ticks.map(n=><g key={n}><line x1="64" x2="724" y1={y(n)} y2={y(n)} stroke="#dce5eb"/><text x="49" y={y(n)+4} textAnchor="end">#{n}</text></g>)}
      <polyline points={points.map((p,i)=>`${x(i)},${y(p.rank)}`).join(' ')} fill="none" stroke="#1768ac" strokeWidth="3"/>
      {points.map((p,i)=><g key={p.label} tabIndex={0} role="img" aria-label={`${p.label}: rank ${p.rank} of ${p.teams}; results through ${dateLabel(p.through)}`} onFocus={()=>setHovered(i)} onBlur={()=>setHovered(null)} onMouseEnter={()=>setHovered(i)} onMouseLeave={()=>setHovered(null)} onClick={()=>setHovered(i)}>
        <circle cx={x(i)} cy={y(p.rank)} r="13" fill="transparent"/>
        <circle cx={x(i)} cy={y(p.rank)} r={active===p?6:4} fill="#1768ac" stroke="white" strokeWidth="2"/>
        <title>{p.label}: #{p.rank}</title>
        {(points.length<=10||i%2===0||i===points.length-1)&&<text x={x(i)} y="281" textAnchor="middle">{p.short}</text>}
      </g>)}
    </svg></div>
    <p className="rank-point-readout" aria-live="polite"><strong>{active.label}: #{active.rank}</strong> of {active.teams} FBS teams <span>Results through {dateLabel(active.through)}</span></p>
    <p className="fine-print">This is Saturday Lab’s ranking, not the AP poll or ESPN FPI. Each point uses only results available at that time. A bye week can still change a team’s rank as other teams play.{data.season<2023?' This archived season uses the exploratory scoring model.':''}</p>
    {explanation&&<details className="rank-values"><summary>Why did this ranking change?</summary><p className="subcopy">Previous rank #{explanation.previousRank}; now #{last.rank}. Rank is relative to the whole FBS field.</p><dl className="stat-list"><div><dt>This team’s update, holding the previous field fixed</dt><dd>{signed(explanation.ownIndexChange*100,2)} percentage points</dd></div><div><dt>Then updating the rest of the field</dt><dd>{signed(explanation.fieldIndexChange*100,2)} percentage points</dd></div></dl><p className="fine-print">These two steps add up to the change in the strength index. A team can improve while its rank falls if other teams improve more. This decomposition is descriptive, not a causal estimate.</p><details><summary>Strength components</summary><dl className="stat-list">{explanation.drivers.map(d=><div key={d.label}><dt>{d.label}</dt><dd>{signed(d.logOddsChange,3)}</dd></div>)}</dl><p className="fine-print">Changes in model log odds, not points scored. Opponent adjustment can revise a team’s strength even during a bye.</p></details></details>}
    <details className="rank-values"><summary>View exact weekly rankings</summary><table><thead><tr><th>Week completed</th><th>Rank</th><th>Results through</th></tr></thead><tbody>{points.map(p=><tr key={p.label}><td>{p.label}</td><td>#{p.rank}</td><td>{dateLabel(p.through)}</td></tr>)}</tbody></table></details>
  </section>;
}
