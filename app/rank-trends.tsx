"use client";
import {useMemo,useState} from 'react';
import type {CSSProperties,MouseEvent,WheelEvent} from 'react';
import {Expand,Plus,X,ScanLine} from 'lucide-react';
import type {Season,Team} from './types';
import {Logo,dateLabel,weekName,download,Picker} from './ui';
import {Button} from '@/components/ui/button';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle,DialogTrigger} from '@/components/ui/dialog';

const colors=['#d94f2b','#1768ac','#25836f','#8a5bb5','#d29a24','#2f4858','#d36b9a','#5979c7','#8b6f47','#4e969e','#8f4c3f','#667a2f'];
type Point={i:number;week:number;rank:number;through:string|null}|null;
type Series={team:Team;color:string;points:Point[]};

function TrendChart({series,weeks,low,high,activeIndex,setHovered,onOpenTeam,onZoom,large=false}:{series:Series[];weeks:number[];low:number;high:number;activeIndex:number;setHovered:(v:number|null)=>void;onOpenTeam:(id:string)=>void;onZoom:(direction:number)=>void;large?:boolean}){
  const width=large?1440:1120,height=large?680:520,left=68,right=width-80,top=35,bottom=height-82;
  const x=(i:number)=>left+i/Math.max(1,weeks.length-1)*(right-left),y=(rank:number)=>top+(rank-low)/Math.max(1,high-low)*(bottom-top);
  const ticks=Array.from(new Set(Array.from({length:6},(_,i)=>Math.round(low+(high-low)*i/5))));
  const move=(e:MouseEvent<SVGSVGElement>)=>{const r=e.currentTarget.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*width,index=Math.round((px-left)/(right-left)*Math.max(1,weeks.length-1));setHovered(Math.max(0,Math.min(weeks.length-1,index)))};
  const wheel=(e:WheelEvent<SVGSVGElement>)=>{if(!e.ctrlKey)return;e.preventDefault();onZoom(e.deltaY>0?-1:1)};
  return <><div className="comparison-chart-scroll"><svg viewBox={`0 0 ${width} ${height}`} className="comparison-rank-chart" onMouseLeave={()=>setHovered(null)} onMouseMove={move} onWheel={wheel} role="img" aria-label={`Ranking history for ${series.map(s=>s.team.name).join(', ')}`}>
    {ticks.map(n=><g key={n}><line x1={left} x2={right} y1={y(n)} y2={y(n)} stroke="#d7e2e8" strokeDasharray={n===1?'0':'4 7'}/><text x={left-13} y={y(n)+4} textAnchor="end">#{n}</text></g>)}
    {weeks.map((w,i)=><g key={w}><line x1={x(i)} x2={x(i)} y1={top} y2={bottom} stroke={i===activeIndex?'#7f909a':'transparent'} strokeWidth="1.5"/><text x={x(i)} y={bottom+31} textAnchor="middle">{weekName(w).replace('Before ','')}</text></g>)}
    {series.map(s=>{const points=s.points.filter(Boolean) as Exclude<Point,null>[];return <g key={s.team.id}><polyline points={points.map(p=>`${x(p.i)},${y(p.rank)}`).join(' ')} fill="none" stroke="white" strokeWidth="8" opacity=".9"/><polyline points={points.map(p=>`${x(p.i)},${y(p.rank)}`).join(' ')} fill="none" stroke={s.color} strokeWidth="4"/>{points.map(p=><circle key={p.i} cx={x(p.i)} cy={y(p.rank)} r={p.i===activeIndex?7:4} fill={s.color} stroke="white" strokeWidth="2"/>)}</g>})}
  </svg></div><div className="trend-scoreboard" aria-live="polite">{series.slice().sort((a,b)=>(a.points[activeIndex]?.rank??999)-(b.points[activeIndex]?.rank??999)).map(s=>{const p=s.points[activeIndex];return p&&<button key={s.team.id} onClick={()=>onOpenTeam(s.team.id)}><i style={{background:s.color}}/><Logo team={s.team} size={30}/><span><strong>#{p.rank} {s.team.short}</strong><small>Through {dateLabel(p.through)}</small></span></button>})}</div></>;
}

export function RankTrends({data,onOpenTeam}:{data:Season;onOpenTeam:(id:string)=>void}){
  const latest=data.snapshots['99']??data.snapshots[String(data.weeks.at(-1))],ordered=latest.teams.slice().sort((a,b)=>(a.modelRank??a.rank)-(b.modelRank??b.rank));
  const alphabetical=latest.teams.slice().sort((a,b)=>a.name.localeCompare(b.name));
  const [selected,setSelected]=useState(()=>ordered.slice(0,4).map(t=>t.id));
  const [addId,setAddId]=useState(()=>alphabetical.find(t=>!selected.includes(t.id))?.id??'');
  const [hovered,setHovered]=useState<number|null>(null),weeks=data.weeks;
  const [scaleMode,setScaleMode]=useState<'auto'|'all'>('auto'),[zoom,setZoom]=useState(1);
  const series=useMemo(()=>selected.map((id,index)=>({team:ordered.find(t=>t.id===id)!,color:colors[index%colors.length],points:weeks.map((week,i)=>{const snap=data.snapshots[String(week)],team=snap?.teams.find(t=>t.id===id);return team?{i,week,rank:team.modelRank??team.rank,through:snap.through}:null})})).filter(x=>x.team),[selected,ordered,weeks,data.snapshots]);
  const activeIndex=Math.min(hovered??weeks.length-1,weeks.length-1),count=Math.max(1,latest.teams.length);
  const ranks=series.flatMap(s=>s.points.flatMap(p=>p?[p.rank]:[])),fitLow=Math.max(1,(ranks.length?Math.min(...ranks):1)-4),fitHigh=Math.min(count,(ranks.length?Math.max(...ranks):10)+4);
  const baseLow=scaleMode==='all'?1:fitLow,baseHigh=scaleMode==='all'?count:Math.max(fitHigh,fitLow+10),focusRanks=series.flatMap(s=>s.points[activeIndex]?[s.points[activeIndex]!.rank]:[]),focus=focusRanks.length?focusRanks.reduce((sum,n)=>sum+n,0)/focusRanks.length:(baseLow+baseHigh)/2,span=Math.max(8,(baseHigh-baseLow)/zoom);
  let low=Math.max(1,focus-span/2),high=Math.min(count,focus+span/2);if(high-low<span){if(low===1)high=Math.min(count,1+span);else low=Math.max(1,count-span)}
  const changeZoom=(direction:number)=>setZoom(z=>Math.max(1,Math.min(4,Number((z+direction*.25).toFixed(2)))));
  const add=()=>{if(addId&&!selected.includes(addId)){setSelected([...selected,addId]);setAddId(alphabetical.find(t=>!selected.includes(t.id)&&t.id!==addId)?.id??'')}};
  const exportRows=weeks.flatMap((w,i)=>series.map(s=>{const p=s.points[i];return p?{season:data.season,week:weekName(w),team:s.team.name,rank:p.rank,resultsThrough:p.through}:null}).filter(Boolean)) as object[];
  const chartProps={series,weeks,low,high,activeIndex,setHovered,onOpenTeam,onZoom:changeZoom};
  return <div className="trend-workspace"><div className="section-heading trend-heading"><div><span className="scoreline">WEEK-BY-WEEK MOVEMENT</span><h1>Race across the season</h1><p>Put teams on the same field and watch the national order change after every Saturday.</p></div><Button variant="outline" onClick={()=>download(`rank-trends-${data.season}.csv`,exportRows)}>Export chart data</Button></div>
    <section className="surface trend-controls"><div><Picker label="Add a team" value={addId} onChange={setAddId} options={alphabetical.filter(t=>!selected.includes(t.id)).map(t=>({value:t.id,label:t.name}))}/><Button onClick={add} disabled={!addId||selected.length>=12}><Plus size={16}/> Add</Button></div><p>{selected.length}/12 teams shown. Team lists are alphabetical throughout the site.</p><div className="team-chip-row">{series.map(s=><button key={s.team.id} className="team-chip" style={{'--team-line':s.color} as CSSProperties} onClick={()=>setSelected(selected.filter(id=>id!==s.team.id))} aria-label={`Remove ${s.team.name}`}><Logo team={s.team} size={25}/><span>{s.team.short}</span><X size={14}/></button>)}</div></section>
    <section className="surface comparison-chart-panel"><div className="panel-title"><div><h2>{data.season} national rank</h2><p className="subcopy">Rank 1 is at the top. Fit the selected teams or restore the full {count}-team field.</p></div><div className="trend-chart-actions"><strong>{weekName(weeks[activeIndex])}</strong><Button variant={scaleMode==='auto'?'default':'outline'} onClick={()=>{setScaleMode('auto');setZoom(1)}}><ScanLine size={15}/> Fit selected</Button><Button variant={scaleMode==='all'?'default':'outline'} onClick={()=>{setScaleMode('all');setZoom(1)}}>All {count}</Button><label className="chart-zoom">Zoom <input aria-label="Ranking chart zoom" type="range" min="1" max="4" step=".25" value={zoom} onChange={e=>setZoom(Number(e.target.value))}/><span>{zoom.toFixed(2)}×</span></label><Dialog><DialogTrigger asChild><Button variant="outline"><Expand size={16}/> Expand chart</Button></DialogTrigger><DialogContent className="trend-dialog" onOpenAutoFocus={e=>e.preventDefault()}><DialogHeader><DialogTitle>{data.season} national ranking race</DialogTitle><DialogDescription>Move across the chart to inspect a week. Ctrl-wheel or pinch to zoom the rank scale.</DialogDescription></DialogHeader><TrendChart {...chartProps} large/></DialogContent></Dialog></div></div><TrendChart {...chartProps}/></section>
  </div>;
}
