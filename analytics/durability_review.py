"""Unit-persistence and preseason-information research beyond v6."""
import csv,hashlib,json,math
from collections import defaultdict
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import spearmanr
from pipeline import ROOT,YEARS,load_data,metrics,sigmoid
import cohort_review as cohort
import qb_review as qb
import ranking_review as r
from opponent_stability_review import number
from stability_review import bootstrap_probability

DATA=ROOT/'analytics/research-durability';SOURCE_MANIFEST=ROOT/'analytics/durability-sources.json';CACHE=ROOT/'analytics/durability-review-cache.json'
UNIT_CONFIGS=[
 {'name':'v6','carry':.65,'lam':1.,'decay':.97},
 {'name':'carry0','carry':0.,'lam':1.,'decay':.97},{'name':'carry25','carry':.25,'lam':1.,'decay':.97},{'name':'carry45','carry':.45,'lam':1.,'decay':.97},
 {'name':'lambda05','carry':.65,'lam':.5,'decay':.97},{'name':'lambda2','carry':.65,'lam':2.,'decay':.97},{'name':'lambda4','carry':.65,'lam':4.,'decay':.97},
 {'name':'decay94','carry':.65,'lam':1.,'decay':.94},{'name':'decay100','carry':.65,'lam':1.,'decay':1.},
]
BUNDLES={'broad':[6,8,9,10,11,12,13],'first_down':[8,13],'yards':[11,13],'stable_pair':[6,8,13],'pass_rush':[9,10,13]}
STRUCTURES=['standard','split','decay4','decay8','decay12','rp4','rp8','rp_staff8','split_rp8']

def fit_unit(history,ids,prior,lam,carry,unit,decay):
 n=len(ids);ix={t:i for i,t in enumerate(ids)};po=np.array([prior.get(t,(0.,0.))[0]*carry for t in ids]);pd_=np.array([prior.get(t,(0.,0.))[1]*carry for t in ids]);o,d=po.copy(),pd_.copy();mu=28.
 if not history:return o,d,mu
 attack=[];defend=[];target=[];weight=[];latest=max(g['seq'] for g in history)
 for g in history:
  hv,av=g['units'][0][unit],g['units'][1][unit]
  if hv is None or av is None:continue
  attack.extend([ix[g['home']],ix[g['away']]]);defend.extend([ix[g['away']],ix[g['home']]]);target.extend([hv+28,av+28]);weight.extend([g['weight']*decay**(latest-g['seq'])]*2)
 if not target:return o,d,mu
 ai,di=np.array(attack),np.array(defend);y=np.array(target);w=np.array(weight);ac=np.bincount(ai,weights=w,minlength=n);dc=np.bincount(di,weights=w,minlength=n)
 for _ in range(180):
  old=np.r_[o,d,mu];o=(np.bincount(ai,weights=w*(y-mu+d[di]),minlength=n)+lam*po)/(ac+lam);d=(np.bincount(di,weights=w*(mu+o[ai]-y),minlength=n)+lam*pd_)/(dc+lam);mu=float((np.sum(w*(y-o[ai]+d[di]))+20*28)/(np.sum(w)+20))
  if np.max(np.abs(np.r_[o,d,mu]-old))<1e-7:break
 return o,d,mu

def build_states(teams,seasons,talents,cfg,unitcfg):
 states={};priors=[{} for _ in range(10)];elo={}
 for year in YEARS:
  ids=list(teams[year]);history=[];last={};counts={t:0 for t in ids};preScore={};elo={t:cfg['carry']*elo.get(t,0.) for t in ids}
  for seq,week in enumerate(seasons[year]['weeks']+[99]):
   oo=[];dd=[];mus=[]
   o,d,mu=r.fit_rating(history,ids,priors[0],cfg['lam'],3.,cfg['carry'],None,{t:cfg['talentPrior']*sum(talents[year][t][:2]) for t in ids});oo.append(o);dd.append(d);mus.append(mu)
   for unit in range(9):
    o,d,mu=fit_unit(history,ids,priors[unit+1],unitcfg['lam'],unitcfg['carry'],unit,unitcfg['decay']);oo.append(o);dd.append(d);mus.append(mu)
   state={}
   for i,t in enumerate(ids):
    tv=talents[year][t];state[t]={'q':[float(oo[0][i]+dd[0][i]),float(oo[1][i]+dd[1][i]),float(oo[2][i]+dd[2][i]),elo[t]/100,tv[0],tv[1],*[float(oo[j][i]+dd[j][i]) for j in range(3,len(oo))]],'offense':float(oo[0][i]),'defense':float(dd[0][i]),'mu':mus[0],'sample':counts[t],'lastDate':last.get(t),'calendar':seq,'talentMissing':tv[2]}
   if seq==0:preScore={t:state[t]['q'][0] for t in ids}
   for t in ids:state[t]['preseasonScore']=preScore[t]
   states[f'{year}:{week}']=state
   if week==99:
    priors=[{t:(float(oo[j][i]),float(dd[j][i])) for i,t in enumerate(ids)} for j in range(10)];break
   batch=[g for g in seasons[year]['games'] if g['week']==week];updates={t:0. for t in ids}
   for g in batch:
    for t in [g['home'],g['away']]:
     if t in state:last[t]=g['date']
    if not g['fbs']:continue
    a,b=state[g['home']],state[g['away']];h=0 if g['neutral'] else 3.;expected=a['q'][0]-b['q'][0]+h;prob=float(sigmoid(expected/8));margin=g['hs']-g['as'];total=g['hs']+g['as'];weight=1.
    history.append({**g,'seq':seq,'modelHome':(total+margin)/2,'modelAway':(total-margin)/2,'weight':weight});pe=float(sigmoid((elo[g['home']]-elo[g['away']]+(0 if g['neutral'] else 55))*math.log(10)/400));delta=40*(float(g['hs']>g['as'])-pe);updates[g['home']]+=delta;updates[g['away']]-=delta;counts[g['home']]+=1;counts[g['away']]+=1
   for t in ids:elo[t]+=updates[t]
 return states

def preseason_inputs(teams):
 manifest=json.loads(SOURCE_MANIFEST.read_text());out={};coverage=[]
 for entry in manifest:
  path=DATA/entry['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];frame=pd.read_parquet(path);year=int(frame.season.iloc[0]);raw={}
  for row in frame.to_dict('records'):
   for side in ['home','away']:
    tid=str(int(row[f'{side}_team_id']));vals=[row.get(f'{side}_ovr_rtprod'),row.get(f'{side}_hc_tenure'),row.get(f'{side}_oc_cont'),row.get(f'{side}_dc_cont')]
    if tid not in raw:raw[tid]=vals
  ids=list(teams[year]);rp={t:(float(raw[t][0]) if t in raw and pd.notna(raw[t][0]) else None) for t in ids};staff={t:((math.log1p(max(0,float(raw[t][1]))),float(raw[t][2])+float(raw[t][3])) if t in raw and all(pd.notna(v) for v in raw[t][1:]) else None) for t in ids}
  def standard(values):
   valid=np.array([v for v in values.values() if v is not None],float);mean=valid.mean(axis=0);sd=np.maximum(valid.std(axis=0),1e-9);z={t:float(np.mean((np.asarray(v)-mean)/sd)) for t,v in values.items() if v is not None};scale=max(np.std(list(z.values())),1e-9);return {t:z.get(t,0.)/scale for t in ids}
  out[year]={'returning':standard(rp),'staff':standard(staff)};coverage.append({'season':year,'teams':len(ids),'returningProduction':sum(v is not None for v in rp.values()),'staffContinuity':sum(v is not None for v in staff.values())})
 return out,coverage

def rest(state,date):
 if not state['lastDate']:return 7.
 return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(state['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))

def team_vector(state,pre,structure,bundle):
 q=state['q'];calendar=state['calendar'];pre_score=pre['score'];values=[];names=[]
 if structure=='standard' or structure.startswith('rp'):
  values.append(q[0]);names.append('Scoring strength')
 else:
  half=None if structure=='split' else float(structure.replace('decay','').replace('split_rp',''))
  fade=1. if half is None else math.exp(-calendar/half);values.extend([pre_score*fade,q[0]-pre_score]);names.extend(['Preseason scoring strength','In-season scoring change'])
 for index in BUNDLES[bundle]:values.append(q[index]);names.append(['','','','','','','Non-explosive EPA','Turnover control','First-down rate','Pass EPA','Rush EPA','Yards per play','Explosive rate','Observed passer prior efficiency'][index])
 if structure in ['rp4','rp8','rp_staff8','split_rp8']:
  half=4. if structure=='rp4' else 8.;values.append(pre['returning']*math.exp(-calendar/half));names.append('Returning production')
 if structure=='rp_staff8':values.append(pre['staff']*math.exp(-calendar/8));names.append('Staff continuity')
 return values,names

def design(g,states,preseason,structure,bundle):
 a=states[f"{g['season']}:{g['week']}"][g['home']];b=states[f"{g['season']}:{g['week']}"][g['away']];season=preseason[g['season']];pa={'returning':season['returning'][g['home']],'staff':season['staff'][g['home']],'score':a['preseasonScore']};pb={'returning':season['returning'][g['away']],'staff':season['staff'][g['away']],'score':b['preseasonScore']};av,names=team_vector(a,pa,structure,bundle);bv,_=team_vector(b,pb,structure,bundle)
 return [*(np.array(av)-np.array(bv)),0. if g['neutral'] else 1.,rest(a,g['date'])-rest(b,g['date'])],names+['Home field','Rest days']

def fit_model(x,y,penalty):
 scale=np.maximum(np.sqrt(np.mean(x*x,axis=0)),1e-6);z=x/scale;bounds=[(0,None)]*(x.shape[1]-1)+[(None,None)]
 def objective(b):
  logits=z@b;return np.logaddexp(0,logits).sum()-y@logits+penalty/2*(b@b),z.T@(sigmoid(logits)-y)+penalty*b
 result=minimize(objective,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',bounds=bounds,options={'ftol':1e-11,'gtol':1e-7,'maxiter':400})
 if not result.success:result=minimize(objective,result.x,jac=True,method='SLSQP',bounds=bounds,options={'ftol':1e-10,'maxiter':800})
 if not result.success:raise RuntimeError(result.message)
 return result.x/scale

def main():
 cohort.configure();r.UNIT_INDICES=list(range(9));teams,seasons,talents,coverage=cohort.read_inputs()
 for year in YEARS:
  raw=list(csv.DictReader((r.DIR/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig')));lookup={(v['game_id'],v['team_id']):v for v in raw}
  for g in seasons[year]['games']:
   for i,t in enumerate([g['home'],g['away']]):
    row=lookup.get((g['id'],t),{});g['units'][i].extend([number(row,'first_downs_created_rate'),number(row,'EPA_passing_per_play'),number(row,'EPA_rushing_per_play'),number(row,'yards_per_play'),number(row,'EPA_explosive_rate')])
 preseason,preCoverage=preseason_inputs(teams);_,_,boxes,_=load_data(r.SOURCE_DATA);passers,passerCoverage=qb.passer_states(teams,seasons,boxes);cfg=json.loads((ROOT/'public/data/model-v5.json').read_text())['annual']['2026']['selected']['ratingConfig']
 games=[g for y in YEARS if y>=2019 for g in seasons[y]['games'] if g['fbs']];yy=np.array([g['season'] for g in games]);outcome=np.array([g['hs']>g['as'] for g in games],float);candidates=[];stateCache={}
 for ci,unitcfg in enumerate(UNIT_CONFIGS):
  states=build_states(teams,seasons,talents[cfg['talentMode']],cfg,unitcfg)
  for key,snapshot in states.items():
   for t,state in snapshot.items():state['q'].extend(passers[key][t]['values'])
  stateCache[ci]=states
  for bundle in BUNDLES:
   for structure in STRUCTURES:
    rows=[design(g,states,preseason,structure,bundle) for g in games];x=np.array([row[0] for row in rows]);featureNames=rows[0][1]
    for penalty in [1.,10.,50.]:
     prob=np.full(len(games),np.nan);coefs={}
     for year in range(2020,2027):
      tr=(yy>=2019)&(yy<year);te=yy==year;coef=fit_model(x[tr],outcome[tr],penalty);prob[te]=sigmoid(x[te]@coef);coefs[str(year)]=coef.tolist()
     candidates.append({'unitIndex':ci,'unitConfig':unitcfg,'bundle':bundle,'structure':structure,'ridge':penalty,'featureNames':featureNames,'prob':prob,'coefs':coefs})
  print('STATE',ci+1,'/',len(UNIT_CONFIGS),unitcfg['name'],flush=True)
 old=json.loads((ROOT/'analytics/opponent-stability-review-results.json').read_text());oldp={p['id']:p for p in old['predictions']};annual={};selected={};predictions=[]
 for year in [2023,2024,2025,2026]:
  val=(yy>=year-3)&(yy<year);test=yy==year;ordered=sorted(candidates,key=lambda c:(metrics(c['prob'][val],outcome[val])['logLoss'],len(c['featureNames']),c['ridge']));choice=ordered[0];selected[year]=choice
  annual[str(year)]={'selected':{k:choice[k] for k in ['unitIndex','unitConfig','bundle','structure','ridge','featureNames']},'validationYears':list(range(year-3,year)),'trainingThrough':year-1,'validation':metrics(choice['prob'][val],outcome[val]),'test':metrics(choice['prob'][test],outcome[test]),'coefficients':choice['coefs'][str(year)],'topCandidates':[{**{k:c[k] for k in ['unitIndex','unitConfig','bundle','structure','ridge','featureNames']},**metrics(c['prob'][val],outcome[val])} for c in ordered[:12]]}
  for i in np.where(test)[0]:
   prev=oldp[games[i]['id']];predictions.append({'id':games[i]['id'],'season':year,'week':games[i]['week'],'prob':float(choice['prob'][i]),'v6Prob':prev['prob'],'v5Prob':prev['v5Prob'],'v1Prob':prev['v1Prob'],'outcome':int(outcome[i])})
 comparisons={};paired=[]
 for year in [2023,2024,2025,2026]:
  rows=[p for p in predictions if p['season']==year];comparisons[str(year)]={key:metrics([p[col] for p in rows],[p['outcome'] for p in rows]) for key,col in [('candidate','prob'),('v6','v6Prob'),('v5','v5Prob'),('v1','v1Prob')]}
  if year<=2025:
   for p in rows:
    y=p['outcome'];q1=np.clip(p['prob'],1e-9,1-1e-9);q0=np.clip(p['v6Prob'],1e-9,1-1e-9);paired.append({'season':year,'week':p['week'],'candidateLoss':float(-y*np.log(q1)-(1-y)*np.log(1-q1)),'v5Loss':float(-y*np.log(q0)-(1-y)*np.log(1-q0))})
 pooled=[p for p in predictions if p['season']<=2025];pc=metrics([p['prob'] for p in pooled],[p['outcome'] for p in pooled]);pv=metrics([p['v6Prob'] for p in pooled],[p['outcome'] for p in pooled]);boot=bootstrap_probability(paired,seed=20260926);guard=all(comparisons[str(y)]['candidate']['logLoss']-comparisons[str(y)]['v6']['logLoss']<=.003 for y in [2023,2024,2025]);gate={'pooledLogLossImprovement':pv['logLoss']-pc['logLoss'],'pooledAccuracyDelta':pc['accuracy']-pv['accuracy'],'completeSeasonGuard':guard,'bootstrap':boot};gate['passed']=gate['pooledLogLossImprovement']>=.0015 and gate['pooledAccuracyDelta']>=-.005 and guard and boot['probabilityLowerLogLoss']>=.9
 choice=selected[2026];ss=stateCache[choice['unitIndex']];latest=ss['2026:99'];coef=np.array(choice['coefs']['2026']);strength={}
 for t,s in latest.items():
  vals,_=team_vector(s,{'returning':preseason[2026]['returning'][t],'staff':preseason[2026]['staff'][t],'score':s['preseasonScore']},choice['structure'],choice['bundle']);strength[t]=float(np.array([*vals,0.,0.])@coef)
 fpi=json.loads((ROOT/'public/data/fpi-reference.json').read_text());published=json.loads((ROOT/'public/data/2026.json').read_text());pub={t['id']:t['modelRank'] for t in published['snapshots']['99']['teams']};rows=[x for x in fpi['teams'] if x['id'] in strength];order={t:i+1 for i,t in enumerate(sorted(strength,key=lambda t:(-strength[t],t)))};fpiDiag={}
 for name,ranks in [('v6',pub),('candidate',order)]:fpiDiag[name]={'meanAbsoluteRankGap':float(np.mean([abs(ranks[x['id']]-x['rank']) for x in rows])),'spearman':float(spearmanr([ranks[x['id']] for x in rows],[x['rank'] for x in rows]).statistic)}
 protocol={'version':'6-research-7-durability','blueprintSha256':hashlib.sha256((ROOT/'analytics/DURABILITY-REVIEW.md').read_bytes()).hexdigest(),'sourceManifest':json.loads(SOURCE_MANIFEST.read_text()),'unitConfigurations':UNIT_CONFIGS,'bundles':BUNDLES,'structures':STRUCTURES,'ridges':[1.,10.,50.],'candidateCount':len(candidates)}
 report={'protocol':protocol,'coverage':coverage,'preseasonCoverage':preCoverage,'passerCoverage':passerCoverage,'annual':annual,'comparisons':comparisons,'predictions':predictions,'pooled2023To2025':{'candidate':pc,'v6':pv},'promotionGate':gate,'fpiDiagnostic':fpiDiag,'decision':'promote' if gate['passed'] else 'retain-v6','scope':'Retrospective study after inspection of v6 results; no pristine holdout. FPI is diagnostic only.'};CACHE.write_text(json.dumps(report,separators=(',',':'),allow_nan=False));(ROOT/'analytics/durability-review-results.json').write_text(json.dumps(report,indent=2,allow_nan=False));print(json.dumps({'annual':annual,'comparisons':comparisons,'pooled':report['pooled2023To2025'],'gate':gate,'fpi':fpiDiag,'decision':report['decision']},indent=2))

if __name__=='__main__':main()
