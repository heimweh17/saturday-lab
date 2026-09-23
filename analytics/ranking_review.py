"""Frozen, opponent-aware scalar-strength search. No school-specific rules."""
import csv,json,math,itertools,hashlib,argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from pipeline import ROOT,YEARS,load_data,sigmoid,metrics

DIR=ROOT/'analytics/research-v4'
NAMES=['Scoring strength','Opponent-adjusted EPA','Special teams','Results-based Elo','Recruiting composite','Blue-chip share','Home field','Rest days']
BUNDLES={'score':[0,6,7],'score_elo':[0,3,6,7],'score_epa':[0,1,2,6,7],'score_epa_elo':[0,1,2,3,6,7],'all_constant':list(range(8)),'all_calendar':list(range(8))}
CONFIGS=[dict(carry=c,lam=l,method=m,weight=w,memory=1,decay=.97) for c,l,m,w in itertools.product([0.,.35,.65],[1.,4.],['raw','cap28','residual28'],['uniform','mismatch'])]
CACHE=ROOT/'analytics/ranking-review-cache.json'
RUN_NAME='ranking-review'
PROTOCOL_EXTRA={}
UNIT_INDICES=[0,1]
SOURCE_DATA=ROOT.parent/'research/data'

def fit_rating(history,ids,prior,lam,home,carry,unit=None,prior_shift=None):
    n=len(ids);ix={t:i for i,t in enumerate(ids)}
    po=np.array([prior.get(t,(0.,0.))[0]*carry for t in ids]);pd_=np.array([prior.get(t,(0.,0.))[1]*carry for t in ids])
    if prior_shift:
        shift=np.array([prior_shift.get(t,0.)/2 for t in ids]);po+=shift;pd_+=shift
    o,d=po.copy(),pd_.copy();mu=28.
    if not history:return o,d,mu
    attack=[];defend=[];target=[];weight=[];latest=max(g['seq'] for g in history)
    for g in history:
        if unit is None:hs,aws=g['modelHome'],g['modelAway']
        else:
            hv,av=g['units'][0][unit],g['units'][1][unit]
            if hv is None or av is None:continue
            hs,aws=hv+28,av+28
        adv=0 if g['neutral'] else home/2
        attack.extend([ix[g['home']],ix[g['away']]]);defend.extend([ix[g['away']],ix[g['home']]])
        target.extend([hs-adv,aws+adv]);weight.extend([g['weight']*.97**(latest-g['seq'])]*2)
    if not target:return o,d,mu
    ai,di=np.array(attack),np.array(defend);y=np.array(target);w=np.array(weight)
    ac=np.bincount(ai,weights=w,minlength=n);dc=np.bincount(di,weights=w,minlength=n)
    for _ in range(180):
        old=np.r_[o,d,mu]
        o=(np.bincount(ai,weights=w*(y-mu+d[di]),minlength=n)+lam*po)/(ac+lam)
        d=(np.bincount(di,weights=w*(mu+o[ai]-y),minlength=n)+lam*pd_)/(dc+lam)
        mu=float((np.sum(w*(y-o[ai]+d[di]))+20*28)/(np.sum(w)+20))
        if np.max(np.abs(np.r_[o,d,mu]-old))<1e-7:break
    return o,d,mu

def verify_files(manifest,folder):
    for entry in json.loads(manifest.read_text()):
        content=(folder/entry['file']).read_bytes()
        if entry.get('hashNormalization')=='CRLF to LF':content=content.replace(b'\r\n',b'\n')
        assert hashlib.sha256(content).hexdigest()==entry['sha256'],f"Input revised: {entry['file']}; create a new research version instead of reusing caches."

def read_inputs():
    verify_files(ROOT/'analytics/core-source-hashes.json',SOURCE_DATA)
    verify_files(ROOT/'analytics/redesign-sources.json',DIR)
    teams,seasons,_,_=load_data(SOURCE_DATA);talents={};coverage=[]
    for year in YEARS:
        raw=list(csv.DictReader((DIR/f'adv_team_gamelog_{year}.csv').open(encoding='utf-8-sig')))
        lookup={(r['game_id'],r['team_id']):r for r in raw};assert len(lookup)==len(raw)
        tal={str(r['team_id']):r for r in pd.read_parquet(DIR/f'cfb_team_talent_{year}.parquet').to_dict('records')}
        means=[float(np.mean([r[k] for t,r in tal.items() if t in teams[year]])) for k in ['talent_composite','blue_chip_ratio']]
        talents[year]={t:[float(tal.get(t,{}).get('talent_composite',means[0]))/1000-means[0]/1000,float(tal.get(t,{}).get('blue_chip_ratio',means[1]))-means[1],t not in tal] for t in teams[year]}
        paired=0
        for g in seasons[year]['games']:
            vals=[]
            for t in [g['home'],g['away']]:
                row=lookup.get((g['id'],t),{})
                def number(k):
                    try:v=float(row[k]);return v if math.isfinite(v) else None
                    except (KeyError,ValueError):return None
                if row:
                    assert row['start_date'][:10]==g['date'][:10],g['id']
                    assert int(float(row['points_for']))==(g['hs'] if t==g['home'] else g['as']),g['id']
                vals.append([number('EPA_per_play'),number('EPA_sp')])
            g['units']=vals
            if g['fbs'] and all(v[0] is not None for v in vals):paired+=1
        coverage.append(dict(year=year,games=sum(g['fbs'] for g in seasons[year]['games']),epaPairedGames=paired,talentTeams=sum(t in tal for t in teams[year]),teams=len(teams[year])))
    return teams,seasons,talents,coverage

def build(teams,seasons,talents,cfg):
    states={};priors=[{} for _ in range(len(UNIT_INDICES)+1)];elo={}
    for year in YEARS:
        ids=list(teams[year]);history=[];last={};counts={t:0 for t in ids}
        elo={t:cfg['carry']*elo.get(t,0.) for t in ids}
        for seq,week in enumerate(seasons[year]['weeks']+[99]):
            oo=[];dd=[];mus=[]
            for unit in [None,*UNIT_INDICES]:
                j=0 if unit is None else unit+1
                o,d,mu=fit_rating(history,ids,priors[j],cfg['lam'] if j==0 else cfg['lam']/2,3. if j==0 else 0.,cfg['carry'],unit,{t:cfg.get('talentPrior',0)*sum(talents[year][t][:2]) for t in ids} if j==0 else None)
                oo.append(o);dd.append(d);mus.append(mu)
            state={}
            for i,t in enumerate(ids):
                tv=talents[year][t]
                state[t]={'q':[float(oo[0][i]+dd[0][i]),float(oo[1][i]+dd[1][i]),float(oo[2][i]+dd[2][i]),elo[t]/100,tv[0],tv[1],*[float(oo[j][i]+dd[j][i]) for j in range(3,len(oo))]],'offense':float(oo[0][i]),'defense':float(dd[0][i]),'mu':mus[0],'sample':counts[t],'lastDate':last.get(t),'calendar':seq,'talentMissing':tv[2]}
            states[f'{year}:{week}']=state
            if week==99:
                priors=[{t:(float(oo[j][i]),float(dd[j][i])) for i,t in enumerate(ids)} for j in range(len(UNIT_INDICES)+1)];break
            batch=[g for g in seasons[year]['games'] if g['week']==week]
            cutoff=min(g['date'] for g in batch);assert all(g['date']<cutoff for g in history)
            updates={t:0. for t in ids}
            for g in batch:
                for t in [g['home'],g['away']]:
                    if t in state:last[t]=g['date']
                if not g['fbs']:continue
                a,b=state[g['home']],state[g['away']];h=0 if g['neutral'] else 3.
                expected=a['q'][0]-b['q'][0]+h;prob=float(sigmoid(expected/8));margin=g['hs']-g['as'];total=g['hs']+g['as']
                if cfg['method']=='cap28':margin=float(np.clip(margin,-28,28))
                elif cfg['method']=='residual28':margin=float(expected+28*np.tanh((margin-expected)/28))
                weight=1. if cfg['weight']=='uniform' else max(.25,4*prob*(1-prob))
                history.append({**g,'seq':seq,'modelHome':(total+margin)/2,'modelAway':(total-margin)/2,'weight':weight})
                pe=float(sigmoid((elo[g['home']]-elo[g['away']]+(0 if g['neutral'] else 55))*math.log(10)/400));delta=40*(float(g['hs']>g['as'])-pe)
                updates[g['home']]+=delta;updates[g['away']]-=delta
                counts[g['home']]+=1;counts[g['away']]+=1
            for t in ids:elo[t]+=updates[t]
    return states

def vector(state,bundle):
    q=np.array(state['q']).copy()
    if bundle=='all_calendar':q[4:6]*=math.exp(-state['calendar']/6)
    return q

def features(a,b,location,bundle,date=None):
    def rest(s):
        if not date or not s['lastDate']:return 7.
        return max(3.,min(21.,(datetime.fromisoformat(date.replace('Z','+00:00'))-datetime.fromisoformat(s['lastDate'].replace('Z','+00:00'))).total_seconds()/86400))
    return [*(vector(a,bundle)-vector(b,bundle)),float(location),rest(a)-rest(b)]

def fit(x,y,idx,penalty):
    a=x[:,idx];scale=np.maximum(np.sqrt(np.mean(a*a,axis=0)),1e-6);z=a/scale
    def objective(b):
        logits=z@b;loss=np.logaddexp(0,logits).sum()-y@logits+penalty/2*(b@b)
        grad=z.T@(sigmoid(logits)-y)+penalty*b
        return loss,grad
    fit_=minimize(objective,np.zeros(len(idx)),jac=True,method='L-BFGS-B',bounds=[(None,None) if j==len(NAMES)-1 else (0,None) for j in idx],options={'ftol':1e-12,'gtol':1e-7,'maxiter':500})
    if not fit_.success:
        fit_=minimize(objective,fit_.x,jac=True,method='SLSQP',bounds=[(None,None) if j==len(NAMES)-1 else (0,None) for j in idx],options={'ftol':1e-10,'maxiter':500})
    if not fit_.success:raise RuntimeError(fit_.message)
    beta=np.zeros(len(NAMES));beta[idx]=fit_.x/scale;return beta

def main():
    global SOURCE_DATA
    parser=argparse.ArgumentParser();parser.add_argument('--data',default=str(SOURCE_DATA));SOURCE_DATA=Path(parser.parse_args().data)
    protocol={'version':'5-research-1','ratingConfigurations':CONFIGS,'bundles':BUNDLES,'ridges':[1.,10.],'featureNames':NAMES,'constraints':'All team-strength and home-field coefficients nonnegative; rest unconstrained. No intercept. Neutral strength is scalar and transitive.','selection':'Minimum pooled previous-three-year log loss. Inner-year fits train only on preceding years from 2019. Refit through outerYear-1.','calendarDecay':'Recruiting in all_calendar multiplied by exp(-completed calendar weeks/6), never opponent sample count.','scope':'Retrospective revised historical data; all evaluation years have been inspected previously. EPA upstream fitting may include later data. No pristine holdout or verified garbage-time-filter claim.','blueprintSha256':hashlib.sha256((ROOT/'analytics/RANKING-REVIEW.md').read_bytes()).hexdigest()}
    protocol.update(PROTOCOL_EXTRA)
    path=ROOT/f'analytics/{RUN_NAME}-protocol.json'
    if path.exists():assert json.loads(path.read_text(encoding='utf-8'))==protocol
    else:path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    teams,seasons,talents,coverage=read_inputs();games=[g for year in YEARS for g in seasons[year]['games'] if g['fbs']]
    yy=np.array([g['season'] for g in games]);outcome=np.array([g['hs']>g['as'] for g in games],float);candidates=[]
    work=ROOT/f'analytics/{RUN_NAME}-work';work.mkdir(exist_ok=True)
    for ci,cfg in enumerate(CONFIGS):
        part=work/f'candidate-{ci}.json'
        if part.exists():
            saved=json.loads(part.read_text());assert saved['protocol']==protocol
            for c in saved['candidates']:c['prob']=np.array([np.nan if p is None else p for p in c['prob']])
            candidates.extend(saved['candidates']);print('CACHED',ci+1,flush=True);continue
        states=build(teams,seasons,talents,cfg);current=[]
        for name,idx in BUNDLES.items():
            x=np.array([features(states[f"{g['season']}:{g['week']}"][g['home']],states[f"{g['season']}:{g['week']}"][g['away']],0 if g['neutral'] else 1,name,g['date']) for g in games])
            for ridge in [1.,10.]:
                probs=np.full(len(games),np.nan);coefs={}
                for year in range(2020,2027):
                    tr=(yy>=2019)&(yy<year);te=yy==year;coef=fit(x[tr],outcome[tr],idx,ridge);probs[te]=sigmoid(x[te]@coef);coefs[str(year)]=coef.tolist()
                current.append({'ratingIndex':ci,'ratingConfig':cfg,'bundle':name,'ridge':ridge,'coefs':coefs,'prob':probs})
        part.write_text(json.dumps({'protocol':protocol,'candidates':[{**c,'prob':[float(v) if np.isfinite(v) else None for v in c['prob']]} for c in current]},separators=(',',':')),encoding='utf-8')
        candidates.extend(current);print('RATING',ci+1,'/',len(CONFIGS),flush=True)
    annual={};searches=[];predictions=[];selectedStates={}
    old=json.loads((ROOT/'public/data/model-v4.json').read_text());assert old['version']=='4.0.0';oldp={p['id']:p for p in old['predictions']}
    for year in [2023,2024,2025,2026]:
        val=(yy>=year-3)&(yy<year);test=yy==year
        order=sorted(candidates,key=lambda c:(metrics(c['prob'][val],outcome[val])['logLoss'],len(BUNDLES[c['bundle']]),c['ratingIndex']))
        selected=order[0];search=[{k:c[k] for k in ['ratingIndex','ratingConfig','bundle','ridge']}|metrics(c['prob'][val],outcome[val]) for c in order]
        annual[str(year)]={'selected':search[0],'coefficients':selected['coefs'][str(year)],'trainingThrough':year-1,'validationYears':list(range(year-3,year)),'validation':search[0],'test':metrics(selected['prob'][test],outcome[test])}
        searches.append({'targetSeason':year,'candidates':search});ss=build(teams,seasons,talents,selected['ratingConfig']);selectedStates[str(year)]={k:v for k,v in ss.items() if k.startswith(str(year)+':')}
        for i,g in enumerate(games):
            if g['season']!=year:continue
            o=oldp[g['id']];a,b=ss[f'{year}:{g["week"]}'][g['home']],ss[f'{year}:{g["week"]}'][g['away']];h=0 if g['neutral'] else 1.5
            p={k:v for k,v in g.items() if k!='units'}
            p.update(prob=float(selected['prob'][i]),outcome=int(outcome[i]),previousProb=o['prob'],v3Prob=o['previousProb'],benchmark=o['benchmark'],cutoff=o['cutoff'],homeScore=a['mu']+a['offense']-b['defense']+h,awayScore=a['mu']+b['offense']-a['defense']-h)
            p['margin']=p['homeScore']-p['awayScore'];p['actualMargin']=g['hs']-g['as'];predictions.append(p)
        print('SELECTED',year,json.dumps(annual[str(year)]),flush=True)
    report={'version':'5.0.0','protocol':protocol,'candidateCount':len(candidates),'coverage':coverage,'annual':annual,'searches':searches,'predictions':predictions,'scope':protocol['scope']}
    CACHE.write_text(json.dumps({'states':selectedStates,'report':report},separators=(',',':'),allow_nan=False),encoding='utf-8')
    for year in [2023,2024,2025,2026]:
        rows=[r for r in predictions if r['season']==year]
        for name,key in [('v5','prob'),('v4','previousProb'),('v3','v3Prob'),('v1','benchmark')]:print(year,name,metrics([r[key] for r in rows],[r['outcome'] for r in rows]),flush=True)
if __name__=='__main__':main()
