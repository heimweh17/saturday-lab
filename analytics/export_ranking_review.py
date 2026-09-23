"""Publish the selected scalar-strength model and its complete comparison record."""
import json,csv,hashlib
from datetime import datetime,timezone
from collections import defaultdict
import numpy as np
from scipy.stats import spearmanr
from pipeline import ROOT,sigmoid,metrics
from ranking_review import NAMES,vector
from qb_review import CACHE

def summarize(rows,key):return metrics([p[key] for p in rows],[p['outcome'] for p in rows])

def main():
 cache=json.loads(CACHE.read_text());research=cache['report'];NAMES=research['featureNames'];rows=research['predictions'];old=json.loads((ROOT/'public/data/model-v4.json').read_text());oldrows={p['id']:p for p in old['predictions']}
 evaluation=[];groups=[];bootstrap=[];rng=np.random.default_rng(20260923)
 for year in [2023,2024,2025,2026]:
  ps=[p for p in rows if p['season']==year];data=json.loads((ROOT/f'public/data/{year}.json').read_text());teams={t['id']:t for t in data['snapshots']['99']['teams']}
  for label,key in [('Saturday model','prob'),('Previous v4','previousProb'),('Previous v3','v3Prob'),('Original scoring benchmark','benchmark')]:evaluation.append({'season':year,'model':label,**summarize(ps,key)})
  for label,rr in [('Weeks 1-4',[p for p in ps if p['week']<=4]),('Week 5 onward',[p for p in ps if p['week']>4]),('Cross-conference',[p for p in ps if teams[p['home']]['conference']!=teams[p['away']]['conference']]),('V4 favorite at least 80%',[p for p in ps if max(p['previousProb'],1-p['previousProb'])>=.8]),('V4 competitive games',[p for p in ps if max(p['previousProb'],1-p['previousProb'])<.8])]:groups.append({'season':year,'group':label,'new':summarize(rr,'prob'),'previous':summarize(rr,'previousProb'),'original':summarize(rr,'benchmark')})
 for years in [[2024,2025],[2026]]:
  ps=[p for p in rows if p['season'] in years]
  for reference,key in [('v4','previousProb'),('original','benchmark')]:
   blocks=defaultdict(list)
   for p in ps:
    loss=lambda q:-np.log(np.clip(q if p['outcome'] else 1-q,1e-9,1))
    blocks[(p['season'],p['week'])].append(loss(p['prob'])-loss(p[key]))
   sums=np.array([sum(v) for v in blocks.values()]);counts=np.array([len(v) for v in blocks.values()]);sample=rng.integers(0,len(sums),(3000,len(sums)));d=sums[sample].sum(axis=1)/counts[sample].sum(axis=1)
   bootstrap.append({'years':years,'reference':reference,'difference':float(sums.sum()/counts.sum()),'lower':float(np.quantile(d,.025)),'upper':float(np.quantile(d,.975)),'weeks':len(sums)})
 caseStudies=[];movement=[]
 for year in [2023,2024,2025,2026]:
  path=ROOT/f'public/data/{year}.json';data=json.loads(path.read_text());annual=research['annual'][str(year)];cfg=annual['selected']['ratingConfig'];bundle=annual['selected']['bundle'];coef=np.array(annual['coefficients'])
  data['model']={'version':'5.0.0','coefficients':coef.tolist(),'weight':1.,'trainingThrough':year-1,'featureNames':NAMES,'ratingConfig':cfg,'bundle':bundle,'ranking':'scalar neutral strength'}
  data['scoringConfig']={'elo':{'k':40,'home':55,'carry':cfg['carry']},'scoring':{'shrinkage':cfg['lam'],'home':3.,'decay':.97,'scale':8.},'eloWeight':0}
  previous={};previousScore={};previousIndex={};previousParts={}
  for week in data['weeks']:
   snap=data['snapshots'][str(week)];states=cache['states'][str(year)][f'{year}:{week}'];parts={t:vector(s,bundle)*coef[:-2] for t,s in states.items()};strength={t:float(sum(p)) for t,p in parts.items()};indices={t:float(np.mean([sigmoid(v-b) for k,b in strength.items() if k!=t])) for t,v in strength.items()};order=sorted(strength,key=lambda t:(-strength[t],t));ranks={t:i+1 for i,t in enumerate(order)}
   for t in snap['teams']:
    tid=t['id'];s=states[tid];t.setdefault('v4ModelRank',t['modelRank']);t.setdefault('v4WinIndex',t['winIndex'])
    t.update(power=s['q'][0],offense=s['offense'],defense=s['defense'],elo=1500+s['q'][3]*100,winIndex=indices[tid],modelRank=ranks[tid],modelChange=previous.get(tid,ranks[tid])-ranks[tid])
    t['modelState'].pop('v',None);t['modelState'].update(s,q=vector(s,bundle).tolist(),basePower=s['q'][0]);snap['mu']=s['mu']
    cutoff=snap['through'];past=[g for g in data['games'] if g['fbs'] and cutoff and g['date']<=cutoff and tid in [g['home'],g['away']]];opponents=[g['away'] if g['home']==tid else g['home'] for g in past];t['sos']=float(np.mean([states[o]['q'][0] for o in opponents])) if opponents else None
    if previous:
     fixed=float(np.mean([sigmoid(strength[tid]-v) for k,v in previousScore.items() if k!=tid]))
     t['ratingExplanation']={'previousRank':previous[tid],'ownIndexChange':fixed-previousIndex[tid],'fieldIndexChange':indices[tid]-fixed,'drivers':[{'label':NAMES[j],'logOddsChange':float(parts[tid][j]-previousParts[tid][j])} for j in range(len(coef)-2) if coef[j]!=0]}
     if year==2026:movement.append({'teamId':tid,'team':t['name'],'snapshot':week,'rank':ranks[tid],'v4Rank':t['v4ModelRank'],'originalRank':t['rank'],**t['ratingExplanation']})
    else:t.pop('ratingExplanation',None)
    if year==2026 and tid in ['57','248']:caseStudies.append({'team':t['name'],'teamId':tid,'snapshot':week,'v5Rank':ranks[tid],'v4Rank':t['v4ModelRank'],'originalRank':t['rank'],'strengthIndex':indices[tid],'explanation':t.get('ratingExplanation')})
   previous=ranks;previousScore=strength;previousIndex=indices;previousParts=parts
  lookup={p['id']:p for p in rows if p['season']==year}
  for p in data['predictions']:p.update({k:lookup[p['id']][k] for k in ['prob','previousProb','v3Prob','margin','homeScore','awayScore','cutoff']},modelVersion='5.0.0')
  path.write_text(json.dumps(data,separators=(',',':'),allow_nan=False),encoding='utf-8')
 # Reuse timestamp-audited external records, replacing only our model outcomes.
 paired=json.loads((ROOT/'public/data/fpi-paired-audit.json').read_text());lookup={p['id']:p for p in rows};fpiMetrics=[]
 for p in paired:
  r=lookup[p['id']];p.update(newCorrect=int((r['prob']>=.5)==bool(r['outcome'])),previousCorrect=int((r['previousProb']>=.5)==bool(r['outcome'])),originalCorrect=int((r['benchmark']>=.5)==bool(r['outcome'])))
 for year in [2023,2024,2025,2026]:
  pp=[p for p in paired if p['season']==year];fpiMetrics.append({'season':year,'n':len(pp),**{key:float(np.mean([p[col] for p in pp])) for key,col in [('fpiPickAccuracy','fpiCorrect'),('newAccuracy','newCorrect'),('previousAccuracy','previousCorrect'),('originalAccuracy','originalCorrect'),('v3Accuracy','v3Correct')]}})
 current=json.loads((ROOT/'public/data/2026.json').read_text());currentTeams={t['id']:t for t in current['snapshots']['99']['teams']}
 fpi=json.loads((ROOT/'public/data/fpi-reference.json').read_text());rankrows=[{**t,'previousRank':currentTeams[t['id']]['v4ModelRank'],'modelRank':currentTeams[t['id']]['modelRank'],'gap':currentTeams[t['id']]['modelRank']-t['rank']} for t in fpi['teams'] if t['id'] in currentTeams];rankmetrics={}
 for name,key in [('previous','previousRank'),('new','modelRank')]:rankmetrics[name]={'meanAbsoluteRankGap':float(np.mean([abs(t[key]-t['rank']) for t in rankrows])),'spearman':float(spearmanr([t[key] for t in rankrows],[t['rank'] for t in rankrows]).statistic)}
 stage1=json.loads((ROOT/'analytics/ranking-review-cache.json').read_text())['report'];stage1Evaluation=[{'season':year,**summarize([p for p in stage1['predictions'] if p['season']==year],'prob')} for year in [2023,2024,2025,2026]]
 stage3=json.loads((ROOT/'analytics/cohort-review-cache.json').read_text())['report']
 cohortAblation=[]
 for search in stage3['searches']:
  for mode in ['none','published','equal','developmental','no_freshmen','lagged_four']:
   options=[c for c in search['candidates'] if c['ratingConfig']['talentMode']==mode]
   if options:cohortAblation.append({'targetSeason':search['targetSeason'],'mode':mode,'bestValidationLogLoss':min(c['logLoss'] for c in options),'candidates':len(options)})
 report={**research,'cohortAblation':cohortAblation,'firstStageEvaluation':stage1Evaluation,'evaluation':evaluation,'groups':groups,'bootstrap':bootstrap,'fpiComparison':{**old['fpiComparison'],'matchedGames':fpiMetrics,'rankMetrics':rankmetrics,'teams':rankrows},'sources':old['sources']+json.loads((ROOT/'analytics/extended-sources.json').read_text()),'caseStudies':caseStudies,'protocolSha256':hashlib.sha256((ROOT/'analytics/qb-review-protocol.json').read_bytes()).hexdigest()}
 for name,obj in [('research-stage2.json',json.loads((ROOT/'analytics/prior-review-cache.json').read_text())['report']),('research-stage3.json',json.loads((ROOT/'analytics/cohort-review-cache.json').read_text())['report']),('research-stage1.json',stage1),('model.json',report),('ranking-review.json',report),('ranking-movement.json',movement),('fpi-paired-audit.json',paired)]:
  (ROOT/'public/data'/name).write_text(json.dumps(obj,separators=(',',':'),allow_nan=False),encoding='utf-8')
 with (ROOT/'public/data/model-predictions.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 cfg=current['scoringConfig'];display=json.loads((ROOT/'public/data/report.json').read_text());ps=[p for p in rows if p['season'] in (2024,2025)];res=sorted(abs(p['actualMargin']-p['margin']) for p in ps)
 display.update(config=cfg,evaluation=evaluation,holdout=summarize(ps,'prob'),residual80=res[int(.8*(len(res)-1))]);(ROOT/'public/data/report.json').write_text(json.dumps(display,separators=(',',':')),encoding='utf-8')
 manifest=json.loads((ROOT/'public/data/manifest.json').read_text());manifest.update(version='5.0.0',config=cfg,generatedAt=datetime.now(timezone.utc).isoformat());(ROOT/'public/data/manifest.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
 (ROOT/'lib/production-config.json').write_text(json.dumps({'version':'5.0.0',**research['annual']['2026'],'featureNames':NAMES},separators=(',',':')),encoding='utf-8')
 print(json.dumps({'evaluation':evaluation,'bootstrap':bootstrap,'fpi':fpiMetrics,'rankMetrics':rankmetrics,'caseStudies':caseStudies},indent=2))
if __name__=='__main__':main()
