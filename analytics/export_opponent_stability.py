"""Publish the opponent-adjusted stability model after its frozen gate passes."""
import csv,json,hashlib
from collections import defaultdict
from datetime import datetime,timezone
import numpy as np
from scipy.stats import spearmanr
from pipeline import ROOT,YEARS,load_data,metrics,sigmoid
import cohort_review as cohort
import qb_review as qb
import ranking_review as r
from opponent_stability_review import NAMES,number

def summarize(rows,key):return metrics([p[key] for p in rows],[p['outcome'] for p in rows])

def build_states():
 cohort.configure();r.NAMES=NAMES;r.UNIT_INDICES=list(range(9));teams,seasons,talents,_=cohort.read_inputs()
 for year in YEARS:
  raw=list(csv.DictReader((r.DIR/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig')));lookup={(v['game_id'],v['team_id']):v for v in raw}
  for g in seasons[year]['games']:
   for i,t in enumerate([g['home'],g['away']]):
    row=lookup.get((g['id'],t),{});g['units'][i].extend([number(row,'first_downs_created_rate'),number(row,'EPA_passing_per_play'),number(row,'EPA_rushing_per_play'),number(row,'yards_per_play'),number(row,'EPA_explosive_rate')])
 config=json.loads((ROOT/'lib/production-config.json').read_text())['selected']['ratingConfig'];states=cohort.build(teams,seasons,talents,config)
 _,_,boxes,_=load_data(r.SOURCE_DATA);passers,_=qb.passer_states(teams,seasons,boxes)
 for key,snapshot in states.items():
  for team,state in snapshot.items():state['q'].extend(passers[key][team]['values'])
 return states,config

def main():
 research=json.loads((ROOT/'analytics/opponent-stability-review-results.json').read_text());assert research['promotionGate']['passed']
 states,config=build_states();pred={p['id']:p for p in research['predictions']};oldReport=json.loads((ROOT/'public/data/model.json').read_text())
 if not (ROOT/'public/data/model-v5.json').exists():(ROOT/'public/data/model-v5.json').write_text(json.dumps(oldReport,separators=(',',':'),allow_nan=False))
 movements=[]
 for year in [2023,2024,2025,2026]:
  path=ROOT/f'public/data/{year}.json';data=json.loads(path.read_text());annual=research['annual'][str(year)];coef=np.array(annual['coefficients']);bundle=annual['selected']['bundle']
  data['model']={'version':'6.0.0','coefficients':coef.tolist(),'weight':1.,'trainingThrough':year-1,'featureNames':NAMES,'ratingConfig':config,'bundle':bundle,'ranking':'opponent-adjusted scalar neutral strength'}
  previous={};previousScore={};previousIndex={};previousParts={}
  for week in data['weeks']:
   snap=data['snapshots'][str(week)];ss=states[f'{year}:{week}'];parts={t:np.array(s['q'])*coef[:-2] for t,s in ss.items()};strength={t:float(sum(v)) for t,v in parts.items()};indices={t:float(np.mean([sigmoid(v-b) for k,b in strength.items() if k!=t])) for t,v in strength.items()};order=sorted(strength,key=lambda t:(-strength[t],t));ranks={t:i+1 for i,t in enumerate(order)}
   for t in snap['teams']:
    tid=t['id'];s=ss[tid];t.setdefault('v5ModelRank',t['modelRank']);t.setdefault('v5WinIndex',t['winIndex']);t.update(power=s['q'][0],offense=s['offense'],defense=s['defense'],elo=1500+s['q'][3]*100,winIndex=indices[tid],modelRank=ranks[tid],modelChange=previous.get(tid,ranks[tid])-ranks[tid]);t['modelState'].update(s,q=s['q'],basePower=s['q'][0]);snap['mu']=s['mu']
    if previous:
     fixed=float(np.mean([sigmoid(strength[tid]-v) for k,v in previousScore.items() if k!=tid]));t['ratingExplanation']={'previousRank':previous[tid],'ownIndexChange':fixed-previousIndex[tid],'fieldIndexChange':indices[tid]-fixed,'drivers':[{'label':NAMES[j],'logOddsChange':float(parts[tid][j]-previousParts[tid][j])} for j in range(len(coef)-2) if coef[j]!=0]}
    else:t.pop('ratingExplanation',None)
    if year==2026:movements.append({'teamId':tid,'team':t['name'],'snapshot':week,'rank':ranks[tid],'v5Rank':t['v5ModelRank'],'originalRank':t['rank'],'strengthIndex':indices[tid],'explanation':t.get('ratingExplanation')})
   previous=ranks;previousScore=strength;previousIndex=indices;previousParts=parts
  for p in data['predictions']:
   row=pred.get(p['id'])
   if row:p.setdefault('v5Prob',p['prob']);p['prob']=row['prob'];p['modelVersion']='6.0.0'
  path.write_text(json.dumps(data,separators=(',',':'),allow_nan=False))
 evaluation=[]
 for year in [2023,2024,2025,2026]:
  rows=[p for p in research['predictions'] if p['season']==year]
  for label,key in [('Saturday model v6','prob'),('Previous v5','v5Prob'),('Previous v4','v4Prob'),('Original scoring benchmark','v1Prob')]:evaluation.append({'season':year,'model':label,**summarize(rows,key)})
 current=json.loads((ROOT/'public/data/2026.json').read_text());currentTeams={t['id']:t for t in current['snapshots']['99']['teams']};fpi=oldReport.get('fpiComparison',{});rankrows=[]
 for item in fpi.get('teams',[]):
  if item['id'] in currentTeams:
   team=currentTeams[item['id']];rankrows.append({**item,'v5Rank':team['v5ModelRank'],'modelRank':team['modelRank'],'gap':team['modelRank']-item['rank']})
 rankmetrics=dict(fpi.get('rankMetrics',{}))
 if rankrows:rankmetrics['current']={'meanAbsoluteRankGap':float(np.mean([abs(t['modelRank']-t['rank']) for t in rankrows])),'spearman':float(spearmanr([t['modelRank'] for t in rankrows],[t['rank'] for t in rankrows]).statistic)}
 report={**oldReport,'version':'6.0.0','currentAnnual':research['annual'],'stabilityResearch':research,'predictions':research['predictions'],'evaluation':evaluation,'scope':research['scope'],'protocolSha256':research['protocol']['blueprintSha256'],'fpiComparison':{**fpi,'rankMetrics':rankmetrics,'teams':rankrows},'sources':oldReport.get('sources',[])+json.loads((ROOT/'analytics/stability-sources.json').read_text())}
 for name,obj in [('model.json',report),('ranking-review.json',report),('research-stage5.json',json.loads((ROOT/'analytics/stability-review-results.json').read_text())),('research-stage6.json',research),('ranking-movement.json',movements)]:
  (ROOT/'public/data'/name).write_text(json.dumps(obj,separators=(',',':'),allow_nan=False))
 with (ROOT/'public/data/model-predictions.csv').open('w',newline='',encoding='utf-8') as file:
  writer=csv.DictWriter(file,fieldnames=list(research['predictions'][0]));writer.writeheader();writer.writerows(research['predictions'])
 display=json.loads((ROOT/'public/data/report.json').read_text());pooled=[p for p in research['predictions'] if p['season'] in (2024,2025)];display.update(evaluation=evaluation,holdout=summarize(pooled,'prob'));(ROOT/'public/data/report.json').write_text(json.dumps(display,separators=(',',':')))
 manifest=json.loads((ROOT/'public/data/manifest.json').read_text());manifest.update(version='6.0.0',generatedAt=datetime.now(timezone.utc).isoformat());(ROOT/'public/data/manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
 selected=research['annual']['2026'];(ROOT/'lib/production-config.json').write_text(json.dumps({'version':'6.0.0','selected':{**selected['selected'],'ratingConfig':config},'coefficients':selected['coefficients'],'trainingThrough':2025,'validationYears':selected['validationYears'],'validation':selected['validation'],'test':selected['test'],'featureNames':NAMES},separators=(',',':')))
 print(json.dumps({'version':'6.0.0','evaluation':evaluation,'gate':research['promotionGate'],'rankMetrics':rankmetrics},indent=2))

if __name__=='__main__':main()
