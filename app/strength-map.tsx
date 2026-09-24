"use client";
import {useRef,useState} from 'react';
import type {PointerEvent,WheelEvent} from 'react';
import {Expand,ScanLine,RotateCcw} from 'lucide-react';
import type {Team} from './types';
import {Logo,signed,pct} from './ui';
import {Button} from '@/components/ui/button';
import {Dialog,DialogContent,DialogDescription,DialogHeader,DialogTitle,DialogTrigger} from '@/components/ui/dialog';

type View={x:number;y:number;w:number;h:number};

function Field({teams,onSelect,large=false}:{teams:Team[];onSelect:(id:string)=>void;large?:boolean}){
  const [activeId,setActiveId]=useState<string|null>(null);
  const active=teams.find(t=>t.id===activeId)??teams.find(t=>(t.modelRank??t.rank)===1)??teams[0];
  const width=large?960:720,height=large?610:480;
  const [view,setView]=useState<View>({x:0,y:0,w:width,h:height});
  const drag=useRef<{x:number;y:number;view:View}|null>(null);
  const left=56,right=width-28,top=28,bottom=height-62;
  const x=(v:number)=>Math.max(left,Math.min(right,(left+right)/2+v/40*(right-left)/2));
  const y=(v:number)=>Math.max(top,Math.min(bottom,(top+bottom)/2-v/40*(bottom-top)/2));
  const ticks=[-30,-15,0,15,30],zoom=width/view.w;
  const clampView=(next:View):View=>({...next,x:Math.max(0,Math.min(width-next.w,next.x)),y:Math.max(0,Math.min(height-next.h,next.y))});
  const setZoom=(nextZoom:number,anchorX=.5,anchorY=.5)=>setView(current=>{
    const z=Math.max(1,Math.min(5,nextZoom)),w=width/z,h=height/z;
    const anchorSvgX=current.x+current.w*anchorX,anchorSvgY=current.y+current.h*anchorY;
    return clampView({x:anchorSvgX-w*anchorX,y:anchorSvgY-h*anchorY,w,h});
  });
  const onWheel=(event:WheelEvent<SVGSVGElement>)=>{
    event.preventDefault();
    const rect=event.currentTarget.getBoundingClientRect(),ax=(event.clientX-rect.left)/rect.width,ay=(event.clientY-rect.top)/rect.height;
    setZoom(zoom*(event.deltaY>0 ? .86 : 1.16),ax,ay);
  };
  const onPointerDown=(event:PointerEvent<SVGSVGElement>)=>{
    if((event.target as Element).closest('.plot-point'))return;
    drag.current={x:event.clientX,y:event.clientY,view};event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove=(event:PointerEvent<SVGSVGElement>)=>{if(!drag.current)return;const rect=event.currentTarget.getBoundingClientRect(),dx=(event.clientX-drag.current.x)/rect.width*drag.current.view.w,dy=(event.clientY-drag.current.y)/rect.height*drag.current.view.h;setView(clampView({...drag.current.view,x:drag.current.view.x-dx,y:drag.current.view.y-dy}))};
  const onPointerUp=(event:PointerEvent<SVGSVGElement>)=>{drag.current=null;event.currentTarget.releasePointerCapture(event.pointerId)};
  const focusCluster=()=>{
    const xs=teams.map(t=>x(t.offense)).sort((a,b)=>a-b),ys=teams.map(t=>y(t.defense)).sort((a,b)=>a-b),lo=Math.floor(teams.length*.06),hi=Math.max(lo+1,Math.ceil(teams.length*.94)-1);
    const x0=Math.max(0,xs[lo]-55),x1=Math.min(width,xs[hi]+55),y0=Math.max(0,ys[lo]-55),y1=Math.min(height,ys[hi]+55),z=Math.max(1,Math.min(4,Math.min(width/(x1-x0),height/(y1-y0))));
    const w=width/z,h=height/z,cx=(x0+x1)/2,cy=(y0+y1)/2;setView(clampView({x:cx-w/2,y:cy-h/2,w,h}));
  };
  return <div className="strength-map-body">
    <div className="map-canvas"><div className="map-chart-tools"><Button variant="outline" onClick={()=>setView({x:0,y:0,w:width,h:height})}><RotateCcw size={14}/> All teams</Button><Button variant="outline" onClick={focusCluster}><ScanLine size={14}/> Focus cluster</Button><label>Zoom <input aria-label="Offense defense map zoom" type="range" min="1" max="5" step=".1" value={zoom} onChange={e=>setZoom(Number(e.target.value))}/><span>{zoom.toFixed(1)}×</span></label></div>
    <svg viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} className="strength-chart zoomable-chart" onWheel={onWheel} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={()=>{drag.current=null}} role="img" aria-label="Interactive offense and defense map. Better offense is to the right and better defense is higher. Scroll to zoom and drag open space to pan.">
      <rect x={left} y={top} width={right-left} height={bottom-top} fill="#eef4f7"/>
      <path d={`M${left} ${top}H${right}V${bottom}H${left}Z`} fill="none" stroke="#b9cad4"/>
      {ticks.map(n=><g key={n}><line x1={x(n)} x2={x(n)} y1={top} y2={bottom} stroke={n===0?'#8299a8':'#d2dfe5'} strokeDasharray={n===0?'0':'4 7'}/><line x1={left} x2={right} y1={y(n)} y2={y(n)} stroke={n===0?'#8299a8':'#d2dfe5'} strokeDasharray={n===0?'0':'4 7'}/><text x={x(n)} y={bottom+25} textAnchor="middle">{n>0?`+${n}`:n}</text><text x={left-10} y={y(n)+4} textAnchor="end">{n>0?`+${n}`:n}</text></g>)}
      <text x={right-10} y={top+22} textAnchor="end" className="quadrant">ELITE BOTH WAYS</text><text x={left+12} y={bottom-13} className="quadrant">BUILDING</text>
      {teams.slice().reverse().map(t=>{const rank=t.modelRank??t.rank,isActive=t.id===active?.id;return <g key={t.id} role="button" tabIndex={0} aria-label={`${t.short}, rank ${rank}, offense ${t.offense.toFixed(1)}, defense ${t.defense.toFixed(1)}. Open team report.`} onMouseEnter={()=>setActiveId(t.id)} onFocus={()=>setActiveId(t.id)} onClick={()=>onSelect(t.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(t.id)}}} className="plot-point">
        <circle cx={x(t.offense)} cy={y(t.defense)} r={isActive?12:rank<=10?7:4.2} fill={rank<=25?t.color:'#7893a2'} opacity={isActive?1:rank<=25 ? .88 : .48} stroke="white" strokeWidth={isActive?3:1.4}/>
        {(isActive||rank<=5)&&<text x={x(t.offense)+11} y={y(t.defense)-9} className="point-label">{t.abbr}</text>}
      </g>})}
      <text x={(left+right)/2} y={height-13} textAnchor="middle" className="axis-label">Opponent-adjusted offense →</text>
      <text transform={`translate(16 ${(top+bottom)/2}) rotate(-90)`} textAnchor="middle" className="axis-label">Better defense →</text>
    </svg><p className="chart-instruction">Scroll or pinch to zoom · drag open space to pan · choose All teams to reset</p></div>
    {active&&<button className="map-team-readout" onClick={()=>onSelect(active.id)} aria-label={`Open ${active.name} team report`}>
      <Logo team={active} size={48}/><span><small>#{active.modelRank??active.rank} nationally</small><strong>{active.name}</strong><em>{active.wins}–{active.losses} · {active.conference.replace(' Conference','')}</em></span><dl><div><dt>Strength</dt><dd>{pct(active.winIndex)}</dd></div><div><dt>Offense</dt><dd>{signed(active.offense)}</dd></div><div><dt>Defense</dt><dd>{signed(active.defense)}</dd></div></dl>
    </button>}
  </div>;
}

export function StrengthMap({teams,onSelect}:{teams:Team[];onSelect:(id:string)=>void}){
  return <section className="strength-map-panel">
    <div className="panel-title"><div><h2>Offense × defense map</h2><p>Every dot is a team. Hover for its profile; select it for the full report.</p></div><Dialog><DialogTrigger asChild><Button variant="outline"><Expand size={16}/> Expand</Button></DialogTrigger><DialogContent className="strength-map-dialog" onOpenAutoFocus={e=>e.preventDefault()}><DialogHeader><DialogTitle>FBS offense × defense map</DialogTitle><DialogDescription>Opponent-adjusted points per game. Right and up are better. Zoom into the central pack, pan freely or restore all teams.</DialogDescription></DialogHeader><Field teams={teams} onSelect={onSelect} large/></DialogContent></Dialog></div>
    <Field teams={teams} onSelect={onSelect}/>
  </section>;
}
