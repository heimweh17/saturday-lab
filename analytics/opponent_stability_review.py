"""Opponent-adjusted follow-up to the raw pregame stability search."""
import csv,hashlib,json,math
from datetime import datetime
import numpy as np
from pipeline import ROOT,YEARS,load_data,metrics,sigmoid
import cohort_review as cohort
import qb_review as qb
import ranking_review as r
from stability_review import bootstrap_probability

CACHE=ROOT/'analytics/opponent-stability-review-cache.json'
UNITS=['non_explosive_epa','first_down_rate','pass_epa','rush_epa','yards_per_play','explosive_rate']
NAMES=['Scoring strength','Opponent-adjusted EPA','Special teams','Results-based Elo','Recruiting composite','Blue-chip share','Non-explosive EPA','Turnover control','First-down rate','Pass EPA','Rush EPA','Yards per play','Explosive rate','Observed passer prior efficiency','Observed passer prior experience','Home field','Rest days']
BUNDLES={
 'baseline':[0,13,15,16],
 'non_explosive':[0,6,13,15,16],
 'first_down':[0,8,13,15,16],
 'stable_pair':[0,6,8,13,15,16],
 'pass_rush':[0,9,10,13,15,16],
 'yards':[0,11,13,15,16],
 'explosive':[0,12,13,15,16],
 'broad':[0,6,8,9,10,11,12,13,15,16],
}

def number(row,key):
 try:
  value=float(row[key]);return value if math.isfinite(value) else None
 except (KeyError,TypeError,ValueError):return None

def rest(state,date):
 if not state['lastDate']:return 7.
 return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(state['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))

def main():
 cohort.configure();r.NAMES=NAMES;r.UNIT_INDICES=list(range(9))
 teams,seasons,talents,coverage=cohort.read_inputs()
 for year in YEARS:
  rows=list(csv.DictReader((r.DIR/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig')));lookup={(v['game_id'],v['team_id']):v for v in rows}
  for g in seasons[year]['games']:
   for i,t in enumerate([g['home'],g['away']]):
    row=lookup.get((g['id'],t),{})
    g['units'][i].extend([number(row,'first_downs_created_rate'),number(row,'EPA_passing_per_play'),number(row,'EPA_rushing_per_play'),number(row,'yards_per_play'),number(row,'EPA_explosive_rate')])
 cfg=json.loads((ROOT/'lib/production-config.json').read_text())['selected']['ratingConfig'];states=cohort.build(teams,seasons,talents,cfg)
 _,_,boxes,_=load_data(r.SOURCE_DATA);passers,passerCoverage=qb.passer_states(teams,seasons,boxes)
 for key,snapshot in states.items():
  for team,state in snapshot.items():state['q'].extend(passers[key][team]['values'])
 games=[g for year in YEARS if year>=2019 for g in seasons[year]['games'] if g['fbs']];yy=np.array([g['season'] for g in games]);outcome=np.array([g['hs']>g['as'] for g in games],float)
 x=[]
 for g in games:
  a=states[f"{g['season']}:{g['week']}"][g['home']];b=states[f"{g['season']}:{g['week']}"][g['away']]
  x.append([*(np.array(a['q'])-np.array(b['q'])),0. if g['neutral'] else 1.,rest(a,g['date'])-rest(b,g['date'])])
 x=np.array(x);assert x.shape[1]==len(NAMES)
 candidates=[]
 for bundle,indices in BUNDLES.items():
  for ridge in [1.,10.,50.]:
   prob=np.full(len(games),np.nan);coefs={}
   for year in range(2020,2027):
    tr=(yy>=2019)&(yy<year);te=yy==year;coef=r.fit(x[tr],outcome[tr],indices,ridge);prob[te]=sigmoid(x[te]@coef);coefs[str(year)]=coef.tolist()
   candidates.append({'bundle':bundle,'ridge':ridge,'indices':indices,'prob':prob,'coefs':coefs})
 annual={};selected={}
 for year in [2023,2024,2025,2026]:
  val=(yy>=year-3)&(yy<year);test=yy==year;ordered=sorted(candidates,key=lambda c:(metrics(c['prob'][val],outcome[val])['logLoss'],len(c['indices']),c['ridge']));choice=ordered[0];selected[year]=choice['prob']
  annual[str(year)]={'selected':{k:choice[k] for k in ['bundle','ridge','indices']},'validationYears':list(range(year-3,year)),'trainingThrough':year-1,'validation':metrics(choice['prob'][val],outcome[val]),'test':metrics(choice['prob'][test],outcome[test]),'coefficients':choice['coefs'][str(year)],'topCandidates':[{**{k:c[k] for k in ['bundle','ridge','indices']},**metrics(c['prob'][val],outcome[val])} for c in ordered[:8]]}
 old=json.loads(qb.CACHE.read_text())['report'];oldp={p['id']:p for p in old['predictions']};comparisons={};paired=[];predictions=[]
 for year in [2023,2024,2025,2026]:
  mask=yy==year;ids=np.where(mask)[0];p=selected[year][mask];v5=np.array([oldp[games[i]['id']]['prob'] for i in ids]);y=outcome[mask];comparisons[str(year)]={'candidate':metrics(p,y),'v5':metrics(v5,y)}
  for j,i in enumerate(ids):predictions.append({'id':games[i]['id'],'season':year,'week':games[i]['week'],'prob':float(p[j]),'v5Prob':float(v5[j]),'v4Prob':float(oldp[games[i]['id']]['previousProb']),'v1Prob':float(oldp[games[i]['id']]['benchmark']),'outcome':int(y[j])})
  if year in (2024,2025):
   for j,i in enumerate(ids):
    q1=np.clip(p[j],1e-9,1-1e-9);q0=np.clip(v5[j],1e-9,1-1e-9);actual=y[j];paired.append({'season':year,'week':games[i]['week'],'candidateLoss':float(-actual*np.log(q1)-(1-actual)*np.log(1-q1)),'v5Loss':float(-actual*np.log(q0)-(1-actual)*np.log(1-q0))})
 take=np.isin(yy,[2024,2025]);pc=np.concatenate([selected[2024][yy==2024],selected[2025][yy==2025]]);pv=np.array([oldp[g['id']]['prob'] for g in games if g['season'] in (2024,2025)]);pooledCandidate=metrics(pc,outcome[take]);pooledV5=metrics(pv,outcome[take]);boot=bootstrap_probability(paired,seed=20260925)
 gate={'pooledLogLossImprovement':pooledV5['logLoss']-pooledCandidate['logLoss'],'pooledAccuracyDelta':pooledCandidate['accuracy']-pooledV5['accuracy'],'completeSeasonGuard':all(comparisons[str(y)]['candidate']['logLoss']-comparisons[str(y)]['v5']['logLoss']<=.002 for y in [2024,2025]),'bootstrap':boot}
 gate['passed']=gate['pooledLogLossImprovement']>=.002 and gate['pooledAccuracyDelta']>=-.005 and gate['completeSeasonGuard'] and boot['probabilityLowerLogLoss']>=.9
 protocol={'version':'5-research-6-opponent-stability','blueprintSha256':hashlib.sha256((ROOT/'analytics/OPPONENT-STABILITY-REVIEW.md').read_bytes()).hexdigest(),'candidateCount':len(candidates),'features':NAMES,'bundles':BUNDLES,'ridges':[1.,10.,50.]}
 report={'protocol':protocol,'coverage':coverage,'passerCoverage':passerCoverage,'annual':annual,'comparisons':comparisons,'predictions':predictions,'pooled2024To2025':{'candidate':pooledCandidate,'v5':pooledV5},'promotionGate':gate,'decision':'promote' if gate['passed'] else 'retain-v5','scope':'Retrospective research on inspected seasons. Target-week outcomes are excluded from every snapshot; the 2026 evaluation is partial.'}
 CACHE.write_text(json.dumps(report,separators=(',',':'),allow_nan=False));(ROOT/'analytics/opponent-stability-review-results.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({'annual':annual,'comparisons':comparisons,'pooled':report['pooled2024To2025'],'gate':gate,'decision':report['decision']},indent=2))

if __name__=='__main__':main()
