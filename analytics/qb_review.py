"""Hierarchical, past-only observed-passer experiment."""
import json,math,re,hashlib,copy,argparse
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
from pipeline import ROOT,YEARS,load_data,metrics,sigmoid
import cohort_review as cohort
import ranking_review as r

CACHE=ROOT/'analytics/qb-review-cache.json'
NAMES=['Scoring strength','Opponent-adjusted EPA','Special teams','Results-based Elo','Recruiting composite','Blue-chip share','Non-explosive EPA','Turnover control','Observed passer prior efficiency','Observed passer prior experience','Home field','Rest days']
BASE_BUNDLES={'score':[0],'score_elo':[0,3],'score_epa_elo':[0,1,2,3],'robust_efficiency':[0,1,2,3,6,7]}

def parse_passer(row):
 def val(key,fallback):
  x=row.get(key);return row.get(fallback) if x is None or pd.isna(x) else x
 text=str(val('completions/passingAttempts','stat_1'));m=re.fullmatch(r'(\d+)\s*/\s*(\d+)',text)
 if not m:return None
 completions,attempts=map(int,m.groups())
 if not 0<=completions<=attempts or attempts<=0:return None
 try:
  yards=float(val('passingYards','stat_2'));td=float(val('passingTouchdowns','stat_4'));interceptions=float(val('interceptions','stat_5'))
 except (TypeError,ValueError):return None
 if not all(math.isfinite(v) for v in [yards,td,interceptions]) or min(td,interceptions)<0 or td+interceptions>attempts:return None
 return {'id':str(int(row['athlete_id'])),'attempts':attempts,'adjustedYards':yards+20*td-45*interceptions}

def passer_states(teams,seasons,boxes):
 states={};previous={};league=7.;coverage=[]
 for year in YEARS:
  df=pd.read_parquet(cohort.DATA/f'player_box_{year}.parquet');df=df[df.category=='passing'];assert not df.duplicated(['game_id','team_id','athlete_id']).any()
  groups=defaultdict(list);invalid=0
  for row in df.to_dict('records'):
   p=parse_passer(row)
   if p is None:invalid+=1;continue
   groups[(str(int(row['game_id'])),str(int(row['team_id'])))].append(p)
  validated={};rejected=0
  for key,ps in groups.items():
   box=boxes[year].get(key,{});m=re.fullmatch(r'(\d+)\s*[-/]\s*(\d+)',str(box.get('completionAttempts','')))
   if not m or sum(p['attempts'] for p in ps)!=int(m.group(2)):rejected+=1;continue
   validated[key]=ps
  latest={};totals=defaultdict(lambda:[0.,0.]);observedDates={};covered=0
  for week in seasons[year]['weeks']+[99]:
   batch=[g for g in seasons[year]['games'] if g['week']==week];cutoff=min((g['date'] for g in batch),default=None)
   snapshot={}
   for t in teams[year]:
    ps=latest.get(t,[]);att=sum(p['attempts'] for p in ps)
    if att:
     efficiency=experience=0.
     for p in ps:
      past=previous.get(p['id'],[0.,0.]);share=p['attempts']/att
      efficiency+=share*float(np.clip((past[1]+100*league)/(past[0]+100)-league,-5,5))
      experience+=share*math.log1p(past[0])/math.log(401)
     snapshot[t]={'values':[efficiency,experience],'observedThrough':observedDates[t],'priorSeason':year-1,'available':True}
     if cutoff:assert observedDates[t]<cutoff
    else:snapshot[t]={'values':[0.,0.],'observedThrough':None,'priorSeason':year-1,'available':False}
   states[f'{year}:{week}']=snapshot
   if week==99:break
   for g in batch:
    for t in [g['home'],g['away']]:
     ps=validated.get((g['id'],t))
     if ps and t in teams[year]:latest[t]=ps;observedDates[t]=g['date'];covered+=1
     elif t in teams[year]:latest.pop(t,None);observedDates.pop(t,None)
     if ps and g['fbs']:
      for p in ps:totals[p['id']][0]+=p['attempts'];totals[p['id']][1]+=p['adjustedYards']
  attempts=sum(v[0] for v in totals.values());league=sum(v[1] for v in totals.values())/attempts if attempts else 7.;previous=dict(totals)
  coverage.append({'season':year,'passingRows':len(df),'unusableOrZeroAttemptRows':invalid,'validatedTeamGameGroups':len(validated),'rejectedTeamGameGroups':rejected,'observedFbsTeamGames':covered,'priorPerformanceFbsAttempts':attempts})
 return states,coverage

def main():
 cohort.configure();r.NAMES=NAMES
 parser=argparse.ArgumentParser();parser.add_argument('--data',default=str(r.SOURCE_DATA));r.SOURCE_DATA=ROOT/Path(parser.parse_args().data)
 protocol={'version':'5-research-4-observed-passers','selection':'For each outer year, take the three best distinct rating configs in stage-three earlier-year validation. Test four component bundles x four passer treatments x two penalties = 96 candidates. Inner fits train only on previous years; choose pooled earlier-three-year log loss; refit through outerYear-1.','blueprintSha256':hashlib.sha256((ROOT/'analytics/QB-REVIEW.md').read_bytes()).hexdigest(),'sources':json.loads((cohort.DATA/'qb-sources.json').read_text()),'scope':'Hierarchical retrospective study requested after earlier experiments; no pristine holdout. Observed passers are not verified future starters. Individual passing efficiency is raw/shrunken, not opponent-adjusted QBR.'}
 path=ROOT/'analytics/qb-review-protocol.json'
 if path.exists():assert json.loads(path.read_text())==protocol
 else:path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
 parent=json.loads(cohort.CACHE.read_text())['report'];teams,seasons,talents,coverage=cohort.read_inputs();_,_,boxes,_=load_data(r.SOURCE_DATA);passers,passerCoverage=passer_states(teams,seasons,boxes)
 games=[g for y in YEARS for g in seasons[y]['games'] if g['fbs']];years=np.array([g['season'] for g in games]);outcomes=np.array([g['hs']>g['as'] for g in games],float)
 old={p['id']:p for p in json.loads((ROOT/'public/data/model-v4.json').read_text())['predictions']};stateCache={};xCache={};fitCache={};annual={};searches=[];predictions=[];selectedStates={}
 for year in [2023,2024,2025,2026]:
  options=next(s['candidates'] for s in parent['searches'] if s['targetSeason']==year);configs=[]
  for option in options:
   if option['ratingConfig'] not in configs:configs.append(option['ratingConfig'])
   if len(configs)==3:break
  candidates=[]
  for cfg in configs:
   key=json.dumps(cfg,sort_keys=True)
   if key not in stateCache:
    ss=cohort.build(teams,seasons,talents,cfg)
    for sk,states in ss.items():
     for t,s in states.items():s['q'].extend(passers[sk][t]['values']);s['passerContext']=passers[sk][t]
    stateCache[key]=ss
    xCache[key]=np.array([r.features(ss[f"{g['season']}:{g['week']}"][g['home']],ss[f"{g['season']}:{g['week']}"][g['away']],0 if g['neutral'] else 1,'prior',g['date']) for g in games])
   x=xCache[key]
   for base,idx in BASE_BUNDLES.items():
    for context,extra in [('none',[]),('passer_efficiency',[8]),('passer_experience',[9]),('passer_both',[8,9])]:
     indices=idx+extra+[10,11]
     for penalty in [1.,10.]:
      probabilities=np.full(len(games),np.nan);coefs={}
      for target in range(year-3,year+1):
       ck=(key,tuple(indices),penalty,target)
       if ck not in fitCache:
        tr=(years>=2019)&(years<target);fitCache[ck]=r.fit(x[tr],outcomes[tr],indices,penalty)
       coef=fitCache[ck];te=years==target;probabilities[te]=sigmoid(x[te]@coef);coefs[str(target)]=coef.tolist()
      val=(years>=year-3)&(years<year)
      candidates.append({'ratingConfig':cfg,'bundle':base,'passerTreatment':context,'ridge':penalty,'prob':probabilities,'coefs':coefs,'indices':indices,**metrics(probabilities[val],outcomes[val])})
  candidates.sort(key=lambda c:(c['logLoss'],len(c['indices'])));chosen=candidates[0];published=[{k:v for k,v in c.items() if k not in ['prob','coefs']} for c in candidates]
  annual[str(year)]={'selected':published[0],'coefficients':chosen['coefs'][str(year)],'trainingThrough':year-1,'validationYears':list(range(year-3,year)),'validation':published[0],'test':metrics(chosen['prob'][years==year],outcomes[years==year])}
  searches.append({'targetSeason':year,'candidates':published,'ratingPreselection':configs});ss=stateCache[json.dumps(chosen['ratingConfig'],sort_keys=True)];selectedStates[str(year)]={k:v for k,v in ss.items() if k.startswith(str(year)+':')}
  for i,g in enumerate(games):
   if g['season']!=year:continue
   o=old[g['id']];a,b=ss[f'{year}:{g["week"]}'][g['home']],ss[f'{year}:{g["week"]}'][g['away']];h=0 if g['neutral'] else 1.5
   p={k:v for k,v in g.items() if k!='units'};p.update(prob=float(chosen['prob'][i]),outcome=int(outcomes[i]),previousProb=o['prob'],v3Prob=o['previousProb'],benchmark=o['benchmark'],cutoff=o['cutoff'],homeScore=a['mu']+a['offense']-b['defense']+h,awayScore=a['mu']+b['offense']-a['defense']-h);p['margin']=p['homeScore']-p['awayScore'];p['actualMargin']=g['hs']-g['as'];predictions.append(p)
  print('SELECTED',year,json.dumps(annual[str(year)]),flush=True)
 report={'version':'5.0.0','protocol':protocol,'candidateCount':96,'earlierCandidateCounts':[432,576,1056],'coverage':coverage,'passerCoverage':passerCoverage,'cohortCoverage':json.loads((cohort.DATA/'cohort-coverage.json').read_text()),'featureNames':NAMES,'annual':annual,'searches':searches,'predictions':predictions,'scope':parent['scope']+' '+protocol['scope'],'cohortProtocol':parent['protocol']}
 CACHE.write_text(json.dumps({'states':selectedStates,'report':report},separators=(',',':'),allow_nan=False),encoding='utf-8')
 for year in [2023,2024,2025,2026]:
  ps=[p for p in predictions if p['season']==year]
  for name,key in [('v5','prob'),('v4','previousProb'),('v1','benchmark')]:print(year,name,metrics([p[key] for p in ps],[p['outcome'] for p in ps]),flush=True)
if __name__=='__main__':main()
