"""Pregame play-feature stability search against the locked v5 model."""
import hashlib,json,math
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from pipeline import ROOT,YEARS,metrics,sigmoid
import cohort_review as cohort
import qb_review as qb
import ranking_review as r

DATA=ROOT/'analytics/research-stability'
CACHE=ROOT/'analytics/stability-review-cache.json'
SOURCE_MANIFEST=ROOT/'analytics/stability-sources.json'
METRICS=['epa','wepa','success_rate','early_success_rate','late_success_rate','pass_epa','rush_epa','pass_success_rate','rush_success_rate','scoring_opp_rate_oe','pts_per_scoring_opp','starting_fp','3rd_down_pct']
NAMES=['Scoring strength','Observed passer prior efficiency','Home field','Rest days',*[f'Net {m}' for m in METRICS],'Evidence availability','Offensive pace']
FAMILIES={
 'baseline':[],
 'balanced_epa':['epa','wepa'],
 'stable_efficiency':['success_rate','early_success_rate'],
 'pass_rush':['pass_epa','rush_epa','pass_success_rate','rush_success_rate'],
 'finishing_field':['scoring_opp_rate_oe','pts_per_scoring_opp','starting_fp'],
 'situational':['late_success_rate','3rd_down_pct'],
 'broad':METRICS,
 'epa_only':['epa'],
 'wepa_only':['wepa'],
 'success_only':['success_rate'],
 'early_success_only':['early_success_rate'],
 'pass_epa_only':['pass_epa'],
 'rush_epa_only':['rush_epa'],
}
BASE=[0,1,2,3]

def rest(state,date):
 if not state['lastDate']:return 7.
 return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(state['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))

def load_matchups():
 manifest=json.loads(SOURCE_MANIFEST.read_text());look={};coverage=[]
 for entry in manifest:
  path=DATA/entry['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],entry['file']
  frame=pd.read_parquet(path);assert not frame.duplicated(['game_id','team_id']).any()
  year=int(frame.season.iloc[0]);coverage.append({'season':year,'rows':len(frame),'completeSnapshots':int(frame.off_epa.notna().sum())})
  for row in frame.to_dict('records'):look[(str(int(row['game_id'])),str(int(row['team_id'])))]=row
 return look,coverage

def fit_model(x,y,indices,penalty):
 a=x[:,indices].copy();med=np.zeros(len(indices))
 for j in range(len(indices)):
  good=np.isfinite(a[:,j]);med[j]=float(np.median(a[good,j])) if good.any() else 0.;a[~good,j]=med[j]
 scale=np.maximum(np.sqrt(np.mean(a*a,axis=0)),1e-6);z=a/scale
 signed={3,len(NAMES)-2,len(NAMES)-1,4+METRICS.index('3rd_down_pct')}
 bounds=[(None,None) if idx in signed else (0,None) for idx in indices]
 def objective(b):
  logits=z@b
  return np.logaddexp(0,logits).sum()-y@logits+penalty/2*(b@b),z.T@(sigmoid(logits)-y)+penalty*b
 result=minimize(objective,np.zeros(len(indices)),jac=True,method='L-BFGS-B',bounds=bounds,options={'ftol':1e-12,'gtol':1e-7,'maxiter':600})
 if not result.success:raise RuntimeError(result.message)
 beta=np.zeros(len(NAMES));beta[indices]=result.x/scale
 fullmed=np.zeros(len(NAMES));fullmed[indices]=med
 return beta,fullmed

def predict(x,beta,med):
 a=x.copy();missing=~np.isfinite(a);a[missing]=np.take(med,np.where(missing)[1]);return sigmoid(a@beta)

def bootstrap_probability(rows,seed=20260924,reps=10000):
 blocks={}
 for row in rows:blocks.setdefault((row['season'],row['week']),[]).append(row['candidateLoss']-row['v5Loss'])
 values=np.array([np.mean(v) for v in blocks.values()]);rng=np.random.default_rng(seed)
 samples=rng.choice(values,(reps,len(values)),replace=True).mean(axis=1)
 return {'blocks':len(values),'repetitions':reps,'probabilityLowerLogLoss':float(np.mean(samples<0)),'meanDelta':float(values.mean()),'p05':float(np.quantile(samples,.05)),'p95':float(np.quantile(samples,.95))}

def main():
 cohort.configure();r.NAMES=qb.NAMES
 teams,seasons,talents,coreCoverage=cohort.read_inputs();_,_,boxes,_=__import__('pipeline').load_data(r.SOURCE_DATA)
 passer,passerCoverage=qb.passer_states(teams,seasons,boxes)
 cfg=json.loads((ROOT/'lib/production-config.json').read_text())['selected']['ratingConfig'];states=cohort.build(teams,seasons,talents,cfg)
 for key,snapshot in states.items():
  for team,state in snapshot.items():state['q'].extend(passer[key][team]['values'])
 matchup,matchupCoverage=load_matchups();games=[g for year in YEARS if year>=2019 for g in seasons[year]['games'] if g['fbs']]
 yy=np.array([g['season'] for g in games]);outcome=np.array([g['hs']>g['as'] for g in games],float);x=[];matched=0
 for g in games:
  a=states[f"{g['season']}:{g['week']}"][g['home']];b=states[f"{g['season']}:{g['week']}"][g['away']]
  row=[a['q'][0]-b['q'][0],a['q'][8]-b['q'][8],0. if g['neutral'] else 1.,rest(a,g['date'])-rest(b,g['date'])]
  home=matchup.get((g['id'],g['home']));away=matchup.get((g['id'],g['away']))
  if home and away:
   # Kickoff timestamps and one rescheduled week label were revised upstream; IDs and teams are exact.
   assert str(int(home['team_id']))==g['home'];assert str(int(away['team_id']))==g['away'];matched+=1
  for name in METRICS:
   try:row.append(float(home['off_'+name])-float(home['def_'+name])-float(away['off_'+name])+float(away['def_'+name]))
   except (TypeError,ValueError,KeyError):row.append(np.nan)
  ha=bool(home and np.isfinite(home.get('off_epa',np.nan)));aa=bool(away and np.isfinite(away.get('off_epa',np.nan)));row.append(float(ha)-float(aa))
  try:row.append(-float(home['off_sec_per_play_mean'])+float(away['off_sec_per_play_mean']))
  except (TypeError,ValueError,KeyError):row.append(np.nan)
  x.append(row)
 x=np.array(x);assert x.shape==(len(games),len(NAMES))
 candidates=[]
 for family,names in FAMILIES.items():
  indices=BASE+[4+METRICS.index(name) for name in names]
  if family!='baseline':indices += [len(NAMES)-2]
  if family in ('situational','broad'):indices += [len(NAMES)-1]
  indices=sorted(set(indices))
  for penalty in [1.,10.,50.]:
   probs=np.full(len(games),np.nan);parameters={}
   for year in range(2020,2027):
    train=(yy>=2019)&(yy<year);test=yy==year;beta,med=fit_model(x[train],outcome[train],indices,penalty);probs[test]=predict(x[test],beta,med);parameters[str(year)]={'coefficients':beta.tolist(),'medians':med.tolist()}
   candidates.append({'family':family,'ridge':penalty,'indices':indices,'prob':probs,'parameters':parameters})
 annual={};selectedProb={}
 for year in [2023,2024,2025,2026]:
  val=(yy>=year-3)&(yy<year);test=yy==year
  ordered=sorted(candidates,key=lambda c:(metrics(c['prob'][val],outcome[val])['logLoss'],len(c['indices']),c['ridge']))
  chosen=ordered[0];selectedProb[year]=chosen['prob'];annual[str(year)]={'selected':{k:chosen[k] for k in ['family','ridge','indices']},'validation':metrics(chosen['prob'][val],outcome[val]),'test':metrics(chosen['prob'][test],outcome[test]),'parameters':chosen['parameters'][str(year)],'topCandidates':[{**{k:c[k] for k in ['family','ridge','indices']},**metrics(c['prob'][val],outcome[val])} for c in ordered[:10]]}
 old=json.loads(qb.CACHE.read_text())['report'];oldp={p['id']:p for p in old['predictions']};comparisons={};paired=[]
 for year in [2023,2024,2025,2026]:
  mask=yy==year;ids=np.where(mask)[0];p=selectedProb[year][mask];v5=np.array([oldp[games[i]['id']]['prob'] for i in ids]);v4=np.array([oldp[games[i]['id']]['previousProb'] for i in ids]);v1=np.array([oldp[games[i]['id']]['benchmark'] for i in ids]);y=outcome[mask]
  comparisons[str(year)]={'candidate':metrics(p,y),'v5':metrics(v5,y),'v4':metrics(v4,y),'v1':metrics(v1,y)}
  if year in (2024,2025):
   for j,i in enumerate(ids):
    q1=max(1e-9,min(1-1e-9,float(p[j])));q0=max(1e-9,min(1-1e-9,float(v5[j])));actual=y[j]
    paired.append({'season':year,'week':games[i]['week'],'candidateLoss':float(-actual*math.log(q1)-(1-actual)*math.log(1-q1)),'v5Loss':float(-actual*math.log(q0)-(1-actual)*math.log(1-q0))})
 pooledCandidate=metrics([selectedProb[g['season']][i] for i,g in enumerate(games) if g['season'] in (2024,2025)],[outcome[i] for i,g in enumerate(games) if g['season'] in (2024,2025)])
 pooledV5=metrics([oldp[g['id']]['prob'] for g in games if g['season'] in (2024,2025)],[outcome[i] for i,g in enumerate(games) if g['season'] in (2024,2025)])
 boot=bootstrap_probability(paired);seasonGate=all(comparisons[str(y)]['candidate']['logLoss']-comparisons[str(y)]['v5']['logLoss']<=.002 for y in [2024,2025])
 gate={'pooledLogLossImprovement':pooledV5['logLoss']-pooledCandidate['logLoss'],'pooledAccuracyDelta':pooledCandidate['accuracy']-pooledV5['accuracy'],'completeSeasonGuard':seasonGate,'bootstrap':boot}
 gate['passed']=gate['pooledLogLossImprovement']>=.002 and gate['pooledAccuracyDelta']>=-.005 and seasonGate and boot['probabilityLowerLogLoss']>=.9
 protocol={'version':'5-research-5-stability','blueprintSha256':hashlib.sha256((ROOT/'analytics/STABILITY-REVIEW.md').read_bytes()).hexdigest(),'sourceManifest':json.loads(SOURCE_MANIFEST.read_text()),'candidateCount':len(candidates),'featureNames':NAMES,'families':FAMILIES,'ridges':[1.,10.,50.],'promotionGate':'>=0.002 pooled 2024-25 log-loss gain; <=0.002 loss in either complete season; >=-0.5pp pooled accuracy; >=90% week-bootstrap chance of lower loss.'}
 report={'protocol':protocol,'matchedGames':matched,'games':len(games),'coreCoverage':coreCoverage,'matchupCoverage':matchupCoverage,'passerCoverage':passerCoverage,'annual':annual,'comparisons':comparisons,'pooled2024To2025':{'candidate':pooledCandidate,'v5':pooledV5},'promotionGate':gate,'decision':'promote' if gate['passed'] else 'retain-v5'}
 CACHE.write_text(json.dumps(report,separators=(',',':'),allow_nan=False),encoding='utf-8');(ROOT/'analytics/stability-review-results.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
 print(json.dumps({'annual':annual,'comparisons':comparisons,'pooled':report['pooled2024To2025'],'gate':gate,'decision':report['decision']},indent=2))

if __name__=='__main__':main()
