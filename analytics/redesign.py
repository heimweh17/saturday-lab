"""Opponent-adjusted unit research with forward-only yearly model selection."""
import json,csv,math,hashlib,itertools,argparse
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from pipeline import ROOT,YEARS,load_data,ridge_fit,sigmoid,metrics
from box_export import parse
DATA=ROOT/'analytics/research-v4'
NAMES=['Scoring strength','EPA offense/defense','Passing EPA','Rushing EPA','Special teams EPA','Yards/play strength','Recruiting talent','Blue-chip share','Home field','Rest days','Early-season talent','Nonlinear scoring strength','Talent coverage flag']
BUNDLES={'score':[0,8,9],'score_talent':[0,6,7,8,9,10,12],'epa':[0,1,4,8,9],'epa_talent':[0,1,4,6,7,8,9,10,12],'units':[0,2,3,4,5,8,9,11],'units_talent':list(range(13))}
CONFIGS=[dict(method=m,carry=c,lam=l,memory=k,decay=.97) for m,c,l,k in itertools.product(['raw','cap28','soft28'],[.4,.65],[1.,4.],[1,3])]

def fit(x,y,indices,penalty):
    a=np.asarray(x)[:,indices];scale=np.maximum(np.sqrt(np.mean(a*a,axis=0)),1e-6);z=a/scale;y=np.asarray(y);b=np.zeros(len(indices))
    for _ in range(80):
        p=sigmoid(z@b);g=z.T@(p-y)+penalty*b;h=(z.T*(p*(1-p)))@z+penalty*np.eye(len(b));step=np.linalg.solve(h,g);b-=step
        if np.max(np.abs(step))<1e-8:break
    coef=np.zeros(len(NAMES));coef[indices]=b/scale;return coef

def features(a,b,loc,date=None):
    def rest(s):
        if not date or not s['lastDate']:return 7.
        return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(s['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))
    v=np.array(a['v'])-np.array(b['v']);return [*v[:8],float(loc),rest(a)-rest(b),v[6]*math.exp(-min(a['sample'],b['sample'])/4),20*math.tanh(v[0]/20),float(a.get('talentMissing',False))-float(b.get('talentMissing',False))]

def transformed(g,method):
    margin=g['hs']-g['as'];total=g['hs']+g['as']
    if method=='cap28':margin=np.clip(margin,-28,28)
    if method=='soft28':margin=28*np.tanh(margin/28)
    return {**g,'hs':float((total+margin)/2),'as':float((total-margin)/2)}

def scoring(teams,seasons,cfg):
    finals=[];states={}
    for year in YEARS:
        ids=list(teams[year]);recent=finals[-cfg['memory']:];weights=[.5**i for i in range(len(recent))]
        prior={t:tuple(sum(w*f.get(t,(0,0))[j] for w,f in zip(weights,reversed(recent)))/sum(weights) for j in (0,1)) for t in ids} if recent else {}
        history=[]
        for seq,week in enumerate(seasons[year]['weeks']+[99]):
            o,d,mu=ridge_fit(history,ids,prior,cfg['lam'],3.,cfg['decay'],carry=cfg['carry']);states[f'{year}:{week}']={t:[float(o[i]),float(d[i]),mu] for i,t in enumerate(ids)}
            if week==99:finals.append({t:(float(o[i]),float(d[i])) for i,t in enumerate(ids)});break
            history.extend({**transformed(g,cfg['method']),'seq':seq} for g in seasons[year]['games'] if g['week']==week and g['fbs'])
    return states

def unit_states(teams,seasons,boxes):
    states={};prev={};coverage=[];allraw={};talents={}
    for year in YEARS:
        with (DATA/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig') as source:raw=list(csv.DictReader(source))
        by={(r['game_id'],r['team_id']):r for r in raw};assert len(by)==len(raw),'Duplicate EPA game/team rows';allraw[year]=by
        tf=pd.read_parquet(DATA/f'cfb_team_talent_{year}.parquet');tal={str(r['team_id']):r for r in tf.to_dict('records')};talents[year]=tal;ids=list(teams[year]);history=[];count=0
        for seq,week in enumerate(seasons[year]['weeks']+[99]):
            units={t:[] for t in ids}
            for j in range(5):
                hs=[{**g,'hs':g['hv'][j]+28,'as':g['av'][j]+28} for g in history if g['hv'][j] is not None and g['av'][j] is not None]
                pr={t:(v[j*2],v[j*2+1]) for t,v in prev.items()};o,d,_=ridge_fit(hs,ids,pr,2.,0.,.97,carry=.65)
                for i,t in enumerate(ids):units[t].extend([float(o[i]),float(d[i])])
            state={}
            for t in ids:
                played=[g for g in history if t in (g['home'],g['away'])];pastweeks=seasons[year]['weeks'][:seq];dates=[g['date'] for g in seasons[year]['games'] if g['week'] in pastweeks and t in (g['home'],g['away'])];tv=tal.get(t,{})
                state[t]={'units':units[t],'sample':len(played),'lastDate':max(dates,default=None),'talent':float(tv.get('talent_composite',np.mean([tal[k]['talent_composite'] for k in ids if k in tal]))),'blue':float(tv.get('blue_chip_ratio',np.mean([tal[k]['blue_chip_ratio'] for k in ids if k in tal]))),'talentMissing':t not in tal}
            states[f'{year}:{week}']=state
            if week==99:prev=units;break
            for g in seasons[year]['games']:
                if g['week']!=week or not g['fbs']:continue
                vals=[]
                for tid in [g['home'],g['away']]:
                    r=by.get((g['id'],tid),{});b=parse(boxes[year].get((g['id'],tid)),0)
                    def n(key):
                        try:return float(r[key])
                        except (KeyError,ValueError,TypeError):return None
                    # EPA sourced from upstream cfbfastR, not ESPN proprietary EPA.
                    vals.append([n('EPA_per_play'),n('EPA_passing_per_play'),n('EPA_rushing_per_play'),n('EPA_sp'),b.get('yardsPerPlay') if b else None])
                count+=int(vals[0][0] is not None and vals[1][0] is not None)
                history.append({**g,'seq':seq,'hv':vals[0],'av':vals[1]})
        coverage.append({'year':year,'games':sum(g['fbs'] for g in seasons[year]['games']),'epaPairedGames':count,'talentTeams':sum(t in tal for t in ids),'teams':len(ids)})
    return states,coverage

def merge(score,units):
    states={}
    for key,ss in score.items():
        states[key]={}
        for t,s in ss.items():
            u=units[key][t];nets=[sum(u['units'][j*2:j*2+2]) for j in range(5)]
            states[key][t]={'v':[s[0]+s[1],*nets,u['talent']/1000,u['blue']],'offense':s[0],'defense':s[1],'mu':s[2],'sample':u['sample'],'lastDate':u['lastDate'],'talentMissing':u['talentMissing']}
    return states

def main():
    protocol={'version':'4-research-coverage-correction','ratingConfigurations':CONFIGS,'featureBundles':BUNDLES,'ridges':[1.,10.],'features':NAMES,'selection':'For each outer year 2023-2026, minimum pooled log loss over previous three years; each fold trains coefficients on 2019 through foldYear-1. Refit winner through outerYear-1.','coverageCorrection':'Missing signed-class talent is imputed to the same-season FBS mean with an explicit missing indicator; preliminary zero-imputation run superseded before deployment.', 'scope':'Retrospective corrected upstream data; EPA source model may have been fitted on later data. No pristine prospective claim. Returning-production files excluded because same-season participation leaks roster availability. Recruiting composite is a signed-class proxy, not transfer-adjusted roster talent. FPI never used as training label.'}
    path=ROOT/'analytics/redesign-protocol.json'
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==protocol
    else:path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--data',default=str(ROOT.parent/'research/data'));args=parser.parse_args();teams,seasons,boxes,_=load_data(Path(args.data));units,coverage=unit_states(teams,seasons,boxes)
    games=[g for y in YEARS for g in seasons[y]['games'] if g['fbs']];yeararr=np.array([g['season'] for g in games]);y=np.array([g['hs']>g['as'] for g in games],float);allc=[];arrays={};beststates={};annual={};reports=[]
    for ci,cfg in enumerate(CONFIGS):
        states=merge(scoring(teams,seasons,cfg),units);x=np.array([features(states[f"{g['season']}:{g['week']}"][g['home']],states[f"{g['season']}:{g['week']}"][g['away']],0 if g['neutral'] else 1,g['date']) for g in games]);arrays[ci]=x
        for name,idx in BUNDLES.items():
            for ridge in [1.,10.]:
                ps=np.full(len(games),np.nan);coefs={}
                for year in range(2020,2027):
                    tr=(yeararr>=2019)&(yeararr<year);te=yeararr==year;coef=fit(x[tr],y[tr],idx,ridge);coefs[year]=coef.tolist();ps[te]=sigmoid(x[te]@coef)
                allc.append({'rating':ci,'bundle':name,'ridge':ridge,'prob':ps,'coefs':coefs})
        print('Rating variants',ci+1,'/',len(CONFIGS),flush=True)
    predictions=[]
    for year in [2023,2024,2025,2026]:
        val=(yeararr>=year-3)&(yeararr<year);test=yeararr==year;ranked=sorted(allc,key=lambda c:metrics(c['prob'][val],y[val])['logLoss']);win=ranked[0];cfg=CONFIGS[win['rating']];states=merge(scoring(teams,seasons,cfg),units);beststates[year]={k:v for k,v in states.items() if k.startswith(str(year)+':')}
        annual[str(year)]={'ratingConfig':cfg,'ratingIndex':win['rating'],'bundle':win['bundle'],'ridge':win['ridge'],'coefficients':win['coefs'][year],'trainingThrough':year-1,'validationYears':list(range(year-3,year)),'validation':metrics(win['prob'][val],y[val]),'test':metrics(win['prob'][test],y[test])}
        reports.append({'year':year,'candidates':[{'ratingConfig':CONFIGS[c['rating']],'bundle':c['bundle'],'ridge':c['ridge'],**metrics(c['prob'][val],y[val])} for c in ranked]})
        for i,g in enumerate(games):
            if g['season']==year:predictions.append({**g,'prob':float(win['prob'][i]),'outcome':int(y[i])})
        print('SELECTED',year,json.dumps(annual[str(year)]),flush=True)
    report={'protocol':protocol,'coverage':coverage,'annual':annual,'searches':reports,'predictions':predictions,'candidateCount':len(allc)}
    (ROOT/'analytics/redesign-cache.json').write_text(json.dumps({'states':beststates,'report':report},separators=(',',':')),encoding='utf-8')
    (ROOT/'public/data/redesign.json').write_text(json.dumps(report,separators=(',',':')),encoding='utf-8')
if __name__=='__main__':main()
