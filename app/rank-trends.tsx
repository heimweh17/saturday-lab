"use client";
import {useMemo,useState} from 'react';
import type {CSSProperties,MouseEvent} from 'react';
import {Expand,Plus,X} from 'lucide-react';
import type {Season,Team} from './types';
import {Logo,dateLabel,weekName,download} from './ui';
import {Button} from '@/components/ui/button';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle,DialogTrigger} from '@/components/ui/dialog';

const colors=['#d94f2b','#1768ac','#25836f','#8a5bb5','#d29a24','#2f4858','#d36b9a','#5979c7','#8b6f47','#4e969e','#8f4c3f','#667a2f'];
type Point={i:number;week:number;rank:number;through:string|null}|null;
type Series={team:Team;color:string;points:Point[]};

function TrendChart({series,weeks,count,activeIndex,setHovered,onOpenTeam,large=false}:{series:Series[];weeks:number[];count:number;activeIndex:number;setHovered:(v:number|null)=>void;onOpenTeam:(id:string)=>void;large?:boolean}){
  const width=large?1440:1120,height=large?680:520,left=68,right=width-80,top=35,bottom=height-82;
  const x=(i:number)=>left+i/Math.max(1,weeks.length-1)*(right-left),y=(rank:number)=>top+(rank-1)/Math.max(1,count-1)*(bottom-top);
  const ticks=[1,10,25,50,75,100,count].filter((n,i,a)=>n<=count&&a.indexOf(n)===i);
  const move=(e:MouseEvent<SVGSVGElement>)=>{const r=e.currentTarget.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*width,index=Math.round((px-left)/(right-left)*Math.max(1,weeks.length-1));setHovered(Math.max(0,Math.min(weeks.length-1,index)))};
  return <><div className="comparison-chart-scroll"><svg viewBox={`0 0 ${width} ${height}`} className="comparison-rank-chart" onMouseLeave={()=>setHovered(null)} onMouseMove={move} role="img" aria-label={`Ranking history for ${series.map(s=>s.team.name).join(', ')}`}>
    {ticks.map(n=><g key={n}><line x1={left} x2={right} y1={y(n)} y2={y(n)} stroke="#d7e2e8" strokeDasharray={n===1?'0':'4 7'}/><text x={left-13} y={y(n)+4} textAnchor="end">#{n}</text></g>)}
    {weeks.map((w,i)=><g key={w}><line x1={x(i)} x2={x(i)} y1={top} y2={bottom} stroke={i===activeIndex?'#7f909a':'transparent'} strokeWidth="1.5"/><text x={x(i)} y={bottom+31} textAnchor="middle">{weekName(w).replace('Before ','')}</text></g>)}
    {series.map(s=>{const points=s.points.filter(Boolean) as Exclude<Point,null>[];return <g key={s.team.id}><polyline points={points.map(p=>`${x(p.i)},${y(p.rank)}`).join(' ')} fill="none" stroke="white" strokeWidth="8" opacity=".9"/><polyline points={points.map(p=>`${x(p.i)},${y(p.rank)}`).join(' ')} fill="none" stroke={s.color} strokeWidth="4"/>{points.map(p=><circle key={p.i} cx={x(p.i)} cy={y(p.rank)} r={p.i===activeIndex?7:4} fill={s.color} stroke="white" strokeWidth="2"/>)}</g>})}
  </svg></div><div className="trend-scoreboard" aria-live="polite">{series.slice().sort((a,b)=>(a.points[activeIndex]?.rank??999)-(b.points[activeIndex]?.rank??999)).map(s=>{const p=s.points[activeIndex];return p&&<button key={s.team.id} onClick={()=>onOpenTeam(s.team.id)}><i style={{background:s.color}}/><Logo team={s.team} size={30}/><span><strong>#{p.rank} {s.team.short}</strong><small>Through {dateLabel(p.through)}</small></span></button>})}</div></>;
}

export function RankTrends({data,onOpenTeam}:{data:Season;onOpenTeam:(id:string)=>void}){
  const latest=data.snapshots['99']??data.snapshots[String(data.weeks.at(-1))],ordered=latest.teams.slice().sort((a,b)=>(a.modelRank??a.rank)-(b.modelRank??b.rank));
  const [selected,setSelected]=useState(()=>ordered.slice(0,4).map(t=>t.id));
  const [addId,setAddId]=useState(()=>ordered.find(t=>!selected.includes(t.id))?.id??'');
  const [hovered,setHovered]=useState<number|null>(null),weeks=data.weeks;
  const series=useMemo(()=>selected.map((id,index)=>({team:ordered.find(t=>t.id===id)!,color:colors[index%colors.length],points:weeks.map((week,i)=>{const snap=data.snapshots[String(week)],team=snap?.teams.find(t=>t.id===id);return team?{i,week,rank:team.modelRank??team.rank,through:snap.through}:null})})).filter(x=>x.team),[selected,ordered,weeks,data.snapshots]);
  const activeIndex=Math.min(hovered??weeks.length-1,weeks.length-1),count=Math.max(1,latest.teams.length);
  const add=()=>{if(addId&&!selected.includes(addId)){setSelected([...selected,addId]);setAddId(ordered.find(t=>!selected.includes(t.id)&&t.id!==addId)?.id??'')}};
  const exportRows=weeks.flatMap((w,i)=>series.map(s=>{const p=s.points[i];return p?{season:data.season,week:weekName(w),team:s.team.name,rank:p.rank,resultsThrough:p.through}:null}).filter(Boolean)) as object[];
  const chartProps={series,weeks,count,activeIndex,setHovered,onOpenTeam};
  return <div className="trend-workspace"><div className="section-heading trend-heading"><div><span className="scoreline">WEEK-BY-WEEK MOVEMENT</span><h1>Race across the season</h1><p>Put teams on the same field and watch the national order change after every Saturday.</p></div><Button variant="outline" onClick={()=>download(`rank-trends-${data.season}.csv`,exportRows)}>Export chart data</Button></div>
    <section className="surface trend-controls"><div><label htmlFor="trend-add">Add a team</label><select id="trend-add" value={addId} onChange={e=>setAddId(e.target.value)}>{ordered.filter(t=>!selected.includes(t.id)).map(t=><option key={t.id} value={t.id}>{t.short}</option>)}</select><Button onClick={add} disabled={!addId||selected.length>=12}><Plus size={16}/> Add</Button></div><p>{selected.length}/12 teams shown. Remove a team below to make room.</p><div className="team-chip-row">{series.map(s=><button key={s.team.id} className="team-chip" style={{'--team-line':s.color} as CSSProperties} onClick={()=>setSelected(selected.filter(id=>id!==s.team.id))} aria-label={`Remove ${s.team.name}`}><Logo team={s.team} size={25}/><span>{s.team.short}</span><X size={14}/></button>)}</div></section>
    <section className="surface comparison-chart-panel"><div className="panel-title"><div><h2>{data.season} national rank</h2><p className="subcopy">Rank 1 is at the top. Every point uses only results available at that snapshot.</p></div><div className="trend-chart-actions"><strong>{weekName(weeks[activeIndex])}</strong><Dialog><DialogTrigger asChild><Button variant="outline"><Expand size={16}/> Expand chart</Button></DialogTrigger><DialogContent className="trend-dialog" onOpenAutoFocus={e=>e.preventDefault()}><DialogHeader><DialogTitle>{data.season} national ranking race</DialogTitle><DialogDescription>Move across the chart to inspect every saved week.</DialogDescription></DialogHeader><TrendChart {...chartProps} large/></DialogContent></Dialog></div></div><TrendChart {...chartProps}/></section>
  </div>;
}
