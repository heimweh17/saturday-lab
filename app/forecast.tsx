"use client";
import {useEffect,useState} from 'react';
import {Button} from '@/components/ui/button';
import {Table,TableHeader,TableBody,TableHead,TableRow,TableCell} from '@/components/ui/table';
import {predict} from '@/lib/predict';
import {modelPredict,winDistribution} from '@/lib/model';
import {asset} from '@/lib/paths';
import {Picker,pct,dateLabel,download} from './ui';
import type {Season,Config} from './types';
type Fixture={id:string;date:string;home:string;away:string;homeName:string;awayName:string;neutral:boolean;completed:boolean;status:string;fbs:boolean;timeValid:boolean;source:string};
type Fixtures={season:number;fetchedAt:string;ratingThrough:string;teamsExpected:number;teamsCovered:number;failedTeams:{team:string;error:string}[];games:Fixture[]};
export function Forecast({data,teamId,config}:{data:Season;teamId:string;config:Config}){
 const [fixtures,setFixtures]=useState<Fixtures|null>(null),[error,setError]=useState(false);
 useEffect(()=>{const controller=new AbortController();fetch(asset('/data/fixtures.json'),{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(d=>setFixtures(d as Fixtures)).catch(e=>{if(e.name!=='AbortError')setError(true)});return()=>controller.abort()},[]);
 if(error)return <section className="surface"><h2>Upcoming games</h2><p>Schedule data could not load. Refresh to try again.</p></section>;
 if(!fixtures)return <section className="surface" role="status">Loading the remaining schedule…</section>;
 if(data.season!==fixtures.season)return <section className="surface"><h2>Upcoming games</h2><p>Remaining-game forecasts are available for {fixtures.season}. Choose Results to see historical games and their frozen pregame predictions.</p></section>;
 const latest=data.snapshots['99']; const team=latest.teams.find(t=>t.id===teamId); if(!team)return null;
 const rows=fixtures.games.filter(g=>!g.completed&&(g.home===teamId||g.away===teamId)).map(g=>{
   const home=g.home===teamId;const opponent=latest.teams.find(t=>t.id===(home?g.away:g.home));
   const eligible=g.status==='STATUS_SCHEDULED'&&g.date>String(latest.through)&&opponent&&g.fbs;
   const v1=eligible?predict(team,opponent,latest.mu,g.neutral?'neutral':home?'a':'b',config):null;
   const scheduledState=(t:typeof team)=>{const prior=fixtures.games.filter(f=>f.date<g.date&&(f.completed||f.status==='STATUS_SCHEDULED')&&(f.home===t!.id||f.away===t!.id)).map(f=>f.date).sort().at(-1);return {...t!.modelState!,lastDate:prior??t!.modelState!.lastDate}};
   const official=eligible&&team.modelState&&opponent.modelState&&data.model?modelPredict(scheduledState(team),scheduledState(opponent),g.neutral?0:home?1:-1,data.model,g.date):null;
   const probability=official?.probability??v1?.probability;
   return {...g,opponent:home?g.awayName:g.homeName,site:g.neutral?'Neutral':home?'Home':'Away',probability:probability??null,baseline:v1?.probability??null,pick:probability==null?'Not modeled':probability>=.5?'Projected W':'Projected L',reason:!g.fbs?'Opponent outside FBS model':g.status!=='STATUS_SCHEDULED'?g.status.replace('STATUS_',''):'Outside current data coverage'};
 });
 const modeled=rows.filter(r=>r.probability!==null);const expected=modeled.reduce((sum,r)=>sum+r.probability!,0);const distribution=winDistribution(modeled.map(r=>r.probability!));const picks=modeled.filter(r=>r.probability!>=.5).length;
 return <section className="surface forecast-panel"><div className="panel-title"><div><h2>Upcoming games</h2><p className="subcopy">If these teams played with their current strength, who would have the edge?</p></div><span className="muted">Saturday model · {data.model?.version}</span></div>
 <div className="forecast-summary"><div><strong>{expected.toFixed(1)}</strong><span>Expected remaining wins</span><small>Across {modeled.length} modeled games</small></div><div><strong>{picks}–{modeled.length-picks}</strong><span>Wins–losses if every pick holds</span><small>Not a season-record probability</small></div><div><strong>{rows.length}</strong><span>Published games remaining</span><small>{rows.length-modeled.length} outside forecast coverage</small></div></div>
 <p className="fine-print">Always uses the latest {data.season} ratings through {dateLabel(latest.through)}, regardless of the historical week selector. Strength stays fixed; rest uses the currently published schedule. This is a current-strength forecast, not a claim that future strength will stay unchanged. Expected wins sum probabilities, not rounded picks.</p>
 
 <Table><TableHeader><TableRow>{['Date','Opponent','Site','Projected result','Win probability'].map(s=><TableHead key={s}>{s}</TableHead>)}</TableRow></TableHeader><TableBody>{rows.map(g=><TableRow key={g.id}><TableCell>{dateLabel(g.date)}{!g.timeValid&&<small className="muted">Kickoff TBD</small>}</TableCell><TableCell><a href={g.source} target="_blank" rel="noreferrer"><strong>{g.opponent}</strong></a></TableCell><TableCell>{g.site}</TableCell><TableCell>{g.probability===null?<span className="muted">{g.reason}</span>:<span className={g.probability>=.5?'result-win':'result-loss'}>{g.pick}</span>}</TableCell><TableCell>{g.probability===null?'—':<div className="forecast-chance"><strong>{pct(g.probability)}</strong><span><i style={{width:`${g.probability*100}%`}}/></span>{g.probability>.4&&g.probability<.6&&<small>Close call</small>}</div>}</TableCell></TableRow>)}</TableBody></Table>
 {!rows.length&&<p className="empty">No remaining games are currently published for this team. Unannounced postseason games are not invented.</p>}
 <details className="season-distribution"><summary>Explore the remaining-win distribution</summary><p className="subcopy">Exact probability calculation across {modeled.length} modeled games, assuming independent results and the fixed strengths above. Non-modeled games are excluded.</p><div className="distribution-bars">{distribution.map((p,k)=><div key={k}><span>{k} wins</span><div><i style={{width:`${p/Math.max(...distribution)*100}%`}}/></div><strong>{pct(p)}</strong></div>)}</div><p className="fine-print">This is a scenario calculation, not a calibrated season forecast: shared injuries, future rating changes and correlations can shift the distribution.</p></details><div className="panel-title"><p className="fine-print">ESPN schedules retrieved {dateLabel(fixtures.fetchedAt)} · {fixtures.teamsCovered}/{fixtures.teamsExpected} teams covered. Dates and opponents may change.</p><Button variant="outline" onClick={()=>download(`${team.abbr}-remaining-schedule.csv`,rows)}>Export forecasts</Button></div>
 </section>;
}
