"""Recruiting-age ablations and robust efficiency, using the same forward protocol."""
import csv,hashlib,itertools,json
import numpy as np
import pandas as pd
from pipeline import ROOT,YEARS
from box_export import parse
import ranking_review as r

CACHE=ROOT/'analytics/cohort-review-cache.json'
DATA=ROOT/'analytics/research-roster'
COHORTS={'equal':[1,1,1,1,0],'developmental':[.25,.75,1,1,0],'no_freshmen':[0,1,1,1,0],'lagged_four':[0,1,1,1,1]}
CORE_READ=r.read_inputs
CORE_BUILD=r.build

def standardize(values,ids):
    valid=[v for v in values.values() if v is not None]
    mean=np.mean(valid,axis=0);sd=np.maximum(np.std(valid,axis=0),1e-9)
    scores={t:float(np.mean((np.array(values[t])-mean)/sd)) for t in ids if values.get(t) is not None}
    scale=max(float(np.std(list(scores.values()))),1e-9)
    return {t:[scores.get(t,0.)/scale,0.,t not in scores] for t in ids}

def read_inputs():
    r.verify_files(ROOT/'analytics/extended-sources.json',DATA)
    teams,seasons,original,coverage=CORE_READ();talents={k:{} for k in ['none','published',*COHORTS]};classes={};cohortCoverage=[]
    for year in range(2014,2027):
        frame=pd.read_parquet(DATA/f'cfb_recruits_{year}.parquet');assert not frame.duplicated(['season','recruit_id']).any()
        frame=frame[frame['stars'].isin([2.,3.,4.,5.])&frame.team_id.notna()].copy();frame['blue']=frame.stars>=4
        classes[year]={str(t):(float(g.stars.sum()),float(g.blue.sum()),len(g)) for t,g in frame.groupby('team_id')}
    from pipeline import load_data
    _,_,boxes,_=load_data(r.SOURCE_DATA)
    for year in YEARS:
        ids=list(teams[year]);talents['none'][year]={t:[0.,0.,False] for t in ids}
        talents['published'][year]=standardize({t:None if v[2] else [v[0]+v[1]] for t,v in original[year].items()},ids)
        for name,weights in COHORTS.items():
            values={}
            for t in ids:
                records=[(w,classes[year-lag].get(t)) for lag,w in enumerate(weights) if w]
                valid=[(w,c) for w,c in records if c is not None]
                # A partial signed-class history is not silently treated as a complete cohort.
                if len(valid)!=len(records):values[t]=None;continue
                count=sum(w*c[2] for w,c in valid)
                values[t]=[sum(w*c[0] for w,c in valid)/count,sum(w*c[1] for w,c in valid)/count] if count else None
            talents[name][year]=standardize(values,ids)
            cohortCoverage.append({'season':year,'mode':name,'teams':len(ids),'covered':sum(v is not None for v in values.values())})
        raw=list(csv.DictReader((r.DIR/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig')));lookup={(v['game_id'],v['team_id']):v for v in raw}
        for g in seasons[year]['games']:
            for i,t in enumerate([g['home'],g['away']]):
                row=lookup.get((g['id'],t),{});box=parse(boxes[year].get((g['id'],t)),0)
                try:nonexplosive=float(row['EPA_non_explosive_per_play']);nonexplosive=nonexplosive if np.isfinite(nonexplosive) else None
                except (KeyError,ValueError):nonexplosive=None
                turnovers=box.get('turnovers') if box else None
                g['units'][i].extend([nonexplosive,-float(turnovers) if turnovers is not None else None])
    (DATA/'cohort-coverage.json').write_text(json.dumps(cohortCoverage,indent=2),encoding='utf-8')
    return teams,seasons,talents,coverage

def build(teams,seasons,talents,cfg):return CORE_BUILD(teams,seasons,talents[cfg['talentMode']],cfg)

def configure():
    r.CACHE=CACHE;r.RUN_NAME='cohort-review';r.UNIT_INDICES=[0,1,2,3]
    priors=[('none',0.)]+[(m,w) for m in ['published',*COHORTS] for w in [2.,4.]]
    r.CONFIGS=[dict(carry=c,lam=l,method=m,weight=w,talentMode=mode,talentPrior=tp,memory=1,decay=.97) for c,l,(m,w),(mode,tp) in itertools.product([.35,.65],[2.,4.],[('raw','uniform'),('raw','mismatch'),('residual28','uniform')],priors)]
    r.NAMES=['Scoring strength','Opponent-adjusted EPA','Special teams','Results-based Elo','Recruiting composite','Blue-chip share','Non-explosive EPA','Turnover control','Home field','Rest days']
    r.BUNDLES={'score':[0,8,9],'score_elo':[0,3,8,9],'score_epa_elo':[0,1,2,3,8,9],'robust_efficiency':[0,1,2,3,6,7,8,9]}
    r.PROTOCOL_EXTRA={'version':'5-research-3-cohorts','calendarDecay':'None. Recruiting only affects the scoring prior.', 'priorDefinition':'carry * previous final net rating + talentPrior * standardized cohort proxy, split equally between offense/defense.', 'stageThreeReason':'User requested freshman/age/roster ablations after the first two experiments. All results remain exploratory retrospective evidence.', 'cohortWeights':COHORTS,'stageThreeBlueprintSha256':hashlib.sha256((ROOT/'analytics/COHORT-REVIEW.md').read_bytes()).hexdigest(),'additionalSources':json.loads((DATA/'sources.json').read_text())}
    r.read_inputs=read_inputs;r.build=build
if __name__=='__main__':configure();r.main()
