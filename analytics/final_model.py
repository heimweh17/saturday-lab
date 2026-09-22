"""Single production model, selected by nested expanding-time validation.
The protocol, not a favorable test score, determines every annual configuration.
All results are retrospective: previously viewed seasons are never called untouched.
"""
import argparse,json,hashlib,csv
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from feature_engine import ROOT,YEARS,NAMES,BASE,BUNDLES,RIDGES,build,fit,features
from pipeline import load_data,metrics,sigmoid

def candidates():
    return [{'name':name,'indices':idx,'ridge':ridge,'weight':weight} for name,idx in BUNDLES.items() for ridge in RIDGES for weight in (.25,.5,.75,1.)]+[{'name':'scoring_anchor','indices':[0],'ridge':1.,'weight':0.}]

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);args=p.parse_args()
    protocol={'version':'3.0.0','featureNames':NAMES,'ratingParameters':BASE,'candidates':candidates(),'selection':'Minimum pooled log loss in the three seasons preceding each target year. Each inner fold trains only through its previous year. Refit chosen logistic coefficients through targetYear-1. The fixed scoring anchor has shrinkage 5, home 3, decay .94, scale 8.','scope':'All evaluations are retrospective. No future results enter a target week, but historical source revisions and developer exposure preclude pristine prospective-test claims.'}
    lock=ROOT/'analytics/final-protocol.json'
    if lock.exists(): assert json.loads(lock.read_text())==protocol,'Create a new protocol version before changing the frozen search.'
    else: lock.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    # Persist search contract before running any candidate or test evaluation.
    digest=hashlib.sha256(lock.read_bytes()).hexdigest()
    teams,seasons,boxes,_=load_data(Path(args.data));rows,states=build(teams,seasons,boxes)
    (ROOT/'analytics/final-feature-cache.json').write_text(json.dumps({'rows':rows,'states':states},separators=(',',':')),encoding='utf-8')
    byyear={y:[r for r in rows if r['season']==y] for y in YEARS}
    trained={}; forecasts={}
    for year in range(2020,2027):
        train=[r for r in rows if 2019<=r['season']<year];x=np.array([r['x'] for r in byyear[year]])
        for name,idx in BUNDLES.items():
            for ridge in RIDGES:
                coef=fit(train,idx,ridge);trained[(year,name,ridge)]=coef
                forecasts[(year,name,ridge)]=sigmoid(x@coef)
    annual={};predictions=[];evaluation=[];candidate_report=[]
    for year in range(2023,2027):
        folds=list(range(max(2020,year-3),year)); scores=[]
        for c in candidates():
            pp=[];yy=[];foldscores=[]
            for valyear in folds:
                rs=byyear[valyear];anchor=sigmoid(np.array([r['baseMargin'] for r in rs])/8)
                prob=c['weight']*forecasts[(valyear,c['name'] if c['weight'] else 'scoring',c['ridge'])]+(1-c['weight'])*anchor
                foldscores.append({'year':valyear,**metrics(prob,[r['y'] for r in rs])});pp.extend(prob);yy.extend(r['y'] for r in rs)
            scores.append({**c,'folds':foldscores,**metrics(pp,yy)})
        scores.sort(key=lambda c:(c['logLoss'],len(c['indices']),c['weight']))
        chosen=scores[0];coef=trained[(year,chosen['name'] if chosen['weight'] else 'scoring',chosen['ridge'])]
        annual[str(year)]={'coefficients':coef.tolist(),'weight':chosen['weight'],'selected':chosen,'trainingThrough':year-1,'validationYears':folds}
        candidate_report.append({'targetSeason':year,'candidates':scores})
        test=byyear[year];anchor=sigmoid(np.array([r['baseMargin'] for r in test])/8)
        probs=chosen['weight']*sigmoid(np.array([r['x'] for r in test])@coef)+(1-chosen['weight'])*anchor
        old=json.loads((ROOT/f'public/data/{year}.json').read_text());oldp={r['id']:{**r,'prob':r.get('baselineProb',r['prob'])} for r in old['predictions']}
        evaluation.extend([{'season':year,'model':'Saturday model',**metrics(probs,[r['y'] for r in test])},{'season':year,'model':'Original scoring benchmark',**metrics([oldp[r['id']]['prob'] for r in test],[r['y'] for r in test])},{'season':year,'model':'50/50',**metrics([.5]*len(test),[r['y'] for r in test])}])
        for r,prob in zip(test,probs): predictions.append({'id':r['id'],'season':year,'week':r['week'],'home':r['home'],'away':r['away'],'homeName':r['homeName'],'awayName':r['awayName'],'date':r['date'],'prob':float(prob),'benchmark':oldp[r['id']]['prob'],'outcome':r['y'],'margin':r['baseMargin'],'homeScore':r['homeScore'],'awayScore':r['awayScore'],'actualMargin':r['hs']-r['as'],'cutoff':r['cutoff']})
        print('Selected',year,chosen['name'],chosen['ridge'],chosen['weight'],'validation',chosen['logLoss'], 'test',evaluation[-3],flush=True)
    # Paired bootstrap by week retains within-week dependence; uncertainty, not model selection.
    boot=[];rng=np.random.default_rng(20260922)
    for year in (2024,2025,2026):
        rs=[r for r in predictions if r['season']==year];weekids=sorted(set(r['week'] for r in rs));groups=[]
        for week in weekids:
            rr=[r for r in rs if r['week']==week]; y=np.array([r['outcome'] for r in rr]);q=np.clip([r['prob'] for r in rr],1e-9,1-1e-9);b=np.clip([r['benchmark'] for r in rr],1e-9,1-1e-9)
            delta=-(y*np.log(q)+(1-y)*np.log(1-q))+(y*np.log(b)+(1-y)*np.log(1-b));groups.append((float(sum(delta)),len(rr)))
        sims=[]
        for _ in range(3000):
            chosen=rng.integers(0,len(groups),len(groups));sims.append(sum(groups[i][0] for i in chosen)/sum(groups[i][1] for i in chosen))
        boot.append({'season':year,'weeks':len(weekids),'resamples':3000,'lossDifference':sum(g[0] for g in groups)/sum(g[1] for g in groups),'lower':float(np.quantile(sims,.025)),'upper':float(np.quantile(sims,.975))})
    report={**protocol,'protocolSha256':digest,'generatedAt':datetime.now(timezone.utc).isoformat(),'annual':annual,'searches':candidate_report,'evaluation':evaluation,'bootstrap':boot,'predictions':predictions}
    (ROOT/'public/data/model.json').write_text(json.dumps(report,separators=(',',':')),encoding='utf-8')
    with (ROOT/'public/data/model-predictions.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(predictions[0]));w.writeheader();w.writerows(predictions)
    for year in YEARS:
        path=ROOT/f'public/data/{year}.json';data=json.loads(path.read_text());data.pop('v2Coefficients',None)
        data['scoringConfig']={'elo':{'k':40,'home':55,'carry':.65},'scoring':BASE,'eloWeight':0} if str(year) in annual else json.loads((ROOT/'analytics/locked-config.json').read_text())['config']
        if str(year) in annual:
            cfg=annual[str(year)];data['model']={'version':'3.0.0','coefficients':cfg['coefficients'],'weight':cfg['weight'],'trainingThrough':cfg['trainingThrough']}
        previous_ranks={}
        for week,snap in data['snapshots'].items():
            for t in snap['teams']:
                t.pop('v2',None)
                if str(year) in annual:
                    state=states[f'{year}:{week}'][t['id']];t['modelState']=state
                    t.update(offense=state['offense'],defense=state['defense'],power=state['basePower'],elo=state['elo'])
                    snap['mu']=state['mu']
                    preceding=seasons[year]['weeks'][:seasons[year]['weeks'].index(int(week))] if int(week)!=99 else seasons[year]['weeks']
                    opp=[g['away'] if g['home']==t['id'] else g['home'] for g in seasons[year]['games'] if g['fbs'] and g['week'] in preceding and t['id'] in (g['home'],g['away'])]
                    t['sos']=float(np.mean([states[f'{year}:{week}'][o]['basePower'] for o in opp])) if opp else None
            if str(year) in annual:
                # Ranking: neutral-field expected win fraction against every other FBS team.
                coef=np.array(cfg['coefficients']);weight=cfg['weight'];neutral_indices={}
                for t in snap['teams']:
                    xs=np.array([features(t['modelState'],other['modelState'],0) for other in snap['teams'] if other['id']!=t['id']])
                    neutral_indices[t['id']]=float(np.mean(weight*sigmoid(xs@coef)+(1-weight)*sigmoid(xs[:,0]/8)))
                ordered=sorted(snap['teams'],key=lambda t:(-neutral_indices[t['id']],t['name']))
                for rank,t in enumerate(ordered,1):
                    t['winIndex']=neutral_indices[t['id']];t['modelRank']=rank;t['modelChange']=previous_ranks.get(t['id'],rank)-rank
                previous_ranks={t['id']:t['modelRank'] for t in ordered}
        official={r['id']:r for r in predictions if r['season']==year}
        for pred in data['predictions']:
            if pred['id'] in official:
                pred['baselineProb']=pred.get('baselineProb',pred['prob']);pred['prob']=official[pred['id']]['prob'];pred['modelVersion']='3.0.0'
                for key in ('margin','homeScore','awayScore'):pred[key]=official[pred['id']][key]
        path.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    hold=[p for p in predictions if p['season'] in (2024,2025)];residual=sorted(abs(p['actualMargin']-p['margin']) for p in hold)
    config={'elo':{'k':40,'home':55,'carry':.65},'scoring':BASE,'eloWeight':0}
    display={'config':config,'candidates':[],'evaluation':evaluation,'calibration':[],'holdout':metrics([p['prob'] for p in hold],[p['outcome'] for p in hold],[p['margin'] for p in hold],[p['actualMargin'] for p in hold]),'residual80':residual[int(.8*(len(residual)-1))]}
    (ROOT/'public/data/report.json').write_text(json.dumps(display,separators=(',',':')),encoding='utf-8')
    manifest_path=ROOT/'public/data/manifest.json';manifest=json.loads(manifest_path.read_text());manifest.update(version='3.0.0',config=config,modelReport='model.json',boxMetrics=30,generatedAt=datetime.now(timezone.utc).isoformat());manifest_path.write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
    (ROOT/'lib/production-config.json').write_text(json.dumps({'version':'3.0.0',**annual['2026'],'featureNames':NAMES},separators=(',',':')),encoding='utf-8')
    print('Protocol',digest,flush=True)
if __name__=='__main__':main()
