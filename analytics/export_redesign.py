"""Export the selected redesign, with paired benchmarks and dated FPI diagnostics."""
import json,csv,hashlib,math
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr
from pipeline import ROOT,metrics,sigmoid
from redesign import features,NAMES

def main():
 cache=json.loads((ROOT/'analytics/redesign-cache.json').read_text());research=cache['report'];oldpath=ROOT/'public/data/model-v3.json'
 if not oldpath.exists():oldpath.write_bytes((ROOT/'public/data/model.json').read_bytes())
 old=json.loads(oldpath.read_text());oldp={p['id']:p for p in old['predictions']};rows=research['predictions'];byyear={y:json.loads((ROOT/f'public/data/{y}.json').read_text()) for y in range(2018,2027)}
 for p in rows:
  o=oldp[p['id']];p.update(previousProb=o['prob'],benchmark=o['benchmark'],cutoff=o['cutoff'])
  state=cache['states'][str(p['season'])][f"{p['season']}:{p['week']}"];a,b=state[p['home']],state[p['away']];h=0 if p['neutral'] else 1
  p.update(homeScore=a['mu']+a['offense']-b['defense']+1.5*h,awayScore=a['mu']+b['offense']-a['defense']-1.5*h)
  p['margin']=p['homeScore']-p['awayScore'];p['actualMargin']=p['hs']-p['as']
 evaluation=[];groups=[]
 for y in [2023,2024,2025,2026]:
  ps=[p for p in rows if p['season']==y]
  for name,key in [('Saturday model','prob'),('Previous v3','previousProb'),('Original scoring benchmark','benchmark')]:evaluation.append({'season':y,'model':name,**metrics([p[key] for p in ps],[p['outcome'] for p in ps])})
  team={t['id']:t for t in byyear[y]['snapshots']['99']['teams']}
  for label,rr in [('Weeks 1-4',[p for p in ps if p['week']<=4]),('Week 5 onward',[p for p in ps if p['week']>4]),('Cross-conference',[p for p in ps if team[p['home']]['conference']!=team[p['away']]['conference']])]:
   groups.append({'season':y,'group':label,'new':metrics([p['prob'] for p in rr],[p['outcome'] for p in rr]),'previous':metrics([p['previousProb'] for p in rr],[p['outcome'] for p in rr])})
 # Only FPI records whose actual timestamp precedes the same frozen weekly cutoff.
 fpirows=[];rejected=0
 for y in range(2018,2027):
  for r in csv.DictReader((ROOT/f'analytics/research-v4/cfb_fpi_weekly_{y}.csv').open(encoding='utf-8-sig')):
   if r.get('snapshot_out_of_sequence')=='true' or not r.get('last_updated') or not r.get('fpi'):rejected+=1;continue
   fpirows.append(r)
 fpigroups=defaultdict(list)
 for r in fpirows:fpigroups[(int(r['season']),r['team_id'])].append(r)
 paired=[]
 for p in rows:
  chosen=[]
  for t in [p['home'],p['away']]:
   valid=[r for r in fpigroups[(p['season'],t)] if r['last_updated']<p['cutoff']];chosen.append(max(valid,key=lambda r:r['last_updated']) if valid else None)
  if all(chosen):
   margin=float(chosen[0]['fpi'])-float(chosen[1]['fpi'])+(0 if p['neutral'] else 3)
   paired.append({'id':p['id'],'season':p['season'],'cutoff':p['cutoff'],'homeFpiTimestamp':chosen[0]['last_updated'],'awayFpiTimestamp':chosen[1]['last_updated'],'fpiMargin':margin,'fpiCorrect':int((margin>=0)==bool(p['outcome'])),'newCorrect':int((p['prob']>=.5)==bool(p['outcome'])),'v3Correct':int((p['previousProb']>=.5)==bool(p['outcome']))})
 fpimetrics=[]
 for y in [2023,2024,2025,2026]:
  pp=[p for p in paired if p['season']==y];fpimetrics.append({'season':y,'n':len(pp),'fpiPickAccuracy':float(np.mean([p['fpiCorrect'] for p in pp])) if pp else None,'newAccuracy':float(np.mean([p['newCorrect'] for p in pp])) if pp else None,'v3Accuracy':float(np.mean([p['v3Correct'] for p in pp])) if pp else None})
 # Descriptive paired uncertainty against v3, sampling whole weeks.
 rng=np.random.default_rng(42);boot=[]
 for years in [[2024,2025],[2026]]:
  ps=[p for p in rows if p['season'] in years];gg=defaultdict(list)
  for p in ps:
   loss=lambda q: -math.log(max(1e-9,q if p['outcome'] else 1-q))
   gg[(p['season'],p['week'])].append(loss(p['prob'])-loss(p['previousProb']))
  sums=np.array([sum(v) for v in gg.values()]);counts=np.array([len(v) for v in gg.values()]);sample=rng.integers(0,len(sums),(3000,len(sums)));deltas=sums[sample].sum(axis=1)/counts[sample].sum(axis=1)
  boot.append({'years':years,'difference':float(sums.sum()/counts.sum()),'lower':float(np.quantile(deltas,.025)),'upper':float(np.quantile(deltas,.975)),'weeks':len(sums)})
 oldranks={t['id']:t.get('previousModelRank',t['modelRank']) for t in byyear[2026]['snapshots']['99']['teams']}
 annual={};searches=[]
 for y in [2023,2024,2025,2026]:
  a=research['annual'][str(y)];cc=next(r['candidates'] for r in research['searches'] if r['year']==y);selected=cc[0];annual[str(y)]={**a,'selected':selected,'weight':1.};searches.append({'targetSeason':y,'candidates':cc})
  data=byyear[y];cfg=a['ratingConfig'];model={'version':'4.0.0','coefficients':a['coefficients'],'weight':1.,'trainingThrough':y-1,'featureNames':NAMES,'ratingConfig':cfg};data['model']=model;data['scoringConfig']={'elo':{'k':40,'home':55,'carry':.65},'scoring':{'shrinkage':cfg['lam'],'home':3,'decay':cfg['decay'],'scale':8},'eloWeight':0};previous={}
  for week,snap in data['snapshots'].items():
   state=cache['states'][str(y)][f'{y}:{week}'];coef=np.array(a['coefficients']);indices={t:float(np.mean([sigmoid(np.array(features(s,b,0))@coef) for k,b in state.items() if t!=k])) for t,s in state.items()};order=sorted(indices,key=lambda t:(-indices[t],t));ranks={t:i+1 for i,t in enumerate(order)}
   for t in snap['teams']:
    s=state[t['id']];t.setdefault('previousModelRank',t['modelRank']);t.update(offense=s['offense'],defense=s['defense'],power=s['v'][0],winIndex=indices[t['id']],modelRank=ranks[t['id']],modelChange=previous.get(t['id'],ranks[t['id']])-ranks[t['id']]);t['modelState'].update(s,basePower=s['v'][0]);snap['mu']=s['mu']
    # Display schedule strength on the same updated scoring scale.
    cutoff=snap.get('through');past=[g for g in data['games'] if g['fbs'] and cutoff and g['date']<=cutoff and t['id'] in (g['home'],g['away'])];opps=[g['away'] if g['home']==t['id'] else g['home'] for g in past];t['sos']=float(np.mean([state[o]['v'][0] for o in opps])) if opps else None
   previous=ranks
  look={p['id']:p for p in rows if p['season']==y}
  for p in data['predictions']:p.update({k:look[p['id']][k] for k in ['prob','previousProb','margin','homeScore','awayScore','cutoff']},modelVersion='4.0.0')
  (ROOT/f'public/data/{y}.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False),encoding='utf-8')
 fpi=json.loads((ROOT/'public/data/fpi-reference.json').read_text());newranks={t['id']:t['modelRank'] for t in byyear[2026]['snapshots']['99']['teams']};rankrows=[{**t,'previousRank':oldranks[t['id']],'modelRank':newranks[t['id']],'gap':newranks[t['id']]-t['rank']} for t in fpi['teams'] if t['id'] in newranks];compare={}
 for label,key in [('previous','previousRank'),('new','modelRank')]:compare[label]={'meanAbsoluteRankGap':float(np.mean([abs(t[key]-t['rank']) for t in rankrows])),'spearman':float(spearmanr([t[key] for t in rankrows],[t['rank'] for t in rankrows]).statistic)}
 report={**research,'version':'4.0.0','annual':annual,'searches':searches,'evaluation':evaluation,'groups':groups,'bootstrap':boot,'predictions':rows,'protocolSha256':hashlib.sha256((ROOT/'analytics/redesign-protocol.json').read_bytes()).hexdigest(),'scope':research['protocol']['scope'],'fpiComparison':{'note':'Ranking reference Sep 22 versus model results Sep 20. Historical pick benchmark uses latest FPI timestamp before weekly cutoff plus our fixed 3-point home adjustment, not ESPN official game probabilities.','excludedFlaggedRows':rejected,'matchedGames':fpimetrics,'rankMetrics':compare,'teams':rankrows},'sources':json.loads((ROOT/'analytics/research-v4/sources.json').read_text())}
 for name in ['model.json','redesign.json']:(ROOT/f'public/data/{name}').write_text(json.dumps(report,separators=(',',':'),allow_nan=False),encoding='utf-8')
 (ROOT/'public/data/fpi-paired-audit.json').write_text(json.dumps(paired,separators=(',',':')),encoding='utf-8')
 with (ROOT/'public/data/model-predictions.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 current=byyear[2026]['scoringConfig'];display=json.loads((ROOT/'public/data/report.json').read_text());ps=[p for p in rows if p['season'] in (2024,2025)];res=sorted(abs(p['actualMargin']-p['margin']) for p in ps);display.update(config=current,evaluation=evaluation,holdout=metrics([p['prob'] for p in ps],[p['outcome'] for p in ps]),residual80=res[int(.8*(len(res)-1))]);(ROOT/'public/data/report.json').write_text(json.dumps(display,separators=(',',':')))
 manifest=json.loads((ROOT/'public/data/manifest.json').read_text());manifest.update(version='4.0.0',config=current,generatedAt=datetime.now(timezone.utc).isoformat());(ROOT/'public/data/manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
 (ROOT/'lib/production-config.json').write_text(json.dumps({'version':'4.0.0',**annual['2026'],'featureNames':NAMES},separators=(',',':')))
 print(json.dumps({'evaluation':evaluation,'groups':groups,'bootstrap':boot,'fpi':fpimetrics,'rank':compare},indent=2))
if __name__=='__main__':main()
